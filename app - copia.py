# app.py - Sistema de Punto de Venta Argentina con Flask, MySQL y ARCA - VERSIÓN LIMPIA

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, or_, and_  # ← IMPORTAR AQUÍ
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal
import os
import requests
import xml.etree.ElementTree as ET
from zeep import Client
from zeep.wsse import BinarySignature
import base64
import hashlib
from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'

# Intentar cargar configuración local, si no existe usar por defecto
try:
    from config_local import Config, ARCAConfig
    app.config.from_object(Config)
    ARCA_CONFIG = ARCAConfig()
except ImportError:
    # Configuración por defecto si no existe config_local.py
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://pos_user:pos_password@localhost/pos_argentina'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    class DefaultARCAConfig:
        CUIT = '20203852100'
        PUNTO_VENTA = 3
        CERT_PATH = 'certificados/certificado.crt'
        KEY_PATH = 'certificados/private.key'
        USE_HOMOLOGACION = True
        
        @property
        def WSAA_URL(self):
            return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms' if self.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
        
        @property
        def WSFEv1_URL(self):
            return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
        
        TOKEN_CACHE_FILE = 'cache/token_arca.json'
    
    ARCA_CONFIG = DefaultARCAConfig()

db = SQLAlchemy(app)

# Modelos de Base de Datos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(50), default='vendedor')
    activo = db.Column(db.Boolean, default=True)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    documento = db.Column(db.String(20))
    tipo_documento = db.Column(db.String(10))  # DNI, CUIT, etc.
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    condicion_iva = db.Column(db.String(50))  # Responsable Inscripto, Monotributista, etc.

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    categoria = db.Column(db.String(100))
    iva = db.Column(Numeric(5, 2), default=21.00)
    activo = db.Column(db.Boolean, default=True)

class Factura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True)
    tipo_comprobante = db.Column(db.String(10))  # FA, FB, FC, etc.
    punto_venta = db.Column(db.Integer)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    subtotal = db.Column(Numeric(10, 2))
    iva = db.Column(Numeric(10, 2))
    total = db.Column(Numeric(10, 2))
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, autorizada, anulada
    cae = db.Column(db.String(50))  # Código de Autorización Electrónico
    vto_cae = db.Column(db.Date)
    
    cliente = db.relationship('Cliente', backref='facturas')
    usuario = db.relationship('Usuario', backref='facturas')

