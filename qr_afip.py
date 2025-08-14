# qr_afip.py - Generador de códigos QR para AFIP Argentina

import base64
import hashlib
from datetime import datetime
import io

try:
    import qrcode
    from PIL import Image
    QR_DISPONIBLE = True
    print("✅ Módulo QR disponible")
except ImportError:
    QR_DISPONIBLE = False
    print("⚠️ Módulo QR no disponible. Instalar: pip install qrcode[pil] pillow")

class GeneradorQR:
    """Generador de códigos QR para facturas AFIP"""
    
    def __init__(self, config):
        self.config = config
        self.cuit = config.CUIT
        self.punto_venta = config.PUNTO_VENTA
        
    def obtener_info_qr(self, factura):
        """Obtener información del QR de una factura"""
        try:
            # Verificar que la factura tenga CAE
            if not factura.cae:
                return {
                    'valido': False,
                    'mensaje': 'Factura sin CAE de AFIP',
                    'url': None,
                    'datos': {}
                }
            
            # Verificar que el CAE sea válido
            if not factura.cae or len(str(factura.cae)) < 14:
                return {
                    'valido': False,
                    'mensaje': 'CAE inválido',
                    'url': None,
                    'datos': {}
                }
            
            # Construir datos del QR según especificación AFIP
            datos_qr = self._construir_datos_qr(factura)
            
            # Generar URL del QR
            url_qr = self._generar_url_qr(datos_qr)
            
            return {
                'valido': True,
                'mensaje': 'QR AFIP válido',
                'url': url_qr,
                'datos': datos_qr
            }
            
        except Exception as e:
            return {
                'valido': False,
                'mensaje': f'Error generando QR: {str(e)}',
                'url': None,
                'datos': {}
            }
    
    def _construir_datos_qr(self, factura):
        """Construir estructura de datos para QR según AFIP"""
        
        # Obtener datos del cliente
        if factura.cliente and factura.cliente.documento:
            nro_doc = factura.cliente.documento
            tipo_doc = '80' if factura.cliente.tipo_documento == 'CUIT' else '96'  # CUIT o DNI
        else:
            nro_doc = '0'
            tipo_doc = '99'  # Sin identificar
        
        # Formatear fecha (YYYY-MM-DD)
        fecha_cbte = factura.fecha.strftime('%Y-%m-%d')
        
        # Construir datos según especificación AFIP
        datos = {
            'ver': 1,  # Versión del QR
            'fecha': fecha_cbte,
            'cuit': int(self.cuit),
            'ptoVta': factura.punto_venta,
            'tipoCmp': int(factura.tipo_comprobante),
            'nroCmp': self._extraer_numero_comprobante(factura.numero),
            'importe': float(factura.total),
            'moneda': 'PES',  # Pesos argentinos
            'ctz': 1.00,  # Cotización (siempre 1 para pesos)
            'tipoDocRec': int(tipo_doc),
            'nroDocRec': int(nro_doc) if nro_doc.isdigit() else 0,
            'tipoCodAut': 'E',  # Tipo de código de autorización (E = CAE)
            'codAut': int(factura.cae)
        }
        
        return datos
    
    def _extraer_numero_comprobante(self, numero_completo):
        """Extraer número de comprobante del formato PPPP-NNNNNNNN"""
        try:
            if '-' in numero_completo:
                return int(numero_completo.split('-')[1])
            else:
                return int(numero_completo)
        except:
            return 1
    
    def _generar_url_qr(self, datos):
        """Generar URL del QR según especificación AFIP"""
        
        # URL base de AFIP para validación
        base_url = "https://www.afip.gob.ar/fe/qr/"
        
        # Construir query string
        params = []
        params.append(f"p={datos['ver']}")  # Versión
        params.append(f"p={datos['fecha']}")  # Fecha
        params.append(f"p={datos['cuit']}")  # CUIT emisor
        params.append(f"p={datos['ptoVta']}")  # Punto de venta
        params.append(f"p={datos['tipoCmp']}")  # Tipo comprobante
        params.append(f"p={datos['nroCmp']}")  # Número comprobante
        params.append(f"p={datos['importe']:.2f}")  # Importe
        params.append(f"p={datos['moneda']}")  # Moneda
        params.append(f"p={datos['ctz']:.2f}")  # Cotización
        params.append(f"p={datos['tipoDocRec']}")  # Tipo doc receptor
        params.append(f"p={datos['nroDocRec']}")  # Nro doc receptor
        params.append(f"p={datos['tipoCodAut']}")  # Tipo código autorización
        params.append(f"p={datos['codAut']}")  # Código autorización (CAE)
        
        # Construir URL completa
        query_string = "&".join(params)
        url_completa = f"{base_url}?{query_string}"
        
        return url_completa
    
    def generar_qr_imagen(self, factura, tamaño=6):
        """Generar imagen QR en base64"""
        if not QR_DISPONIBLE:
            return None
            
        try:
            info_qr = self.obtener_info_qr(factura)
            
            if not info_qr['valido']:
                return None
            
            # Crear código QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=tamaño,
                border=4,
            )
            
            qr.add_data(info_qr['url'])
            qr.make(fit=True)
            
            # Crear imagen
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return img_base64
            
        except Exception as e:
            print(f"❌ Error generando imagen QR: {e}")
            return None
    
    def generar_qr_ascii(self, factura):
        """Generar QR en ASCII para impresión térmica usando caracteres básicos"""
        if not QR_DISPONIBLE:
            return None
            
        try:
            info_qr = self.obtener_info_qr(factura)
            
            if not info_qr['valido']:
                return None
            
            # Crear QR muy pequeño para ASCII (versión mínima)
            qr = qrcode.QRCode(
                version=1,  # Versión más pequeña
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # Menor corrección
                box_size=1,
                border=1,
            )
            
            qr.add_data(info_qr['url'])
            qr.make(fit=True)
            
            # Obtener matriz del QR
            matrix = qr.get_matrix()
            
            # Convertir a ASCII usando SOLO caracteres básicos compatibles con CP437
            ascii_qr = []
            for row in matrix:
                ascii_row = ""
                for cell in row:
                    if cell:
                        ascii_row += "##"  # Usar ## en lugar de bloques Unicode
                    else:
                        ascii_row += "  "  # Espacios
                ascii_qr.append(ascii_row)
            
            return "\n".join(ascii_qr)
            
        except Exception as e:
            print(f"❌ Error generando QR ASCII: {e}")
            return None
        
    def validar_datos_qr(self, factura):
        """Validar que los datos de la factura sean correctos para QR"""
        errores = []
        
        # Validar CAE
        if not factura.cae:
            errores.append("Factura sin CAE")
        elif len(str(factura.cae)) < 14:
            errores.append("CAE con formato inválido")
        
        # Validar fecha
        if not factura.fecha:
            errores.append("Factura sin fecha")
        
        # Validar tipo de comprobante
        tipos_validos = ['01', '06', '11', '03', '08', '13']
        if str(factura.tipo_comprobante) not in tipos_validos:
            errores.append(f"Tipo de comprobante no válido: {factura.tipo_comprobante}")
        
        # Validar número
        if not factura.numero:
            errores.append("Factura sin número")
        
        # Validar importe
        if not factura.total or factura.total <= 0:
            errores.append("Importe inválido")
        
        # Validar punto de venta
        if not factura.punto_venta or factura.punto_venta <= 0:
            errores.append("Punto de venta inválido")
        
        return errores
    
    def verificar_qr_en_afip(self, factura):
        """Verificar QR en AFIP (implementación futura)"""
        # Esta función podría implementarse para hacer una consulta real a AFIP
        # y verificar que el QR sea válido
        return {
            'verificado': False,
            'mensaje': 'Verificación en AFIP no implementada'
        }

