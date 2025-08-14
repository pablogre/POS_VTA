# ssl_fix_compatible.py - Versión compatible para todas las versiones de Python

import ssl
import urllib3
import os
from urllib3.util import ssl_
from requests.adapters import HTTPAdapter
from requests import Session

def configurar_ssl_afip():
    """Configuración SSL compatible para AFIP"""
    
    # Variables de entorno
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    def create_afip_ssl_context():
        """Crear contexto SSL para AFIP con compatibilidad máxima"""
        try:
            # Intentar con TLS_CLIENT (más nuevo)
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except AttributeError:
            # Fallback para versiones más antiguas
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
        
        # Configuraciones básicas
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Ciphers más permisivos
        try:
            ctx.set_ciphers('ALL:@SECLEVEL=0')
        except ssl.SSLError:
            try:
                ctx.set_ciphers('ALL:@SECLEVEL=1')
            except ssl.SSLError:
                ctx.set_ciphers('ALL')
        
        # Opciones adicionales si están disponibles
        ssl_options = []
        
        # Lista de opciones a intentar
        opciones_ssl = [
            'OP_LEGACY_SERVER_CONNECT',
            'OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION',
            'OP_DONT_INSERT_EMPTY_FRAGMENTS',
            'OP_ALL'
        ]
        
        for opcion in opciones_ssl:
            if hasattr(ssl, opcion):
                try:
                    ctx.options |= getattr(ssl, opcion)
                    ssl_options.append(opcion)
                except:
                    pass
        
        print(f"✅ SSL configurado con opciones: {ssl_options}")
        return ctx
    
    # Aplicar configuración global
    ssl._create_default_https_context = create_afip_ssl_context
    ssl_.create_urllib3_context = create_afip_ssl_context
    
    # Desactivar warnings
    urllib3.disable_warnings()
    
    print("✅ Configuración SSL para AFIP aplicada")

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
            if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
                ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT
            if hasattr(ssl, 'OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION'):
                ctx.options |= ssl.OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION
            if hasattr(ssl, 'OP_ALL'):
                ctx.options |= ssl.OP_ALL
            
            kwargs['ssl_context'] = ctx
            return super().init_poolmanager(*args, **kwargs)
    
    session = Session()
    session.mount('https://', AFIPAdapter())
    session.verify = False
    return session

# Test de conexión mejorado
def test_conexion_directa():
    """Test de conexión HTTP directa"""
    configurar_ssl_afip()
    
    urls = [
        ('WSAA Homologación', 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms'),
        ('WSFEv1 Homologación', 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx'),
        ('WSFEv1 Producción', 'https://servicios1.afip.gov.ar/wsfev1/service.asmx')
    ]
    
    session = crear_session_afip()
    
    for nombre, url in urls:
        try:
            print(f"🔍 Probando {nombre}:")
            print(f"   URL: {url}")
            
            response = session.get(url, timeout=15)
            print(f"   ✅ Status: {response.status_code}")
            
            if 'service' in response.text.lower() or 'wsdl' in response.text.lower():
                print(f"   ✅ Servicio web detectado")
            else:
                print(f"   ⚠️ Respuesta inusual (largo: {len(response.text)})")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:80]}...")
        print()

def test_zeep_wsdl():
    """Test de carga WSDL con zeep"""
    configurar_ssl_afip()
    
    try:
        from zeep import Client
        from zeep.transports import Transport
        
        print("🔍 Probando carga WSDL con zeep...")
        
        session = crear_session_afip()
        transport = Transport(session=session, timeout=90)
        
        # Test WSAA Homologación
        wsaa_url = 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
        print(f"📡 Cargando WSAA...")
        
        client = Client(wsaa_url, transport=transport)
        print("✅ WSAA cargado correctamente")
        
        operaciones = [op for op in dir(client.service) if not op.startswith('_')]
        print(f"   Operaciones: {operaciones}")
        
        # Test WSFEv1 Homologación  
        wsfe_url = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
        print(f"\n📡 Cargando WSFEv1...")
        
        client = Client(wsfe_url, transport=transport)
        print("✅ WSFEv1 cargado correctamente")
        
        operaciones = [op for op in dir(client.service) if not op.startswith('_')][:10]
        print(f"   Operaciones disponibles: {operaciones}")
        
        return True
        
    except ImportError:
        print("❌ Error: zeep no instalado")
        print("   Instalar con: pip install zeep")
        return False
    except Exception as e:
        print(f"❌ Error con zeep: {e}")
        return False

def verificar_sistema():
    """Verificar configuración del sistema"""
    import sys
    import platform
    
    print("=== INFORMACIÓN DEL SISTEMA ===")
    print(f"Python: {sys.version}")
    print(f"Plataforma: {platform.platform()}")
    
    try:
        print(f"OpenSSL: {ssl.OPENSSL_VERSION}")
    except:
        print("OpenSSL: No disponible")
    
    try:
        import requests
        print(f"Requests: {requests.__version__}")
    except:
        print("Requests: No disponible")
    
    try:
        import urllib3
        print(f"urllib3: {urllib3.__version__}")
    except:
        print("urllib3: No disponible")
    
    try:
        import zeep
        print(f"zeep: {zeep.__version__}")
    except:
        print("zeep: No instalado")
    
    print()

if __name__ == "__main__":
    print("🚀 TEST DE CONEXIÓN AFIP - VERSIÓN COMPATIBLE\n")
    
    verificar_sistema()
    
    print("=== TEST 1: Conexión HTTP ===")
    test_conexion_directa()
    
    print("=== TEST 2: Carga WSDL ===")  
    if test_zeep_wsdl():
        print("\n✅ CONEXIÓN CON AFIP EXITOSA")
        print("El sistema debería funcionar correctamente")
    else:
        print("\n❌ PROBLEMAS DE CONEXIÓN")
        print("Revisar configuración SSL o firewall")