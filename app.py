# app.py - Sistema de Punto de Venta Argentina con Flask, MySQL, ARCA e Impresión Térmica

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric, or_, and_  # ← IMPORTAR AQUÍ
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import mysql.connector
from decimal import Decimal
from qr_afip import crear_generador_qr
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
import subprocess

# ================ FIX SSL COMPATIBLE PARA AFIP ================
import ssl
import urllib3
from urllib3.util import ssl_
from requests.adapters import HTTPAdapter
from requests import Session

def configurar_ssl_afip():
    """Configuración SSL compatible para todas las versiones de Python"""
    
    # Variables de entorno
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    def create_afip_ssl_context():
        """Crear contexto SSL para AFIP"""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except AttributeError:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
        
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Ciphers más permisivos - probar niveles de seguridad
        try:
            ctx.set_ciphers('ALL:@SECLEVEL=0')
        except ssl.SSLError:
            try:
                ctx.set_ciphers('ALL:@SECLEVEL=1')
            except ssl.SSLError:
                ctx.set_ciphers('ALL')
        
        # Aplicar opciones SSL disponibles
        for opcion in ['OP_LEGACY_SERVER_CONNECT', 'OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION', 'OP_ALL']:
            if hasattr(ssl, opcion):
                try:
                    ctx.options |= getattr(ssl, opcion)
                except:
                    pass
        
        return ctx
    
    # Aplicar configuración
    ssl._create_default_https_context = create_afip_ssl_context
    ssl_.create_urllib3_context = create_afip_ssl_context
    urllib3.disable_warnings()
    
    print("✅ Configuración SSL para AFIP aplicada")

# Aplicar configuración SSL
configurar_ssl_afip()

def crear_session_afip():
    """Crear sesión HTTP personalizada para AFIP"""
    
    class AFIPAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            except AttributeError:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
            
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            try:
                ctx.set_ciphers('ALL:@SECLEVEL=0')
            except ssl.SSLError:
                try:
                    ctx.set_ciphers('ALL:@SECLEVEL=1')
                except ssl.SSLError:
                    ctx.set_ciphers('ALL')
            
            # Aplicar opciones disponibles
            for opcion in ['OP_LEGACY_SERVER_CONNECT', 'OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION', 'OP_ALL']:
                if hasattr(ssl, opcion):
                    try:
                        ctx.options |= getattr(ssl, opcion)
                    except:
                        pass
            
            kwargs['ssl_context'] = ctx
            return super().init_poolmanager(*args, **kwargs)
    
    session = Session()
    session.mount('https://', AFIPAdapter())
    session.verify = False
    return session

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
        USE_HOMOLOGACION = False  # PRODUCCIÓN
        
        @property
        def WSAA_URL(self):
            return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms' if self.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
        
        @property
        def WSFEv1_URL(self):
            return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
        
        TOKEN_CACHE_FILE = 'cache/token_arca.json'
    
    ARCA_CONFIG = DefaultARCAConfig()

db = SQLAlchemy(app)

# ================ SISTEMA DE IMPRESIÓN TÉRMICA ================
import tempfile
try:
    import win32print
    import win32api
    IMPRESION_DISPONIBLE = True
    print("✅ Sistema de impresión disponible")
except ImportError:
    IMPRESION_DISPONIBLE = False
    print("⚠️ Sistema de impresión no disponible (instalar: pip install pywin32)")

