#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solución definitiva SSL para AFIP PRODUCCIÓN
Ejecutar: python ssl_ultra_fix.py
"""

def crear_parche_ssl():
    """Crear parche SSL que funciona con AFIP"""
    
    parche_ssl = '''
# AGREGAR ESTAS LÍNEAS AL INICIO DE TU app.py (después de los imports):

import ssl
import urllib3
import os

# CONFIGURACIÓN SSL ULTRA-COMPATIBLE PARA AFIP
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

# Configurar SSL globalmente
ssl._create_default_https_context = ssl._create_unverified_context

# Configurar urllib3
urllib3.disable_warnings()

# Parche para requests/urllib3
def patch_ssl_for_afip():
    """Parche SSL específico para AFIP"""
    import ssl
    from urllib3.util import ssl_
    from urllib3.util.ssl_ import create_urllib3_context
    
    def create_legacy_context():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        return ctx
    
    ssl_.create_urllib3_context = create_legacy_context
    ssl.create_default_context = create_legacy_context

# Aplicar parche
patch_ssl_for_afip()
'''
    
    with open('ssl_patch.txt', 'w', encoding='utf-8') as f:
        f.write(parche_ssl)
    
    print("✅ Parche SSL creado en: ssl_patch.txt")

def crear_cliente_requests_custom():
    """Crear cliente requests personalizado para AFIP"""
    
    codigo_requests = '''
# REEMPLAZAR el método _create_zeep_transport en tu ARCAClient por este:

def _create_zeep_transport(self):
    """Crear transporte ZEEP con requests personalizado"""
    from zeep.transports import Transport
    import requests
    import ssl
    from requests.adapters import HTTPAdapter
    from urllib3.util.ssl_ import create_urllib3_context
    
    class AFIPHTTPSAdapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            # Configuración específica para AFIP
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
            kwargs['ssl_context'] = context
            return super().init_poolmanager(*args, **kwargs)
    
    # Crear sesión personalizada
    session = requests.Session()
    session.mount('https://', AFIPHTTPSAdapter())
    session.verify = False
    
    return Transport(session=session, timeout=120)
'''
    
    with open('transport_custom.txt', 'w', encoding='utf-8') as f:
        f.write(codigo_requests)
    
    print("✅ Código de transporte personalizado creado en: transport_custom.txt")

def crear_solucion_completa():
    """Crear app.py parcheado completo"""
    
    print("📝 Creando solución SSL completa...")
    
    try:
        # Leer app.py actual
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        # Hacer backup
        with open('app_original.py.backup', 'w', encoding='utf-8') as f:
            f.write(app_content)
        
        print("💾 Backup creado: app_original.py.backup")
        
        # Buscar los imports
        import_index = app_content.find('from flask import')
        
        if import_index == -1:
            print("❌ No se encontraron los imports de Flask")
            return False
        
        # Agregar parche SSL después de los imports
        ssl_patch = '''
# PARCHE SSL PARA AFIP - SOLUCIÓN DEFINITIVA
import ssl
import urllib3
import os

# Configuración SSL ultra-compatible
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''

# Desactivar verificación SSL
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings()

def patch_ssl_for_afip():
    """Parche SSL específico para servidores AFIP legacy"""
    import ssl
    from urllib3.util import ssl_
    
    def create_afip_context():
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers('ALL:@SECLEVEL=0')
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        return ctx
    
    ssl_.create_urllib3_context = create_afip_context
    ssl.create_default_context = create_afip_context

# Aplicar parche SSL
patch_ssl_for_afip()

'''
        
        # Encontrar el final de los imports (primera línea que no empieza con import/from)
        lines = app_content.split('\n')
        insert_index = 0
        
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('import ', 'from ', '#')):
                insert_index = i
                break
        
        # Insertar el parche SSL
        lines.insert(insert_index, ssl_patch)
        
        # Buscar y reemplazar el método _create_zeep_transport
        new_transport_method = '''    def _create_zeep_transport(self):
        """Crear transporte ZEEP ultra-compatible con AFIP"""
        from zeep.transports import Transport
        import requests
        import ssl
        from requests.adapters import HTTPAdapter
        
        class AFIPHTTPSAdapter(HTTPAdapter):
            def init_poolmanager(self, *args, **kwargs):
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                context.set_ciphers('ALL:@SECLEVEL=0')
                context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
                kwargs['ssl_context'] = context
                return super().init_poolmanager(*args, **kwargs)
        
        session = requests.Session()
        session.mount('https://', AFIPHTTPSAdapter())
        session.verify = False
        
        return Transport(session=session, timeout=120)'''
        
        # Reemplazar el método existente
        content_str = '\n'.join(lines)
        
        # Buscar el método _create_zeep_transport
        start_marker = 'def _create_zeep_transport(self):'
        start_index = content_str.find(start_marker)
        
        if start_index != -1:
            # Encontrar el final del método (próximo def o final de clase)
            method_start = start_index
            lines_from_method = content_str[start_index:].split('\n')
            method_lines = [lines_from_method[0]]  # Primera línea del método
            
            for line in lines_from_method[1:]:
                if line.strip() and not line.startswith('    ') and not line.startswith('\t'):
                    break
                method_lines.append(line)
            
            old_method = '\n'.join(method_lines)
            content_str = content_str.replace(old_method, new_transport_method)
        
        # Guardar archivo modificado
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content_str)
        
        print("✅ app.py parcheado exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error parcheando app.py: {e}")
        return False

def main():
    print("🔧 SOLUCIÓN SSL DEFINITIVA PARA AFIP PRODUCCIÓN")
    print("=" * 50)
    print("Esta solución modifica tu app.py para que funcione con AFIP")
    
    continuar = input("\n¿Aplicar parche SSL definitivo? (S/n): ").strip().lower()
    if continuar in ['n', 'no']:
        print("Operación cancelada")
        return
    
    if crear_solucion_completa():
        print("\n🎉 ¡SOLUCIÓN SSL APLICADA!")
        print("\n🚀 EJECUTA AHORA:")
        print("   python app.py")
        print("   Prueba una venta en PRODUCCIÓN")
        
        print("\n💾 BACKUP:")
        print("   Original guardado en: app_original.py.backup")
        
        print("\n🔄 PARA RESTAURAR:")
        print("   copy app_original.py.backup app.py")
    else:
        print("\n❌ No se pudo aplicar el parche")
        print("💡 Prueba aplicar manualmente los cambios")

if __name__ == "__main__":
    main()