def crear_generador_qr(config=None):
    """Función factory para crear generador QR"""
    if config is None:
        # Configuración por defecto si no se proporciona
        class ConfigDefault:
            CUIT = '20203852100'
            PUNTO_VENTA = 3
        config = ConfigDefault()
    
    return GeneradorQR(config)

# Función de utilidad para verificar si el módulo QR está disponible
def verificar_disponibilidad_qr():
    """Verificar si el módulo QR está disponible"""
    return {
        'disponible': QR_DISPONIBLE,
        'modulos_necesarios': ['qrcode', 'PIL (Pillow)'] if not QR_DISPONIBLE else [],
        'comando_instalacion': 'pip install qrcode[pil] pillow' if not QR_DISPONIBLE else None
    }

# Función de prueba
def test_qr():
    """Función de prueba para el módulo QR"""
    print("🧪 Probando módulo QR...")
    
    disponibilidad = verificar_disponibilidad_qr()
    print(f"✅ Disponible: {disponibilidad['disponible']}")
    
    if not disponibilidad['disponible']:
        print(f"❌ Instalar: {disponibilidad['comando_instalacion']}")
        return False
    
    # Crear generador de prueba
    class ConfigPrueba:
        CUIT = '20203852100'
        PUNTO_VENTA = 3
    
    generador = crear_generador_qr(ConfigPrueba())
    
    # Crear factura de prueba
    class FacturaPrueba:
        def __init__(self):
            self.cae = '12345678901234'
            self.fecha = datetime.now()
            self.tipo_comprobante = '11'
            self.numero = '0003-00000001'
            self.punto_venta = 3
            self.total = 1000.50
            self.cliente = None
    
    factura_test = FacturaPrueba()
    
    # Probar generación de QR
    info_qr = generador.obtener_info_qr(factura_test)
    print(f"🔍 QR válido: {info_qr['valido']}")
    print(f"📄 Mensaje: {info_qr['mensaje']}")
    
    if info_qr['valido']:
        print(f"🌐 URL: {info_qr['url'][:100]}...")
    
    return info_qr['valido']

if __name__ == "__main__":
    test_qr()