# IMPORTAR LA IMPRESORA DESDE EL ARCHIVO SEPARADO
from impresora_termica import impresora_termica

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
class ARCAClient:
    def __init__(self):
        self.config = ARCA_CONFIG
        self.token = None
        self.sign = None
        self.cuit = self.config.CUIT
        self.openssl_path = self._buscar_openssl()
        
        print(f"🔧 AFIP Client inicializado")
        print(f"   CUIT: {self.config.CUIT}")
        print(f"   Ambiente: {'HOMOLOGACIÓN' if self.config.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    
    def _buscar_openssl(self):
        """Buscar OpenSSL en ubicaciones conocidas"""
        ubicaciones = [
            './openssl.exe',
            'openssl.exe', 
            'openssl',
            r'C:\Program Files\OpenSSL-Win64\bin\openssl.exe',
            r'C:\OpenSSL-Win64\bin\openssl.exe',
            r'C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe'
        ]
        
        for ubicacion in ubicaciones:
            try:
                if os.path.exists(ubicacion) or ubicacion in ['openssl.exe', 'openssl']:
                    result = subprocess.run([ubicacion, 'version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print(f"✅ OpenSSL encontrado: {ubicacion}")
                        return ubicacion
            except:
                continue
        
        print("❌ OpenSSL no encontrado, usando 'openssl' por defecto")
        return 'openssl'
    
    def crear_tra(self):
        """Crear Ticket Request Access"""
        now = datetime.utcnow()
        expire = now + timedelta(hours=12)
        unique_id = int(now.timestamp())
        
        tra_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
    <header>
        <uniqueId>{unique_id}</uniqueId>
        <generationTime>{now.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</generationTime>
        <expirationTime>{expire.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</expirationTime>
    </header>
    <service>wsfe</service>
</loginTicketRequest>'''
        
        return tra_xml
    
    def firmar_tra_openssl(self, tra_xml):
        """Firmar TRA usando OpenSSL"""
        try:
            import tempfile
            
            print(f"🔐 Firmando TRA con OpenSSL: {self.openssl_path}")
            
            # Verificar certificados
            if not os.path.exists(self.config.CERT_PATH):
                raise Exception(f"Certificado no encontrado: {self.config.CERT_PATH}")
            if not os.path.exists(self.config.KEY_PATH):
                raise Exception(f"Clave privada no encontrada: {self.config.KEY_PATH}")
            
            # Crear archivos temporales
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tra_file:
                tra_file.write(tra_xml)
                tra_temp = tra_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.cms', delete=False) as cms_file:
                cms_temp = cms_file.name
            
            try:
                # Comando OpenSSL
                cmd = [
                    self.openssl_path, 'smime', '-sign',
                    '-in', tra_temp,
                    '-out', cms_temp,
                    '-signer', self.config.CERT_PATH,
                    '-inkey', self.config.KEY_PATH,
                    '-outform', 'DER',
                    '-nodetach'
                ]
                
                print(f"📝 Ejecutando firma...")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    raise Exception(f"Error OpenSSL: {result.stderr}")
                
                # Leer archivo firmado
                with open(cms_temp, 'rb') as f:
                    cms_data = f.read()
                
                if len(cms_data) == 0:
                    raise Exception("Archivo CMS vacío")
                
                # Codificar en base64
                cms_b64 = base64.b64encode(cms_data).decode('utf-8')
                
                print("✅ TRA firmado correctamente")
                return cms_b64
                
            finally:
                # Limpiar archivos temporales
                try:
                    os.unlink(tra_temp)
                    os.unlink(cms_temp)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Error firmando TRA: {e}")
            raise Exception(f"Error firmando TRA: {e}")
    
    def get_ticket_access(self):
        """Obtener ticket de acceso de WSAA con cache inteligente"""
        try:
            # *** NUEVO: Cache inteligente de tokens ***
            if hasattr(self, 'token_timestamp') and self.token and self.sign:
                # Verificar si el token aún es válido (duran 12 horas, usamos 10 horas para estar seguros)
                tiempo_transcurrido = datetime.utcnow() - self.token_timestamp
                
                if tiempo_transcurrido < timedelta(hours=10):
                    print(f"🎫 Usando token existente (válido por {10 - tiempo_transcurrido.seconds//3600} horas más)")
                    return True
                else:
                    print("⏰ Token expirado, obteniendo uno nuevo...")
                    # Limpiar tokens viejos
                    self.token = None
                    self.sign = None
                    delattr(self, 'token_timestamp')
            
            print("🎫 Obteniendo nuevo ticket de acceso...")
            
            # Crear y firmar TRA
            tra_xml = self.crear_tra()
            tra_firmado = self.firmar_tra_openssl(tra_xml)
            
            # URL del WSAA
            wsaa_url = self.config.WSAA_URL + '?wsdl' if not self.config.WSAA_URL.endswith('?wsdl') else self.config.WSAA_URL
            
            print(f"🌐 Conectando con WSAA: {wsaa_url}")
            
            # USAR SESIÓN PERSONALIZADA
            session = crear_session_afip()
            
            from zeep.transports import Transport
            
            transport = Transport(session=session, timeout=60)
            client = Client(wsaa_url, transport=transport)
            
            # Enviar solicitud
            response = client.service.loginCms(tra_firmado)
            
            if response:
                # Procesar respuesta XML
                root = ET.fromstring(response)
                
                token_elem = root.find('.//token')
                sign_elem = root.find('.//sign')
                
                if token_elem is None or sign_elem is None:
                    raise Exception("Token o Sign no encontrados en respuesta")
                
                self.token = token_elem.text
                self.sign = sign_elem.text
                
                # *** NUEVO: Guardar timestamp del token ***
                self.token_timestamp = datetime.utcnow()
                
                print("✅ Ticket de acceso obtenido y guardado en cache")
                return True
            else:
                raise Exception("Respuesta vacía de WSAA")
                
        except Exception as e:
            error_msg = str(e)
            
            # *** NUEVO: Manejo específico del error de token duplicado ***
            if "El CEE ya posee un TA valido" in error_msg:
                print("⚠️ AFIP indica que ya hay un token válido")
                print("💡 Esperando 30 segundos y reintentando...")
                
                import time
                time.sleep(30)  # Esperar 30 segundos
                
                # Limpiar tokens y reintentar UNA SOLA VEZ
                self.token = None
                self.sign = None
                if hasattr(self, 'token_timestamp'):
                    delattr(self, 'token_timestamp')
                
                # Reintentar una vez
                try:
                    print("🔄 Reintentando obtener token...")
                    tra_xml = self.crear_tra()
                    tra_firmado = self.firmar_tra_openssl(tra_xml)
                    
                    session = crear_session_afip()
                    transport = Transport(session=session, timeout=60)
                    client = Client(wsaa_url, transport=transport)
                    
                    response = client.service.loginCms(tra_firmado)
                    
                    if response:
                        root = ET.fromstring(response)
                        token_elem = root.find('.//token')
                        sign_elem = root.find('.//sign')
                        
                        if token_elem is not None and sign_elem is not None:
                            self.token = token_elem.text
                            self.sign = sign_elem.text
                            self.token_timestamp = datetime.utcnow()
                            
                            print("✅ Token obtenido exitosamente en segundo intento")
                            return True
                    
                except Exception as e2:
                    print(f"❌ Segundo intento también falló: {e2}")
            
            print(f"❌ Error obteniendo ticket: {e}")
            return False

    def autorizar_comprobante(self, datos_comprobante):
        """
        Autorizar comprobante en AFIP usando WSFEv1 - VERSIÓN CORREGIDA
        """
        try:
            print("🎫 Verificando ticket de acceso...")
            
            # Verificar que tenemos ticket válido
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener ticket de acceso")
            
            print("🌐 Conectando con WSFEv1...")
            
            # IMPORTANTE: URL limpia y configuración correcta
            wsfev1_url = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
            
            # Crear cliente SOAP con configuración específica
            session = crear_session_afip()
            from zeep.transports import Transport
            from zeep import Settings
            
            # Configuración específica para AFIP
            settings = Settings(strict=False, xml_huge_tree=True)
            transport = Transport(session=session, timeout=60, operation_timeout=60)
            
            try:
                from zeep import Client
                client = Client(wsfev1_url, transport=transport, settings=settings)
                print("✅ Cliente WSFEv1 creado correctamente")
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['invalid xml', 'mismatch', 'html', 'br line', 'span']):
                    raise Exception("WSFEv1 devolviendo HTML en lugar de XML - Servicio en mantenimiento")
                else:
                    raise Exception(f"Error creando cliente SOAP: {str(e)}")
            
            # Preparar autenticación
            auth = {
                'Token': self.token,
                'Sign': self.sign,
                'Cuit': self.cuit
            }
            
            print("📋 Preparando datos del comprobante...")
            
            # Obtener configuración
            pto_vta = datos_comprobante.get('punto_venta', self.config.PUNTO_VENTA)
            tipo_cbte = datos_comprobante.get('tipo_comprobante', 11)  # 11 = Factura C
            
            # Test rápido con FEDummy para verificar que el servicio funciona
            try:
                print("🧪 Verificando servicio con FEDummy...")
                dummy_response = client.service.FEDummy()
                print(f"✅ FEDummy OK: {dummy_response}")
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['invalid xml', 'mismatch', 'html']):
                    raise Exception("FEDummy devolviendo HTML - WSFEv1 en mantenimiento")
                else:
                    print(f"⚠️ Warning en FEDummy: {e}")
            
            # Obtener último comprobante autorizado
            try:
                print("📊 Consultando último comprobante autorizado...")
                ultimo_cbte_response = client.service.FECompUltimoAutorizado(
                    Auth=auth,
                    PtoVta=pto_vta,
                    CbteTipo=tipo_cbte
                )
                
                # Verificar errores en la respuesta
                if hasattr(ultimo_cbte_response, 'Errors') and ultimo_cbte_response.Errors:
                    print(f"⚠️ Advertencias al obtener último comprobante:")
                    if hasattr(ultimo_cbte_response.Errors, 'Err'):
                        errors = ultimo_cbte_response.Errors.Err
                        if isinstance(errors, list):
                            for error in errors:
                                print(f"   [{error.Code}] {error.Msg}")
                        else:
                            print(f"   [{errors.Code}] {errors.Msg}")
                
                ultimo_nro = getattr(ultimo_cbte_response, 'CbteNro', 0)
                proximo_nro = ultimo_nro + 1
                
                print(f"📊 Último comprobante AFIP: {ultimo_nro}")
                print(f"📊 Próximo número: {proximo_nro}")
                
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['invalid xml', 'mismatch', 'html']):
                    raise Exception("FECompUltimoAutorizado devolviendo HTML")
                else:
                    print(f"⚠️ Error obteniendo último comprobante: {e}")
                    print("🔄 Usando número secuencial local...")
                    proximo_nro = 1
            
            # Preparar datos del comprobante
            fecha_hoy = datetime.now().strftime('%Y%m%d')
            
            # Calcular importes
            importe_neto = float(datos_comprobante.get('importe_neto', 0))
            importe_iva = float(datos_comprobante.get('importe_iva', 0))
            importe_total = importe_neto + importe_iva
            
            print(f"💰 Importes: Neto=${importe_neto:.2f}, IVA=${importe_iva:.2f}, Total=${importe_total:.2f}")
            
            # Estructura del comprobante según especificación AFIP
            comprobante = {
                'Concepto': 1,  # 1 = Productos
                'DocTipo': datos_comprobante.get('doc_tipo', 99),  # 99 = Sin identificar
                'DocNro': datos_comprobante.get('doc_nro', 0),
                'CbteDesde': proximo_nro,
                'CbteHasta': proximo_nro,
                'CbteFch': fecha_hoy,
                'ImpTotal': round(importe_total, 2),
                'ImpTotConc': 0.00,  # Importe neto no gravado
                'ImpNeto': round(importe_neto, 2),  # Importe neto gravado
                'ImpOpEx': 0.00,  # Importe exento
                'ImpTrib': 0.00,  # Otros tributos
                'ImpIVA': round(importe_iva, 2),  # Importe de IVA
                'MonId': 'PES',  # Pesos argentinos
                'MonCotiz': 1.00,  # Cotización = 1 para pesos
            }
            
            # Agregar detalle de IVA solo si hay IVA
            if importe_iva > 0:
                comprobante['Iva'] = {
                    'AlicIva': [{
                        'Id': 5,  # 5 = IVA 21%
                        'BaseImp': round(importe_neto, 2),
                        'Importe': round(importe_iva, 2)
                    }]
                }
            
            # Crear request completo
            fe_request = {
                'FeCabReq': {
                    'CantReg': 1,
                    'PtoVta': pto_vta,
                    'CbteTipo': tipo_cbte
                },
                'FeDetReq': {
                    'FECAEDetRequest': [comprobante]
                }
            }
            
            print("📤 Enviando solicitud de autorización a AFIP...")
            print(f"   Tipo comprobante: {tipo_cbte}")
            print(f"   Punto de venta: {pto_vta}")
            print(f"   Número: {proximo_nro}")
            print(f"   Fecha: {fecha_hoy}")
            print(f"   Total: ${importe_total:.2f}")
            
            # ENVÍO CRÍTICO - Aquí es donde fallaba antes
            try:
                response = client.service.FECAESolicitar(Auth=auth, FeCAEReq=fe_request)
                print("✅ Respuesta recibida de AFIP")
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['invalid xml', 'mismatch', 'html', 'br line', 'span']):
                    raise Exception("FECAESolicitar devolviendo HTML - WSFEv1 en mantenimiento")
                else:
                    raise Exception(f"Error en FECAESolicitar: {str(e)}")
            
            # Procesar respuesta de AFIP
            print("📋 Procesando respuesta de AFIP...")
            
            # Verificar errores generales
            if hasattr(response, 'Errors') and response.Errors:
                errores = []
                if hasattr(response.Errors, 'Err'):
                    errors = response.Errors.Err
                    if isinstance(errors, list):
                        for error in errors:
                            errores.append(f"[{error.Code}] {error.Msg}")
                    else:
                        errores.append(f"[{errors.Code}] {errors.Msg}")
                
                error_msg = " | ".join(errores)
                raise Exception(f"Errores AFIP: {error_msg}")
            
            # Verificar que hay respuesta de detalle
            if not hasattr(response, 'FeDetResp') or not response.FeDetResp:
                raise Exception("Respuesta de AFIP sin detalles")
            
            # Obtener detalle de respuesta
            if not hasattr(response.FeDetResp, 'FECAEDetResponse'):
                raise Exception("Respuesta de AFIP sin FECAEDetResponse")
            
            detalle_resp = response.FeDetResp.FECAEDetResponse[0]
            
            # Verificar resultado
            resultado = getattr(detalle_resp, 'Resultado', None)
            if resultado != 'A':  # A = Aprobado
                observaciones = []
                if hasattr(detalle_resp, 'Observaciones') and detalle_resp.Observaciones:
                    if hasattr(detalle_resp.Observaciones, 'Obs'):
                        obs_list = detalle_resp.Observaciones.Obs
                        if isinstance(obs_list, list):
                            for obs in obs_list:
                                observaciones.append(f"[{obs.Code}] {obs.Msg}")
                        else:
                            observaciones.append(f"[{obs_list.Code}] {obs_list.Msg}")
                
                obs_msg = " | ".join(observaciones) if observaciones else "Sin observaciones"
                raise Exception(f"Comprobante no autorizado. Resultado: {resultado}. {obs_msg}")
            
            # ÉXITO - Extraer datos
            cae = getattr(detalle_resp, 'CAE', None)
            fecha_vencimiento = getattr(detalle_resp, 'CAEFchVto', None)
            
            if not cae:
                raise Exception("Respuesta sin CAE")
            
            if not fecha_vencimiento:
                raise Exception("Respuesta sin fecha de vencimiento CAE")
            
            numero_completo = f"{pto_vta:04d}-{proximo_nro:08d}"
            
            print(f"🎉 ¡COMPROBANTE AUTORIZADO EXITOSAMENTE!")
            print(f"   Número: {numero_completo}")
            print(f"   CAE: {cae}")
            print(f"   Vencimiento CAE: {fecha_vencimiento}")
            
            return {
                'success': True,
                'cae': cae,
                'numero': numero_completo,
                'punto_venta': pto_vta,
                'numero_comprobante': proximo_nro,
                'fecha_vencimiento': fecha_vencimiento,
                'fecha_proceso': fecha_hoy,
                'importe_total': importe_total,
                'tipo_comprobante': tipo_cbte,
                'estado': 'autorizada',
                'vto_cae': datetime.strptime(fecha_vencimiento, '%Y%m%d').date()
            }
            
        except Exception as e:
            print(f"❌ Error en autorización AFIP: {e}")
            return {
                'success': False,
                'error': str(e),
                'cae': None,
                'vto_cae': None,
                'estado': 'error_afip'
            }

    def get_ultimo_comprobante(self, tipo_cbte):
        """Obtener último comprobante autorizado"""
        try:
            print(f"📋 Consultando último comprobante tipo {tipo_cbte}...")
            
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener acceso a AFIP")
            
            # URL del WSFEv1
            wsfe_url = self.config.WSFEv1_URL
            
            print(f"🌐 Conectando con WSFEv1: {wsfe_url}")
            
            # USAR SESIÓN PERSONALIZADA
            session = crear_session_afip()
            
            from zeep.transports import Transport
            
            transport = Transport(session=session, timeout=60)
            client = Client(wsfe_url, transport=transport)
            
            response = client.service.FECompUltimoAutorizado(
                Auth={
                    'Token': self.token,
                    'Sign': self.sign,
                    'Cuit': self.cuit
                },
                PtoVta=self.config.PUNTO_VENTA,
                CbteTipo=tipo_cbte
            )
            
            if hasattr(response, 'Errors') and response.Errors:
                error_msg = response.Errors.Err[0].Msg
                raise Exception(f"Error AFIP: {error_msg}")
            
            ultimo_num = response.CbteNro
            print(f"✅ Último comprobante: {ultimo_num}")
            return ultimo_num
            
        except Exception as e:
            print(f"❌ Error consultando comprobante: {e}")
            raise Exception(f"Error al obtener último comprobante: {e}")


arca_client = ARCAClient()

# Monitor AFIP simplificado
class AFIPStatusMonitor:
    def __init__(self, arca_config):
        self.config = arca_config
    
    def verificar_rapido(self):
        """Verificación rápida solo de conectividad"""
        try:
            import socket
            from urllib.parse import urlparse
            
            wsaa_host = urlparse(self.config.WSAA_URL).hostname
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((wsaa_host, 443))
            sock.close()
            
            return {
                'conectividad': result == 0,
                'mensaje': '✅ AFIP accesible' if result == 0 else '❌ AFIP no accesible'
            }
        except Exception as e:
            return {
                'conectividad': False,
                'mensaje': f'❌ Error: {str(e)}'
            }

# Crear instancia del monitor
afip_monitor = AFIPStatusMonitor(ARCA_CONFIG)


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

# ==================== RUTAS DE CLIENTES ====================

@app.route('/api/cliente/<int:cliente_id>')
def obtener_cliente(cliente_id):
    """Obtener datos de un cliente por ID para edición"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Método compatible con SQLAlchemy antiguo
        cliente = Cliente.query.get_or_404(cliente_id)
        return jsonify({
            'id': cliente.id,
            'nombre': cliente.nombre,
            'documento': cliente.documento or '',
            'tipo_documento': cliente.tipo_documento or 'DNI',
            'email': cliente.email or '',
            'telefono': cliente.telefono or '',
            'direccion': cliente.direccion or '',
            'condicion_iva': cliente.condicion_iva or 'CONSUMIDOR_FINAL'
        })
    except Exception as e:
        return jsonify({'error': f'Error al obtener cliente: {str(e)}'}), 500

@app.route('/guardar_cliente', methods=['POST'])
def guardar_cliente():
    """Crear o actualizar un cliente"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        
        # Validar datos requeridos
        if not data.get('nombre', '').strip():
            return jsonify({'error': 'El nombre es obligatorio'}), 400
        
        # Validar CUIT si es necesario
        if data.get('tipo_documento') == 'CUIT' and data.get('documento'):
            documento = data['documento'].strip()
            if not documento.isdigit() or len(documento) != 11:
                return jsonify({'error': 'El CUIT debe tener 11 dígitos sin guiones'}), 400
        
        cliente_id = data.get('id')
        
        if cliente_id:  # Editar cliente existente
            cliente = Cliente.query.get_or_404(cliente_id)
            accion = 'actualizado'
        else:  # Crear nuevo cliente
            cliente = Cliente()
            accion = 'creado'
        
        # Actualizar datos del cliente
        cliente.nombre = data['nombre'].strip()
        cliente.documento = data.get('documento', '').strip() or None
        cliente.tipo_documento = data.get('tipo_documento', 'DNI')
        cliente.email = data.get('email', '').strip() or None
        cliente.telefono = data.get('telefono', '').strip() or None
        cliente.direccion = data.get('direccion', '').strip() or None
        cliente.condicion_iva = data.get('condicion_iva', 'CONSUMIDOR_FINAL')
        
        # Guardar en base de datos
        if not cliente_id:  # Solo agregar si es nuevo
            db.session.add(cliente)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cliente {accion} correctamente',
            'cliente_id': cliente.id,
            'cliente_nombre': cliente.nombre
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error guardando cliente: {str(e)}")
        return jsonify({'error': f'Error al guardar cliente: {str(e)}'}), 500

@app.route('/eliminar_cliente/<int:cliente_id>', methods=['DELETE'])
def eliminar_cliente(cliente_id):
    """Eliminar un cliente (marcar como inactivo)"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Verificar si tiene facturas asociadas
        facturas_count = Factura.query.filter_by(cliente_id=cliente_id).count()
        
        if facturas_count > 0:
            return jsonify({
                'error': f'No se puede eliminar el cliente porque tiene {facturas_count} facturas asociadas'
            }), 400
        
        # Si no tiene facturas, se puede eliminar
        db.session.delete(cliente)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cliente eliminado correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error eliminando cliente: {str(e)}")
        return jsonify({'error': f'Error al eliminar cliente: {str(e)}'}), 500

@app.route('/buscar_clientes')
def buscar_clientes():
    """Buscar clientes con filtros"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Obtener parámetros de búsqueda
        buscar = request.args.get('buscar', '').strip()
        tipo_doc = request.args.get('tipo_documento', '').strip()
        condicion_iva = request.args.get('condicion_iva', '').strip()
        
        # Construir query base
        query = Cliente.query
        
        # Aplicar filtros
        if buscar:
            query = query.filter(
                or_(
                    Cliente.nombre.ilike(f'%{buscar}%'),
                    Cliente.documento.ilike(f'%{buscar}%'),
                    Cliente.email.ilike(f'%{buscar}%')
                )
            )
        
        if tipo_doc:
            query = query.filter(Cliente.tipo_documento == tipo_doc)
        
        if condicion_iva:
            query = query.filter(Cliente.condicion_iva == condicion_iva)
        
        # Obtener resultados
        clientes = query.order_by(Cliente.nombre).all()
        
        # Formatear respuesta
        resultado = []
        for cliente in clientes:
            resultado.append({
                'id': cliente.id,
                'nombre': cliente.nombre,
                'documento': cliente.documento,
                'tipo_documento': cliente.tipo_documento,
                'email': cliente.email,
                'telefono': cliente.telefono,
                'direccion': cliente.direccion,
                'condicion_iva': cliente.condicion_iva
            })
        
        return jsonify({
            'success': True,
            'clientes': resultado,
            'total': len(resultado)
        })
        
    except Exception as e:
        print(f"Error buscando clientes: {str(e)}")
        return jsonify({'error': f'Error en la búsqueda: {str(e)}'}), 500

# ==================== RUTAS DE PRODUCTOS ====================

@app.route('/api/producto_detalle/<int:producto_id>')
def obtener_producto_detalle(producto_id):
    """Obtener datos completos de un producto para edición"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Método compatible con SQLAlchemy antiguo
        producto = Producto.query.get_or_404(producto_id)
        return jsonify({
            'id': producto.id,
            'codigo': producto.codigo,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion or '',
            'precio': float(producto.precio),
            'stock': producto.stock,
            'categoria': producto.categoria or '',
            'iva': float(producto.iva),
            'activo': producto.activo
        })
    except Exception as e:
        return jsonify({'error': f'Error al obtener producto: {str(e)}'}), 500

@app.route('/guardar_producto', methods=['POST'])
def guardar_producto():
    """Crear o actualizar un producto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        
        # Validar datos requeridos
        if not data.get('codigo', '').strip():
            return jsonify({'error': 'El código es obligatorio'}), 400
        
        if not data.get('nombre', '').strip():
            return jsonify({'error': 'El nombre es obligatorio'}), 400
        
        try:
            precio = float(data.get('precio', 0))
            if precio <= 0:
                return jsonify({'error': 'El precio debe ser mayor a 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Precio inválido'}), 400
        
        producto_id = data.get('id')
        codigo = data['codigo'].strip().upper()
        
        # Verificar que el código no exista (excepto si es el mismo producto)
        producto_existente = Producto.query.filter_by(codigo=codigo).first()
        if producto_existente and (not producto_id or producto_existente.id != int(producto_id)):
            return jsonify({'error': f'Ya existe un producto con el código {codigo}'}), 400
        
        if producto_id:  # Editar producto existente
            producto = Producto.query.get_or_404(producto_id)
            accion = 'actualizado'
        else:  # Crear nuevo producto
            producto = Producto()
            accion = 'creado'
        
        # Actualizar datos del producto
        producto.codigo = codigo
        producto.nombre = data['nombre'].strip()
        producto.descripcion = data.get('descripcion', '').strip() or None
        producto.precio = precio
        producto.categoria = data.get('categoria', '').strip() or None
        producto.iva = float(data.get('iva', 21))
        producto.activo = bool(data.get('activo', True))
        
        # Solo actualizar stock si es producto nuevo
        if not producto_id:
            producto.stock = int(data.get('stock', 0))
        
        # Guardar en base de datos
        if not producto_id:  # Solo agregar si es nuevo
            db.session.add(producto)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Producto {accion} correctamente',
            'producto_id': producto.id,
            'producto_codigo': producto.codigo
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error guardando producto: {str(e)}")
        return jsonify({'error': f'Error al guardar producto: {str(e)}'}), 500

@app.route('/ajustar_stock', methods=['POST'])
def ajustar_stock():
    """Ajustar stock de un producto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        
        producto_id = data.get('producto_id')
        tipo_movimiento = data.get('tipo_movimiento')  # entrada, salida, ajuste
        cantidad = int(data.get('cantidad', 0))
        motivo = data.get('motivo', '').strip()
        
        if not producto_id:
            return jsonify({'error': 'ID de producto requerido'}), 400
        
        if cantidad <= 0 and tipo_movimiento != 'ajuste':
            return jsonify({'error': 'La cantidad debe ser mayor a 0'}), 400
        
        producto = Producto.query.get_or_404(producto_id)
        stock_anterior = producto.stock
        
        # Aplicar movimiento según el tipo
        if tipo_movimiento == 'entrada':
            producto.stock += cantidad
            descripcion = f"Entrada: +{cantidad}"
        elif tipo_movimiento == 'salida':
            if cantidad > producto.stock:
                return jsonify({'error': f'No hay suficiente stock. Stock actual: {producto.stock}'}), 400
            producto.stock -= cantidad
            descripcion = f"Salida: -{cantidad}"
        elif tipo_movimiento == 'ajuste':
            if cantidad < 0:
                return jsonify({'error': 'La cantidad para ajuste no puede ser negativa'}), 400
            descripcion = f"Ajuste: {stock_anterior} → {cantidad}"
            producto.stock = cantidad
        else:
            return jsonify({'error': 'Tipo de movimiento inválido'}), 400
        
        # Guardar cambios
        db.session.commit()
        
        # Registrar el movimiento (opcional - puedes crear una tabla de movimientos)
        print(f"MOVIMIENTO STOCK: Producto {producto.codigo} - {descripcion} - Motivo: {motivo}")
        
        return jsonify({
            'success': True,
            'message': f'Stock ajustado correctamente',
            'stock_anterior': stock_anterior,
            'stock_nuevo': producto.stock,
            'movimiento': descripcion
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error ajustando stock: {str(e)}")
        return jsonify({'error': f'Error al ajustar stock: {str(e)}'}), 500

@app.route('/toggle_producto/<int:producto_id>', methods=['POST'])
def toggle_producto(producto_id):
    """Activar/desactivar un producto"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        producto = Producto.query.get_or_404(producto_id)
        
        # Cambiar estado
        producto.activo = not producto.activo
        estado = 'activado' if producto.activo else 'desactivado'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Producto {estado} correctamente',
            'activo': producto.activo
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cambiando estado del producto: {str(e)}")
        return jsonify({'error': f'Error al cambiar estado: {str(e)}'}), 500

@app.route('/buscar_productos_admin')
def buscar_productos_admin():
    """Buscar productos con filtros para administración"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Obtener parámetros de búsqueda
        buscar = request.args.get('buscar', '').strip()
        categoria = request.args.get('categoria', '').strip()
        filtro_stock = request.args.get('stock', '').strip()
        
        # Construir query base
        query = Producto.query
        
        # Aplicar filtros
        if buscar:
            query = query.filter(
                or_(
                    Producto.codigo.ilike(f'%{buscar}%'),
                    Producto.nombre.ilike(f'%{buscar}%'),
                    Producto.descripcion.ilike(f'%{buscar}%')
                )
            )
        
        if categoria:
            query = query.filter(Producto.categoria == categoria)
        
        if filtro_stock == 'bajo':
            query = query.filter(Producto.stock < 10)
        elif filtro_stock == 'sin_stock':
            query = query.filter(Producto.stock <= 0)
        
        # Obtener resultados
        productos = query.order_by(Producto.codigo).all()
        
        # Formatear respuesta
        resultado = []
        for producto in productos:
            resultado.append({
                'id': producto.id,
                'codigo': producto.codigo,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': float(producto.precio),
                'stock': producto.stock,
                'categoria': producto.categoria,
                'iva': float(producto.iva),
                'activo': producto.activo
            })
        
        return jsonify({
            'success': True,
            'productos': resultado,
            'total': len(resultado)
        })
        
    except Exception as e:
        print(f"Error buscando productos: {str(e)}")
        return jsonify({'error': f'Error en la búsqueda: {str(e)}'}), 500

@app.route('/obtener_categorias')
def obtener_categorias():
    """Obtener lista de categorías únicas"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Obtener categorías únicas de productos existentes
        categorias = db.session.query(Producto.categoria).filter(
            Producto.categoria.isnot(None),
            Producto.categoria != ''
        ).distinct().all()
        
        categorias_lista = [cat[0] for cat in categorias if cat[0]]
        categorias_lista.sort()
        
        return jsonify({
            'success': True,
            'categorias': categorias_lista
        })
        
    except Exception as e:
        print(f"Error obteniendo categorías: {str(e)}")
        return jsonify({'error': f'Error al obtener categorías: {str(e)}'}), 500

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

# FUNCIÓN PROCESAR_VENTA CORREGIDA
# REEMPLAZA la función procesar_venta completa (línea ~1200 aprox) con esta versión corregida:

@app.route('/procesar_venta', methods=['POST'])
def procesar_venta():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        
        # PASO 1: Determinar el próximo número de comprobante
        tipo_comprobante = int(data.get('tipo_comprobante', '11'))
        punto_venta = ARCA_CONFIG.PUNTO_VENTA
        
        # PASO 2: Generar número temporal primero
        ultima_factura_local = Factura.query.filter_by(
            tipo_comprobante=str(tipo_comprobante),
            punto_venta=punto_venta
        ).order_by(Factura.id.desc()).first()
        
        numero_temporal = 1
        if ultima_factura_local and ultima_factura_local.numero:
            try:
                ultimo_numero_local = int(ultima_factura_local.numero.split('-')[1])
                numero_temporal = ultimo_numero_local + 1
            except:
                numero_temporal = 1
        
        # Generar número temporal para la base de datos
        numero_factura_temporal = f"{punto_venta:04d}-{numero_temporal:08d}"
        
        # Verificar que el número temporal no exista
        factura_existente = Factura.query.filter_by(numero=numero_factura_temporal).first()
        while factura_existente:
            numero_temporal += 1
            numero_factura_temporal = f"{punto_venta:04d}-{numero_temporal:08d}"
            factura_existente = Factura.query.filter_by(numero=numero_factura_temporal).first()
        
        print(f"📝 Número temporal asignado: {numero_factura_temporal}")
        
        # PASO 3: Crear factura CON número temporal
        factura = Factura(
            numero=numero_factura_temporal,  # ← USAR NÚMERO TEMPORAL
            tipo_comprobante=str(tipo_comprobante),
            punto_venta=punto_venta,
            cliente_id=data['cliente_id'],
            usuario_id=session['user_id'],
            subtotal=Decimal(str(data['subtotal'])),
            iva=Decimal(str(data['iva'])),
            total=Decimal(str(data['total']))
        )
        
        db.session.add(factura)
        db.session.flush()  # Para obtener el ID sin hacer commit
        
        print(f"✅ Factura creada con ID: {factura.id} y número temporal: {factura.numero}")
        
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
                print(f"📦 Stock actualizado para {producto.nombre}: {producto.stock}")
        
        # PASO 5: Intentar autorizar en AFIP
        try:
            print("📄 Autorizando en AFIP...")
            cliente = Cliente.query.get(data['cliente_id'])
            
            # Preparar datos para AFIP
            datos_comprobante = {
                'tipo_comprobante': tipo_comprobante,
                'punto_venta': punto_venta,
                'importe_neto': float(factura.subtotal),
                'importe_iva': float(factura.iva),
                'doc_tipo': 99,  # Sin identificar por defecto
                'doc_nro': 0
            }
            
            # Si el cliente tiene documento, agregar datos
            if cliente and cliente.documento:
                if cliente.tipo_documento == 'CUIT' and len(cliente.documento) == 11:
                    datos_comprobante['doc_tipo'] = 80  # CUIT
                    datos_comprobante['doc_nro'] = int(cliente.documento)
                elif cliente.tipo_documento == 'DNI' and len(cliente.documento) >= 7:
                    datos_comprobante['doc_tipo'] = 96  # DNI
                    datos_comprobante['doc_nro'] = int(cliente.documento)
            
            resultado_afip = arca_client.autorizar_comprobante(datos_comprobante)
            
            if resultado_afip['success']:
                # AFIP devuelve el número correcto - ACTUALIZAR la factura
                numero_afip = resultado_afip['numero']
                print(f"✅ AFIP asignó número: {numero_afip}")
                
                # Verificar si el número de AFIP ya existe en la BD
                factura_afip_existente = Factura.query.filter(
                    and_(Factura.numero == numero_afip, Factura.id != factura.id)
                ).first()
                
                if factura_afip_existente:
                    print(f"⚠️ Número AFIP {numero_afip} ya existe, manteniendo temporal")
                    # Mantener número temporal y marcar como autorizada
                    factura.cae = resultado_afip['cae']
                    factura.vto_cae = resultado_afip['vto_cae']
                    factura.estado = 'autorizada'
                else:
                    # Actualizar con número de AFIP
                    factura.numero = numero_afip
                    factura.cae = resultado_afip['cae']
                    factura.vto_cae = resultado_afip['vto_cae']
                    factura.estado = 'autorizada'
                
                print(f"✅ Autorización AFIP exitosa. CAE: {factura.cae}")
                print(f"✅ Número final: {factura.numero}")
            else:
                # Si AFIP falla, mantener número temporal
                factura.estado = 'error_afip'
                print(f"❌ Error AFIP: {resultado_afip.get('error', 'Error desconocido')}")
                print(f"📝 Manteniendo número temporal: {factura.numero}")
            
        except Exception as e:
            # Si hay error completo, mantener número temporal
            factura.estado = 'error_afip'
            print(f"❌ Error completo al autorizar en AFIP: {e}")
            print(f"📝 Manteniendo número temporal: {factura.numero}")
            
        # PASO 6: Guardar todo en la base de datos
        db.session.commit()
        
        print(f"🎉 Venta procesada exitosamente: {factura.numero}")
        
        # PASO 7: Imprimir automáticamente si está configurado
        imprimir_automatico = data.get('imprimir_automatico', True)
        if imprimir_automatico and IMPRESION_DISPONIBLE:
            try:
                print("🖨️ Imprimiendo factura automáticamente...")
                impresora_termica.imprimir_factura(factura)
            except Exception as e:
                print(f"⚠️ Error en impresión automática: {e}")
        
        return jsonify({
            'success': True,
            'factura_id': factura.id,
            'numero': factura.numero,
            'cae': factura.cae,
            'estado': factura.estado,
            'mensaje': f"Factura {factura.numero} generada correctamente"
        })
        
    except Exception as e:
        print(f"❌ Error en procesar_venta: {str(e)}")
        db.session.rollback()
        return jsonify({'error': f'Error al procesar la venta: {str(e)}'}), 500



# RUTAS DE IMPRESIÓN
@app.route('/imprimir_factura/<int:factura_id>')
def imprimir_factura(factura_id):
    """Endpoint para imprimir factura específica"""
    try:
        print(f"🖨️ Iniciando impresión de factura ID: {factura_id}")
        
        # Obtener la factura de la base de datos
        factura = Factura.query.get_or_404(factura_id)
        
        # Usar directamente la instancia de la clase
        resultado = impresora_termica.imprimir_factura(factura)
        
        if resultado:
            return jsonify({
                'success': True,
                'mensaje': f'Factura impresa correctamente en {impresora_termica.nombre_impresora}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al imprimir factura'
            })
        
    except Exception as e:
        print(f"❌ Error en endpoint imprimir: {e}")
        return jsonify({
            'success': False,
            'error': f'Error al imprimir factura: {str(e)}'
        }), 500
        
@app.route('/test_impresion')
def test_impresion():
    try:
        print("🧪 Iniciando test de impresión...")
        resultado = impresora_termica.test_impresion()  # ← Llama al método de la clase
        
        if resultado:
            return jsonify({
                'success': True,
                'mensaje': f'Test enviado correctamente a {impresora_termica.nombre_impresora}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al enviar test de impresión'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en test: {str(e)}'
        }), 500

@app.route('/estado_impresora')
def estado_impresora():
    """Endpoint para verificar estado de impresora"""
    try:
        estado = impresora_termica.verificar_estado()
        return jsonify(estado)
    except Exception as e:
        return jsonify({
            'disponible': False,
            'error': f'Error verificando estado: {str(e)}'
        }), 500

@app.route('/facturas')
def facturas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    facturas = Factura.query.order_by(Factura.fecha.desc()).limit(100).all()
    return render_template('facturas.html', facturas=facturas)

@app.route('/factura/<int:factura_id>')
def ver_factura(factura_id):
    try:
        # Método compatible con SQLAlchemy antiguo
        factura = Factura.query.get_or_404(factura_id)
        
        return render_template('factura_detalle.html', factura=factura)
        
    except Exception as e:
        app.logger.error(f"Error al cargar factura {factura_id}: {str(e)}")
        flash('Error al cargar la factura', 'error')
        return redirect(url_for('facturas'))

# Funciones de utilidad para limpieza de datos
def limpiar_facturas_duplicadas():
    """Limpiar facturas duplicadas o problemáticas"""
    try:
        # Buscar facturas con números duplicados
        facturas_duplicadas = db.session.query(Factura.numero).group_by(Factura.numero).having(db.func.count(Factura.numero) > 1).all()
        
        if facturas_duplicadas:
            print(f"⚠️ Encontradas {len(facturas_duplicadas)} facturas con números duplicados")
            
            for numero_duplicado in facturas_duplicadas:
                numero = numero_duplicado[0]
                facturas = Factura.query.filter_by(numero=numero).order_by(Factura.id).all()
                
                # Mantener solo la primera, eliminar las demás
                for i, factura in enumerate(facturas):
                    if i > 0:  # Eliminar todas excepto la primera
                        print(f"🗑️ Eliminando factura duplicada: {factura.numero} (ID: {factura.id})")
                        
                        # Eliminar detalles primero
                        DetalleFactura.query.filter_by(factura_id=factura.id).delete()
                        
                        # Eliminar factura
                        db.session.delete(factura)
            
            db.session.commit()
            print("✅ Limpieza de duplicados completada")
        else:
            print("✅ No se encontraron facturas duplicadas")
            
    except Exception as e:
        print(f"❌ Error en limpieza: {e}")
        db.session.rollback()

def verificar_estado_facturas():
    """Verificar el estado actual de las facturas"""
    try:
        total_facturas = Factura.query.count()
        facturas_con_cae = Factura.query.filter(Factura.cae.isnot(None)).count()
        facturas_pendientes = Factura.query.filter_by(estado='pendiente').count()
        facturas_error = Factura.query.filter_by(estado='error_afip').count()
        
        print("\n📊 ESTADO ACTUAL DE FACTURAS:")
        print(f"   Total facturas: {total_facturas}")
        print(f"   Con CAE: {facturas_con_cae}")
        print(f"   Pendientes: {facturas_pendientes}")
        print(f"   Con errores: {facturas_error}")
        
        # Mostrar últimas facturas
        ultimas_facturas = Factura.query.order_by(Factura.id.desc()).limit(5).all()
        print(f"\n📋 ÚLTIMAS 5 FACTURAS:")
        for factura in ultimas_facturas:
            cae_status = f"CAE: {factura.cae[:10]}..." if factura.cae else "Sin CAE"
            print(f"   {factura.numero} - {factura.estado} - {cae_status}")
        
    except Exception as e:
        print(f"❌ Error verificando estado: {e}")

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

@app.route('/qr_afip/<int:factura_id>')
def generar_qr_afip(factura_id):
    try:
        # Método compatible con SQLAlchemy antiguo
        factura = Factura.query.get_or_404(factura_id)
        
        try:
            generador_qr = crear_generador_qr(ARCA_CONFIG)  # ← Ya está correcto
            
            # Generar imagen QR
            qr_base64 = generador_qr.generar_qr_imagen(factura)
            info_qr = generador_qr.obtener_info_qr(factura)
            
            if qr_base64:
                return jsonify({
                    'success': True,
                    'qr_image': qr_base64,
                    'qr_url': info_qr['url'],
                    'qr_valido': info_qr['valido'],
                    'mensaje': info_qr['mensaje']
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Error al generar código QR'
                }), 500
                
        except ImportError:
            return jsonify({
                'success': False,
                'error': 'Módulo QR no disponible'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

# Ruta para mostrar QR en página completa (para escanear con móvil)
@app.route('/mostrar_qr/<int:factura_id>')
def mostrar_qr_completo(factura_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Método compatible con SQLAlchemy antiguo
    factura = Factura.query.get_or_404(factura_id)
    
    try:
        generador_qr = crear_generador_qr(ARCA_CONFIG)  # ← Ya está correcto
        info_qr = generador_qr.obtener_info_qr(factura)
        qr_base64 = generador_qr.generar_qr_imagen(factura, tamaño=8) if info_qr['valido'] else None
    except Exception as e:
        print(f"⚠️ Error generando QR: {e}")
        info_qr = {'valido': False, 'mensaje': f'Error al generar QR: {str(e)}'}
        qr_base64 = None
    
    return render_template('mostrar_qr.html', 
                         factura=factura, 
                         qr_info=info_qr,
                         qr_image=qr_base64)

# Ruta para validar datos QR
@app.route('/validar_qr/<int:factura_id>')
def validar_qr_factura(factura_id):
    try:
        # Método compatible con SQLAlchemy antiguo
        factura = Factura.query.get_or_404(factura_id)
        
        try:
            generador_qr = crear_generador_qr(ARCA_CONFIG)  # ← Ya está correcto
            info_qr = generador_qr.obtener_info_qr(factura)
            errores = generador_qr.validar_datos_qr(factura)
        except Exception as e:
            print(f"⚠️ Error con módulo QR: {e}")
            info_qr = {'valido': False, 'mensaje': f'Error con módulo QR: {str(e)}'}
            errores = [str(e)]
        
        return jsonify({
            'factura_id': factura_id,
            'numero': factura.numero,
            'qr_valido': info_qr['valido'],
            'qr_url': info_qr['url'] if info_qr['valido'] else None,
            'errores': errores,
            'datos_qr': info_qr.get('datos', {}),
            'mensaje': info_qr['mensaje']
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error validando QR: {str(e)}'
        }), 500



@app.route('/api/estado_afip_rapido')
def api_estado_afip_rapido():
    """API para verificación rápida de AFIP"""
    try:
        estado = afip_monitor.verificar_rapido()
        return jsonify({
            'success': True,
            'estado': estado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test_afip')
def test_afip():
    """Test manual de conexión AFIP"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        resultado_auth = arca_client.get_ticket_access()
        
        return jsonify({
            'success': resultado_auth,
            'mensaje': "✅ Test AFIP exitoso" if resultado_auth else "❌ Test AFIP falló",
            'estado': "success" if resultado_auth else "error",
            'tiene_token': bool(arca_client.token),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'mensaje': f"❌ Error en test: {str(e)}",
            'estado': 'error'
        }), 500


# Agregar esta función en app.py para debug de WSFEv1

# Versión simplificada sin verificación de sesión para debug
##### http://localhost:5000/debug_afip_simple LLAMAR ESTA RUTA PARA VERIFICAR ARCA

@app.route('/debug_afip_simple')
def debug_afip_simple():
    """Debug simple de AFIP sin verificación de sesión"""
    try:
        resultado = {
            'timestamp': datetime.utcnow().isoformat(),
            'tests': {}
        }
        
        print("🔍 INICIANDO DEBUG SIMPLE DE AFIP...")
        
        # Test 1: Autenticación WSAA
        print("1️⃣ Test autenticación WSAA...")
        try:
            auth_result = arca_client.get_ticket_access()
            resultado['tests']['wsaa_auth'] = {
                'success': auth_result,
                'token_exists': bool(arca_client.token),
                'message': 'Autenticación exitosa' if auth_result else 'Fallo en autenticación'
            }
        except Exception as e:
            resultado['tests']['wsaa_auth'] = {
                'success': False,
                'error': str(e),
                'message': 'Error en autenticación'
            }
        
        # Test 2: Conectividad WSFEv1
        print("2️⃣ Test conectividad WSFEv1...")
        try:
            import socket
            from urllib.parse import urlparse
            
            wsfe_url = ARCA_CONFIG.WSFEv1_URL
            parsed = urlparse(wsfe_url)
            host = parsed.hostname
            port = 443
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            connect_result = sock.connect_ex((host, port))
            sock.close()
            
            resultado['tests']['wsfe_connectivity'] = {
                'success': connect_result == 0,
                'host': host,
                'port': port,
                'url': wsfe_url,
                'message': 'Conectividad OK' if connect_result == 0 else f'No se puede conectar (código: {connect_result})'
            }
        except Exception as e:
            resultado['tests']['wsfe_connectivity'] = {
                'success': False,
                'error': str(e),
                'message': 'Error verificando conectividad'
            }
        
        # Test 3: Solo si tenemos autenticación, probar FEDummy
        if resultado['tests']['wsaa_auth']['success']:
            print("3️⃣ Test FEDummy...")
            try:
                from zeep import Client
                from zeep.transports import Transport
                
                session_afip = crear_session_afip()
                transport = Transport(session=session_afip, timeout=30)
                client = Client(ARCA_CONFIG.WSFEv1_URL, transport=transport)
                
                dummy_response = client.service.FEDummy()
                
                resultado['tests']['fe_dummy'] = {
                    'success': True,
                    'response': str(dummy_response),
                    'message': 'FEDummy exitoso'
                }
            except Exception as e:
                resultado['tests']['fe_dummy'] = {
                    'success': False,
                    'error': str(e),
                    'message': 'Error en FEDummy'
                }
        
        # Generar resumen
        total_tests = len(resultado['tests'])
        successful_tests = sum(1 for test in resultado['tests'].values() if test['success'])
        
        resultado['summary'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': f"{(successful_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%",
            'overall_status': 'OK' if successful_tests == total_tests else 'PROBLEMAS'
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error general: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500



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
    print(f"🖨️ Impresión: {'Disponible' if IMPRESION_DISPONIBLE else 'No disponible'}")
    print(f"👤 Usuario: admin")
    print(f"🔑 Contraseña: admin123")
    print()
    
    with app.app_context():
        create_tables()
        
        # Limpiar datos problemáticos
        print("🧹 Verificando integridad de datos...")
        limpiar_facturas_duplicadas()
        verificar_estado_facturas()
    





app.run(debug=True, host='0.0.0.0', port=5000)