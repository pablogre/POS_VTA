#!/usr/bin/env python3
"""
DIAGNÓSTICO AFIP - Archivo independiente
Ejecutar: python diagnostico_afip.py
"""

import os
import sys
import requests
import socket
import subprocess
from datetime import datetime, timedelta
from urllib.parse import urlparse
import ssl
import urllib3
from urllib3.util import ssl_
from requests.adapters import HTTPAdapter
from requests import Session

# Configuración SSL para AFIP
def configurar_ssl_afip():
    """Configuración SSL compatible para AFIP"""
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    def create_afip_ssl_context():
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
        
        return ctx
    
    ssl._create_default_https_context = create_afip_ssl_context
    ssl_.create_urllib3_context = create_afip_ssl_context
    urllib3.disable_warnings()

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
            
            kwargs['ssl_context'] = ctx
            return super().init_poolmanager(*args, **kwargs)
    
    session = Session()
    session.mount('https://', AFIPAdapter())
    session.verify = False
    return session

# Configuración
class ConfigAFIP:
    #CUIT = '20203852100'
    #PUNTO_VENTA = 3
    CUIT = '27333429433'
    PUNTO_VENTA = 4
    CERT_PATH = 'certificados/certificado.crt'
    KEY_PATH = 'certificados/private.key'
    USE_HOMOLOGACION = False  # PRODUCCIÓN
    
    @property
    def WSAA_URL(self):
        return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms' if self.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    
    @property
    def WSFEv1_URL(self):
        return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'

def buscar_openssl():
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
                    return ubicacion, result.stdout.strip()
        except:
            continue
    
    return None, None