class DetalleFactura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('factura.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(Numeric(10, 2), nullable=False)
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    
    factura = db.relationship('Factura', backref='detalles')
    producto = db.relationship('Producto', backref='detalles_factura')

# Clase para manejo de ARCA/AFIP
# Clase para manejo de ARCA/AFIP usando PyAfipWs
class ARCAClient:
    def __init__(self):
        self.config = ARCA_CONFIG
        
        # Importar PyAfipWs
        try:
            from pyafipws.wsaa import WSAA
            from pyafipws.wsfev1 import WSFEv1
        except ImportError:
            raise Exception("PyAfipWs no está instalado. Ejecuta: pip install pyafipws")
        
        # Configurar WSAA (autenticación)
        self.wsaa = WSAA()
        if self.config.USE_HOMOLOGACION:
            self.wsaa.Conectar("https://wsaahomo.afip.gov.ar/ws/services/LoginCms")
        else:
            self.wsaa.Conectar("https://wsaa.afip.gov.ar/ws/services/LoginCms")
            
        # Configurar WSFEv1 (facturación)
        self.wsfe = WSFEv1()
        if self.config.USE_HOMOLOGACION:
            self.wsfe.Conectar("https://wswhomo.afip.gov.ar/wsfev1/service.asmx")
        else:
            self.wsfe.Conectar("https://servicios1.afip.gov.ar/wsfev1/service.asmx")
        
        print(f"✅ PyAfipWs inicializado")
        print(f"   CUIT: {self.config.CUIT}")
        print(f"   Ambiente: {'HOMOLOGACIÓN' if self.config.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    
    def get_ticket_access(self):
        """Obtiene el ticket de acceso (TA) de WSAA"""
        try:
            print("🎫 Obteniendo ticket de acceso con PyAfipWs...")
            
            # Verificar que existan los certificados
            if not os.path.exists(self.config.CERT_PATH):
                raise Exception(f"Certificado no encontrado: {self.config.CERT_PATH}")
            
            if not os.path.exists(self.config.KEY_PATH):
                raise Exception(f"Clave privada no encontrada: {self.config.KEY_PATH}")
            
            # Autenticar con WSAA
            ta = self.wsaa.Autenticar("wsfe", self.config.CERT_PATH, self.config.KEY_PATH)
            
            if self.wsaa.Excepcion:
                raise Exception(f"Error WSAA: {self.wsaa.Excepcion}")
            
            if not ta:
                raise Exception("No se pudo obtener ticket de acceso")
            
            # Configurar credenciales en WSFEv1
            self.wsfe.Token = self.wsaa.Token
            self.wsfe.Sign = self.wsaa.Sign
            self.wsfe.Cuit = self.config.CUIT
            
            print("✅ Ticket de acceso obtenido correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error obteniendo ticket: {e}")
            return False
    
    def get_ultimo_comprobante(self, tipo_cbte):
        """Obtiene el último número de comprobante autorizado"""
        try:
            print(f"📋 Consultando último comprobante tipo {tipo_cbte}...")
            
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener acceso a AFIP")
            
            # Consultar último comprobante
            ultimo = self.wsfe.CompUltimoAutorizado(tipo_cbte, self.config.PUNTO_VENTA)
            
            if self.wsfe.Excepcion:
                raise Exception(f"Error WSFEv1: {self.wsfe.Excepcion}")
            
            print(f"✅ Último comprobante: {ultimo}")
            return ultimo
            
        except Exception as e:
            print(f"❌ Error consultando último comprobante: {e}")
            raise Exception(f"Error al obtener último comprobante: {e}")
    
    def autorizar_comprobante(self, factura_data):
        """Autoriza un comprobante en AFIP"""
        try:
            print(f"📄 Autorizando comprobante {factura_data['numero']} con PyAfipWs...")
            
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener acceso a AFIP")
            
            # Determinar tipo de documento del cliente
            cliente_cuit = factura_data.get('cliente_cuit', '0')
            if cliente_cuit and cliente_cuit != '0' and len(cliente_cuit) == 11:
                tipo_doc = 80  # CUIT
                nro_doc = int(cliente_cuit)
            else:
                tipo_doc = 99  # Sin identificar
                nro_doc = 0
            
            # Crear el comprobante
            self.wsfe.CrearFactura(
                concepto=1,  # Productos
                tipo_doc=tipo_doc,
                nro_doc=nro_doc,
                tipo_cbte=factura_data['tipo_comprobante'],
                punto_vta=self.config.PUNTO_VENTA,
                cbte_nro=factura_data['numero'],
                fecha_cbte=factura_data['fecha'].strftime('%Y%m%d'),
                imp_total=float(factura_data['total']),
                imp_tot_conc=0,  # Importe no gravado
                imp_neto=float(factura_data['subtotal']),
                imp_iva=float(factura_data['iva']),
                imp_trib=0,  # Otros tributos
                imp_op_ex=0,  # Operaciones exentas
                fecha_serv_desde=None,
                fecha_serv_hasta=None,
                fecha_venc_pago=None,
                moneda_id='PES',
                moneda_ctz=1
            )
            
            # Solicitar autorización (CAE)
            cae = self.wsfe.CAESolicitar()
            
            if self.wsfe.Excepcion:
                raise Exception(f"Error autorizando comprobante: {self.wsfe.Excepcion}")
            
            if not cae:
                raise Exception("No se pudo obtener CAE")
            
            # Verificar resultado
            if self.wsfe.Resultado == 'A':
                print(f"✅ Comprobante autorizado - CAE: {self.wsfe.CAE}")
                
                # Convertir fecha de vencimiento
                try:
                    from datetime import datetime
                    vto_cae = datetime.strptime(self.wsfe.Vencimiento, '%Y%m%d').date()
                except:
                    vto_cae = None
                
                return {
                    'cae': self.wsfe.CAE,
                    'vto_cae': vto_cae,
                    'estado': 'autorizada',
                    'resultado': self.wsfe.Resultado
                }
            else:
                print(f"❌ Comprobante rechazado: {self.wsfe.Resultado}")
                return {
                    'cae': None,
                    'vto_cae': None,
                    'estado': 'rechazada',
                    'resultado': self.wsfe.Resultado
                }
                
        except Exception as e:
            print(f"❌ Error autorizando comprobante: {e}")
            raise Exception(f"Error al autorizar comprobante: {e}")
    
    def test_conexion(self):
        """Prueba la conexión con AFIP"""
        try:
            print("🧪 Probando conexión con AFIP...")
            
            # Probar método dummy (no requiere autenticación)
            dummy = self.wsfe.Dummy()
            if dummy:
                print(f"✅ Conexión WSFEv1 OK")
                print(f"   AppServer: {self.wsfe.AppServerStatus}")
                print(f"   DbServer: {self.wsfe.DbServerStatus}")
                print(f"   AuthServer: {self.wsfe.AuthServerStatus}")
                return True
            else:
                print("❌ No hay respuesta del servidor AFIP")
                return False
                
        except Exception as e:
            print(f"❌ Error probando conexión: {e}")
            return False
# Instancia del cliente ARCA
arca_client = ARCAClient()

# Rutas de la aplicación
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuario = Usuario.query.filter_by(username=username, activo=True).first()
        
        # Login simple sin encriptación
        if usuario and usuario.password_hash == password:
            session['user_id'] = usuario.id
            session['username'] = usuario.username
            session['nombre'] = usuario.nombre
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/productos')
def productos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    productos = Producto.query.filter_by(activo=True).all()
    return render_template('productos.html', productos=productos)

@app.route('/clientes')
def clientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    clientes = Cliente.query.all()
    return render_template('clientes.html', clientes=clientes)

@app.route('/nueva_venta')
def nueva_venta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    productos = Producto.query.filter_by(activo=True).all()
    clientes = Cliente.query.all()
    return render_template('nueva_venta.html', productos=productos, clientes=clientes)

# APIs para búsqueda de productos
@app.route('/api/buscar_productos/<termino>')
def buscar_productos(termino):
    """Busca productos por código o nombre (búsqueda parcial)"""
    if not termino or len(termino) < 2:
        return jsonify([])
    
    # Búsqueda por código exacto primero
    producto_exacto = Producto.query.filter_by(codigo=termino.upper(), activo=True).first()
    if producto_exacto:
        return jsonify([{
            'id': producto_exacto.id,
            'codigo': producto_exacto.codigo,
            'nombre': producto_exacto.nombre,
            'precio': float(producto_exacto.precio),
            'stock': producto_exacto.stock,
            'iva': float(producto_exacto.iva),
            'match_tipo': 'codigo_exacto',
            'descripcion': producto_exacto.descripcion or ''
        }])
    
    # Búsqueda parcial en código y nombre
    termino_busqueda = f"%{termino.lower()}%"
    
    productos = Producto.query.filter(
        and_(
            Producto.activo == True,
            or_(
                Producto.codigo.ilike(termino_busqueda),
                Producto.nombre.ilike(termino_busqueda),
                Producto.descripcion.ilike(termino_busqueda)
            )
        )
    ).limit(10).all()
    
    resultados = []
    for producto in productos:
        # Determinar tipo de coincidencia para ordenar resultados
        match_tipo = 'nombre'
        if termino.lower() in producto.codigo.lower():
            match_tipo = 'codigo'
        elif termino.lower() in producto.nombre.lower()[:20]:
            match_tipo = 'nombre_inicio'
        
        resultados.append({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'iva': float(producto.iva),
            'match_tipo': match_tipo,
            'descripcion': producto.descripcion or ''
        })
    
    # Ordenar resultados por relevancia
    def orden_relevancia(item):
        if item['match_tipo'] == 'codigo_exacto':
            return 0
        elif item['match_tipo'] == 'codigo':
            return 1
        elif item['match_tipo'] == 'nombre_inicio':
            return 2
        else:
            return 3
    
    resultados.sort(key=orden_relevancia)
    return jsonify(resultados)

@app.route('/api/producto_por_id/<int:producto_id>')
def get_producto_por_id(producto_id):
    """Obtiene un producto por ID"""
    producto = Producto.query.filter_by(id=producto_id, activo=True).first()
    if producto:
        return jsonify({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'iva': float(producto.iva),
            'descripcion': producto.descripcion or ''
        })
    return jsonify({'error': 'Producto no encontrado'}), 404

@app.route('/api/producto/<codigo>')
def get_producto(codigo):
    """Obtiene un producto por código exacto"""
    producto = Producto.query.filter_by(codigo=codigo.upper(), activo=True).first()
    if producto:
        return jsonify({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'stock': producto.stock,
            'iva': float(producto.iva),
            'descripcion': producto.descripcion or ''
        })
    return jsonify({'error': 'Producto no encontrado'}), 404

# REEMPLAZAR la función procesar_venta en app.py por esta versión corregida:

@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        
        # PASO 1: Obtener próximo número de comprobante ANTES de crear la factura
        try:
            print("Intentando obtener número de AFIP...")
            ultimo_numero = arca_client.get_ultimo_comprobante(int(data.get('tipo_comprobante', '11')))
            nuevo_numero = ultimo_numero + 1
            print(f"Número obtenido de AFIP: {nuevo_numero}")
        except Exception as e:
            print(f"Error al obtener número de AFIP: {e}")
            print("Usando numeración local...")
            
            # Fallback: usar numeración local
            ultima_factura = Factura.query.filter_by(
                tipo_comprobante=data.get('tipo_comprobante', '11'),
                punto_venta=ARCA_CONFIG.PUNTO_VENTA
            ).order_by(Factura.id.desc()).first()
            
            if ultima_factura and ultima_factura.numero:
                try:
                    # Extraer número de la última factura (formato: 0001-00000001)
                    ultimo_numero_local = int(ultima_factura.numero.split('-')[1])
                    nuevo_numero = ultimo_numero_local + 1
                except:
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            print(f"Número local generado: {nuevo_numero}")
        
        # PASO 2: Generar número de factura con formato correcto
        numero_factura = f"{ARCA_CONFIG.PUNTO_VENTA:04d}-{nuevo_numero:08d}"
        print(f"Número de factura generado: {numero_factura}")
        
        # PASO 3: Crear factura CON el número ya asignado
        factura = Factura(
            numero=numero_factura,  # ← ASIGNAR AQUÍ EL NÚMERO
            tipo_comprobante=data.get('tipo_comprobante', '11'),
            punto_venta=ARCA_CONFIG.PUNTO_VENTA,
            cliente_id=data['cliente_id'],
            usuario_id=session['user_id'],
            subtotal=Decimal(str(data['subtotal'])),
            iva=Decimal(str(data['iva'])),
            total=Decimal(str(data['total']))
        )
        
        db.session.add(factura)
        db.session.flush()  # Para obtener el ID sin hacer commit
        
        print(f"Factura creada con ID: {factura.id} y número: {factura.numero}")
        
        # PASO 4: Agregar detalles
        for item in data['items']:
            detalle = DetalleFactura(
                factura_id=factura.id,
                producto_id=item['producto_id'],
                cantidad=item['cantidad'],
                precio_unitario=Decimal(str(item['precio_unitario'])),
                subtotal=Decimal(str(item['subtotal']))
            )
            db.session.add(detalle)
            
            # Actualizar stock
            producto = Producto.query.get(item['producto_id'])
            if producto:
                producto.stock -= item['cantidad']
                print(f"Stock actualizado para {producto.nombre}: {producto.stock}")
        
        # PASO 5: Intentar autorizar en AFIP
        try:
            print("Intentando autorizar en AFIP...")
            cliente = Cliente.query.get(data['cliente_id'])
            factura_data = {
                'tipo_comprobante': int(data.get('tipo_comprobante', '11')),
                'numero': nuevo_numero,
                'fecha': factura.fecha,
                'cliente_cuit': cliente.documento if cliente and cliente.tipo_documento == 'CUIT' else '0',
                'subtotal': factura.subtotal,
                'iva': factura.iva,
                'total': factura.total
            }
            
            resultado_afip = arca_client.autorizar_comprobante(factura_data)
            
            factura.cae = resultado_afip['cae']
            factura.vto_cae = resultado_afip['vto_cae']
            factura.estado = resultado_afip['estado']
            
            print(f"Autorización AFIP exitosa. CAE: {factura.cae}")
            
        except Exception as e:
            print(f"Error al autorizar en AFIP: {e}")
            factura.estado = 'error_afip'
            # Continuar con la venta local
        
        # PASO 6: Guardar todo en la base de datos
        db.session.commit()
        
        print(f"Venta procesada exitosamente: {factura.numero}")
        
        return jsonify({
            'success': True,
            'factura_id': factura.id,
            'numero': factura.numero,
            'cae': factura.cae,
            'estado': factura.estado
        })
        
    except Exception as e:
        print(f"Error en procesar_venta: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/facturas')
def facturas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    facturas = Factura.query.order_by(Factura.fecha.desc()).limit(100).all()
    return render_template('facturas.html', facturas=facturas)

@app.route('/factura/<int:factura_id>')
def ver_factura(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    factura = Factura.query.get_or_404(factura_id)
    return render_template('factura_detalle.html', factura=factura)

# Funciones de inicialización
def create_tables():
    """Crea las tablas de la base de datos"""
    try:
        db.create_all()
        
        # Crear usuario admin por defecto si no existe
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password_hash='admin123',  # Sin encriptación para simplicidad
                nombre='Administrador',
                rol='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado (admin/admin123)")
        
        print("✅ Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error al inicializar base de datos: {e}")

if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('cache', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('certificados', exist_ok=True)
    
    print("🚀 Iniciando POS Argentina...")
    print(f"📍 URL: http://localhost:5000")
    print(f"🏢 CUIT: {ARCA_CONFIG.CUIT}")
    print(f"🏪 Punto de Venta: {ARCA_CONFIG.PUNTO_VENTA}")
    print(f"🔧 Ambiente: {'HOMOLOGACIÓN' if ARCA_CONFIG.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    print(f"👤 Usuario: admin")
    print(f"🔑 Contraseña: admin123")
    print()
    
    with app.app_context():
        create_tables()
    
    app.run(debug=True, host='0.0.0.0', port=5000)