def test_conectividad_tcp(host, port, timeout=10):
    """Test de conectividad TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        return False

def test_url_http(url, session):
    """Test HTTP de una URL"""
    try:
        response = session.get(url, timeout=15)
        content_type = response.headers.get('content-type', '').lower()
        content_preview = response.text[:200] if len(response.text) > 0 else 'Sin contenido'
        
        is_html = 'text/html' in content_type or '<html' in response.text.lower()
        should_be_xml = 'wsdl' in url.lower()
        
        return {
            'status_code': response.status_code,
            'ok': response.status_code == 200,
            'content_type': content_type,
            'is_html': is_html,
            'should_be_xml': should_be_xml,
            'problema_xml': is_html and should_be_xml,
            'content_preview': content_preview,
            'response_size': len(response.text)
        }
    except Exception as e:
        return {
            'error': str(e),
            'ok': False
        }

def verificar_certificados(config):
    """Verificar certificados AFIP"""
    print("\n🔍 VERIFICANDO CERTIFICADOS...")
    
    cert_exists = os.path.exists(config.CERT_PATH)
    key_exists = os.path.exists(config.KEY_PATH)
    
    print(f"   Certificado: {config.CERT_PATH}")
    print(f"   {'✅ Existe' if cert_exists else '❌ No existe'}")
    print(f"   Clave privada: {config.KEY_PATH}")
    print(f"   {'✅ Existe' if key_exists else '❌ No existe'}")
    
    if not cert_exists:
        print("   ❌ ERROR: Certificado no encontrado")
        return False
    
    if not key_exists:
        print("   ❌ ERROR: Clave privada no encontrada")
        return False
    
    try:
        # Verificar certificado
        with open(config.CERT_PATH, 'rb') as f:
            cert_data = f.read()
        
        try:
            from cryptography import x509
            try:
                cert = x509.load_pem_x509_certificate(cert_data)
            except:
                cert = x509.load_der_x509_certificate(cert_data)
            
            subject = cert.subject.rfc4514_string()
            not_before = cert.not_valid_before
            not_after = cert.not_valid_after
            
            now = datetime.utcnow()
            is_valid = not_before <= now <= not_after
            days_until_expiry = (not_after - now).days
            
            print(f"   📋 Subject: {subject}")
            print(f"   📅 Válido desde: {not_before}")
            print(f"   📅 Válido hasta: {not_after}")
            
            if is_valid:
                print(f"   ✅ Certificado válido - Expira en {days_until_expiry} días")
                if days_until_expiry < 30:
                    print(f"   ⚠️ ATENCIÓN: El certificado expira pronto!")
                return True
            else:
                print(f"   ❌ CERTIFICADO EXPIRADO O INVÁLIDO")
                return False
                
        except ImportError:
            print("   ⚠️ No se puede verificar fecha (falta cryptography)")
            return True
            
    except Exception as e:
        print(f"   ❌ Error verificando certificado: {e}")
        return False

def test_urls_afip(config):
    """Test de URLs de AFIP"""
    print("\n🌐 TESTEANDO URLs DE AFIP...")
    
    session = crear_session_afip()
    
    urls_test = [
        ('AFIP Home', 'https://www.afip.gob.ar'),
        ('WSAA', config.WSAA_URL),
        ('WSAA WSDL', config.WSAA_URL + '?wsdl'),
        ('WSFEv1', config.WSFEv1_URL.replace('?WSDL', '').replace('?wsdl', '')),
        ('WSFEv1 WSDL', config.WSFEv1_URL),
    ]
    
    resultados = {}
    problemas = []
    
    for nombre, url in urls_test:
        print(f"\n   🔍 Probando {nombre}:")
        print(f"      URL: {url}")
        
        # Test TCP
        parsed = urlparse(url)
        host = parsed.hostname
        port = 443 if parsed.scheme == 'https' else 80
        
        tcp_ok = test_conectividad_tcp(host, port)
        print(f"      TCP: {'✅ OK' if tcp_ok else '❌ FALLO'}")
        
        if not tcp_ok:
            problemas.append(f"{nombre}: Sin conectividad TCP a {host}:{port}")
            resultados[nombre] = {'tcp': False, 'http': False}
            continue
        
        # Test HTTP
        http_result = test_url_http(url, session)
        
        if http_result.get('ok'):
            if http_result.get('problema_xml'):
                print(f"      HTTP: ❌ Devuelve HTML cuando debería ser XML")
                print(f"      Contenido: {http_result.get('content_preview', '')[:100]}...")
                problemas.append(f"{nombre}: Devuelve HTML en lugar de XML")
            else:
                print(f"      HTTP: ✅ OK ({http_result.get('status_code')})")
                print(f"      Tipo: {http_result.get('content_type', 'desconocido')}")
        else:
            error = http_result.get('error', f"Status {http_result.get('status_code', 'desconocido')}")
            print(f"      HTTP: ❌ {error}")
            problemas.append(f"{nombre}: Error HTTP - {error}")
        
        resultados[nombre] = {
            'tcp': tcp_ok,
            'http': http_result.get('ok', False),
            'problema_xml': http_result.get('problema_xml', False)
        }
    
    return resultados, problemas

def test_wsaa_auth(config):
    """Test de autenticación WSAA"""
    print("\n🎫 TESTEANDO AUTENTICACIÓN WSAA...")
    
    try:
        # Verificar que tenemos los certificados
        if not os.path.exists(config.CERT_PATH) or not os.path.exists(config.KEY_PATH):
            print("   ❌ Certificados no encontrados")
            return False
        
        # Crear TRA simple
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
        
        print("   📝 TRA creado")
        
        # Intentar firmar con OpenSSL
        openssl_path, openssl_version = buscar_openssl()
        if not openssl_path:
            print("   ❌ OpenSSL no encontrado")
            return False
        
        print(f"   🔧 OpenSSL: {openssl_version}")
        
        # Test básico de zeep con WSAA
        try:
            from zeep import Client
            from zeep.transports import Transport
            
            session = crear_session_afip()
            transport = Transport(session=session, timeout=30)
            
            wsaa_url = config.WSAA_URL + '?wsdl'
            print(f"   🌐 Conectando con: {wsaa_url}")
            
            client = Client(wsaa_url, transport=transport)
            print("   ✅ Cliente SOAP creado correctamente")
            return True
            
        except Exception as e:
            error_str = str(e).lower()
            if 'invalid xml' in error_str or 'mismatch' in error_str:
                print("   ❌ WSAA devolviendo HTML en lugar de XML")
            else:
                print(f"   ❌ Error SOAP: {str(e)}")
            return False
        
    except Exception as e:
        print(f"   ❌ Error general: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    print("=" * 60)
    print("🔍 DIAGNÓSTICO COMPLETO DE AFIP")
    print("=" * 60)
    print(f"⏰ Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configurar SSL
    configurar_ssl_afip()
    config = ConfigAFIP()
    
    print(f"\n📋 CONFIGURACIÓN:")
    print(f"   CUIT: {config.CUIT}")
    print(f"   Ambiente: {'HOMOLOGACIÓN' if config.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    print(f"   WSAA: {config.WSAA_URL}")
    print(f"   WSFEv1: {config.WSFEv1_URL}")
    
    # 1. Verificar certificados
    cert_ok = verificar_certificados(config)
    
    # 2. Test de URLs
    urls_results, url_problems = test_urls_afip(config)
    
    # 3. Test de autenticación
    auth_ok = test_wsaa_auth(config)
    
    # RESUMEN FINAL
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    total_tests = 3
    tests_ok = sum([cert_ok, len(url_problems) == 0, auth_ok])
    
    print(f"✅ Tests pasados: {tests_ok}/{total_tests}")
    
    if cert_ok:
        print("✅ Certificados: OK")
    else:
        print("❌ Certificados: PROBLEMA")
    
    if len(url_problems) == 0:
        print("✅ URLs AFIP: OK")
    else:
        print("❌ URLs AFIP: PROBLEMAS")
        for problema in url_problems:
            print(f"   • {problema}")
    
    if auth_ok:
        print("✅ Conexión WSAA: OK")
    else:
        print("❌ Conexión WSAA: PROBLEMA")
    
    # DIAGNÓSTICO
    print("\n🎯 DIAGNÓSTICO:")
    
    if tests_ok == total_tests:
        print("✅ SISTEMA FUNCIONANDO - El problema puede ser temporal de AFIP")
        print("💡 Recomendación: Esperar 30-60 minutos y volver a probar")
    elif not cert_ok:
        print("❌ PROBLEMA DE CERTIFICADOS")
        print("💡 Recomendación: Verificar archivos de certificado")
    elif len(url_problems) > 0:
        if any('HTML' in p for p in url_problems):
            print("❌ AFIP DEVOLVIENDO HTML - Servicio en mantenimiento")
            print("💡 Recomendación: Esperar a que AFIP resuelva el problema")
        else:
            print("❌ PROBLEMA DE CONECTIVIDAD")
            print("💡 Recomendación: Verificar conexión a internet/firewall")
    else:
        print("❌ PROBLEMA DE CONFIGURACIÓN")
        print("💡 Recomendación: Verificar configuración AFIP")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Diagnóstico interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
    
    input("\n📋 Presiona Enter para salir...")