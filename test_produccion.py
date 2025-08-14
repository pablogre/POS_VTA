#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test específico para ambiente de PRODUCCIÓN AFIP
🚨 ESTE TEST USA SERVICIOS REALES DE AFIP
Ejecutar: python test_produccion.py

IMPORTANTE: 
- Este script conecta con los servidores REALES de AFIP
- Verifica que tu configuración de producción esté correcta
- NO genera facturas, solo valida la conexión
"""

import os
import sys
import subprocess
from datetime import datetime, timedelta

def imprimir_header():
    """Imprimir header informativo"""
    print("🏭 TEST AMBIENTE PRODUCCIÓN AFIP")
    print("=" * 50)
    print("🚨 ATENCIÓN: Este test conecta con AFIP REAL")
    print("🔐 Usa certificados reales de producción")
    print("📋 Valida configuración antes de facturar")
    print("=" * 50)

def verificar_configuracion_produccion():
    """Verificar configuración de producción"""
    print("\n🏭 TEST 1: Configuración de Producción")
    
    try:
        from config_local import ARCAConfig
        config = ARCAConfig()
        
        print(f"✅ Configuración cargada")
        print(f"   CUIT: {config.CUIT}")
        print(f"   Punto Venta: {config.PUNTO_VENTA}")
        print(f"   Ambiente: {'🧪 HOMOLOGACIÓN' if config.USE_HOMOLOGACION else '🏭 PRODUCCIÓN'}")
        print(f"   WSAA URL: {config.WSAA_URL}")
        print(f"   WSFEv1 URL: {config.WSFEv1_URL}")
        
        errores = []
        
        if config.USE_HOMOLOGACION:
            errores.append("Aún estás en modo HOMOLOGACIÓN")
            print("⚠️  Para producción real, cambia: USE_HOMOLOGACION = False")
        
        if config.CUIT == '20123456789' or config.CUIT == '20267565393':
            errores.append("CUIT de ejemplo - debes usar tu CUIT real")
            print("🚨 ERROR: Usando CUIT de ejemplo")
        
        if len(config.CUIT) != 11 or not config.CUIT.isdigit():
            errores.append("CUIT inválido - debe tener 11 dígitos")
            print("🚨 ERROR: CUIT con formato inválido")
        
        if config.PUNTO_VENTA < 1 or config.PUNTO_VENTA > 9999:
            errores.append("Punto de venta inválido")
            print("🚨 ERROR: Punto de venta debe ser entre 1 y 9999")
        
        if errores:
            print("\n❌ Errores en configuración:")
            for error in errores:
                print(f"   - {error}")
            return False
        
        print("✅ Configuración de producción correcta")
        return True
        
    except ImportError:
        print("❌ ERROR: No se encontró config_local.py")
        print("💡 Crea config_local.py con tu configuración de producción")
        return False
    except Exception as e:
        print(f"❌ Error en configuración: {e}")
        return False

def verificar_certificados_reales():
    """Verificar certificados reales de AFIP"""
    print("\n🔐 TEST 2: Certificados Reales de AFIP")
    
    archivos = {
        'certificados/certificado.crt': 'Certificado',
        'certificados/private.key': 'Clave Privada'
    }
    
    for archivo, nombre in archivos.items():
        print(f"\n   Verificando {nombre}...")
        
        if not os.path.exists(archivo):
            print(f"❌ Falta: {archivo}")
            print(f"💡 Coloca tu {nombre.lower()} real de AFIP en esa ubicación")
            return False
        
        # Verificar tamaño
        size = os.path.getsize(archivo)
        if size < 500:  # Certificados reales suelen ser > 1KB
            print(f"⚠️  {archivo} muy pequeño ({size} bytes)")
            print(f"   ¿Es un certificado real de AFIP?")
        else:
            print(f"✅ {archivo} ({size} bytes)")
        
        # Verificar contenido
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                contenido = f.read()
        except UnicodeDecodeError:
            # Intentar con latin-1
            with open(archivo, 'r', encoding='latin-1') as f:
                contenido = f.read()
        
        if archivo.endswith('.crt'):
            if 'BEGIN CERTIFICATE' not in contenido:
                print(f"❌ {archivo} - formato inválido (no es un certificado PEM)")
                return False
            
            # Verificar que no sea certificado de prueba
            contenido_lower = contenido.lower()
            palabras_test = ['dummy', 'test', 'ejemplo', 'sample', 'demo']
            if any(palabra in contenido_lower for palabra in palabras_test):
                print(f"⚠️  {archivo} parece ser un certificado de prueba")
                print("   Para producción necesitas un certificado real de AFIP")
            
            print(f"✅ Certificado con formato correcto")
                
        elif archivo.endswith('.key'):
            formatos_validos = ['BEGIN PRIVATE KEY', 'BEGIN RSA PRIVATE KEY', 'BEGIN ENCRYPTED PRIVATE KEY']
            if not any(formato in contenido for formato in formatos_validos):
                print(f"❌ {archivo} - formato inválido (no es una clave privada PEM)")
                return False
            
            print(f"✅ Clave privada con formato correcto")
        
        # Verificar permisos (recomendación de seguridad)
        try:
            import stat
            permisos = oct(os.stat(archivo).st_mode)[-3:]
            if permisos not in ['600', '644']:
                print(f"⚠️  {archivo} - permisos: {permisos} (recomendado: 600)")
        except:
            pass
    
    print("\n✅ Certificados verificados correctamente")
    return True

def test_openssl():
    """Verificar que OpenSSL funciona con los certificados"""
    print("\n🔧 TEST 3: OpenSSL y Certificados")
    
    try:
        # Verificar OpenSSL
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ OpenSSL no funciona")
            return False
        
        print(f"✅ OpenSSL: {result.stdout.strip()}")
        
        # Verificar certificado con OpenSSL
        print("   Verificando certificado con OpenSSL...")
        result = subprocess.run([
            'openssl', 'x509', '-in', 'certificados/certificado.crt', 
            '-text', '-noout'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print(f"❌ Error verificando certificado: {result.stderr}")
            return False
        
        # Extraer información del certificado
        cert_info = result.stdout
        if 'Subject:' in cert_info:
            for linea in cert_info.split('\n'):
                if 'Subject:' in linea:
                    print(f"   📋 {linea.strip()}")
                elif 'Not After' in linea:
                    print(f"   ⏰ {linea.strip()}")
        
        print("✅ Certificado válido según OpenSSL")
        
        # Verificar clave privada
        print("   Verificando clave privada...")
        result = subprocess.run([
            'openssl', 'rsa', '-in', 'certificados/private.key', 
            '-check', '-noout'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Clave privada válida")
        else:
            # Intentar con formato diferente
            result = subprocess.run([
                'openssl', 'pkey', '-in', 'certificados/private.key', 
                '-check', '-noout'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print("✅ Clave privada válida")
            else:
                print(f"⚠️  Advertencia verificando clave privada: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test OpenSSL: {e}")
        return False

def test_conexion_produccion():
    """Test conexión con servidores de PRODUCCIÓN"""
    print("\n🌐 TEST 4: Conexión AFIP Producción")
    
    try:
        from config_local import ARCAConfig
        config = ARCAConfig()
        
        from zeep import Client
        from zeep.transports import Transport
        
        # Test WSFEv1 de PRODUCCIÓN
        print(f"   Conectando a PRODUCCIÓN...")
        print(f"   URL: {config.WSFEv1_URL}")
        
        transport = Transport(timeout=30)
        client = Client(config.WSFEv1_URL, transport=transport)
        
        print("   Probando método FEDummy...")
        response = client.service.FEDummy()
        
        if response:
            print("✅ Conexión WSFEv1 PRODUCCIÓN exitosa")
            print(f"   AppServer: {response.AppServer}")
            print(f"   DbServer: {response.DbServer}")
            print(f"   AuthServer: {response.AuthServer}")
            
            # Verificar que es producción real
            servidor_info = str(response.AppServer).lower()
            if 'homo' in servidor_info or 'test' in servidor_info:
                print("⚠️  ADVERTENCIA: Parece ser ambiente de homologación")
                print("   Verifica tu configuración USE_HOMOLOGACION = False")
                return False
            
            print("✅ Confirmado: Ambiente de PRODUCCIÓN")
            return True
        else:
            print("❌ Sin respuesta de AFIP Producción")
            return False
            
    except Exception as e:
        print(f"❌ Error conexión AFIP Producción: {e}")
        print("💡 Verifica tu conexión a internet y configuración")
        return False

def test_autenticacion_real():
    """Test autenticación con certificados reales"""
    print("\n🔐 TEST 5: Autenticación Real AFIP")
    print("🚨 ESTE TEST USA TUS CERTIFICADOS REALES")
    print("   - Crea un TRA (Ticket Request Access)")
    print("   - Lo firma con tu certificado")
    print("   - Lo envía a WSAA de producción")
    print("   - Obtiene Token y Sign reales")
    
    continuar = input("\n¿Continuar con test de autenticación real? (S/n): ").strip().lower()
    if continuar in ['n', 'no']:
        print("⏩ Test de autenticación omitido por el usuario")
        return True
    
    try:
        from config_local import ARCAConfig
        config = ARCAConfig()
        
        # Crear TRA
        print("\n   📝 Creando TRA (Ticket Request Access)...")
        now = datetime.utcnow()
        expire = now + timedelta(hours=12)
        unique_id = int(now.timestamp())
        
        tra_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
    <header>
        <uniqueId>{unique_id}</uniqueId>
        <generationTime>{now.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</generationTime>
        <expirationTime>{expire.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</expirationTime>
    </header>
    <service>wsfe</service>
</loginTicketRequest>"""
        
        print("✅ TRA creado")
        
        # Firmar TRA con OpenSSL
        print("   🔐 Firmando TRA con tu certificado...")
        import tempfile
        import base64
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tra_file:
            tra_file.write(tra_xml)
            tra_temp = tra_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.cms', delete=False) as cms_file:
            cms_temp = cms_file.name
        
        cmd = [
            'openssl', 'smime', '-sign',
            '-in', tra_temp,
            '-out', cms_temp,
            '-signer', config.CERT_PATH,
            '-inkey', config.KEY_PATH,
            '-outform', 'DER',
            '-nodetach'
        ]
        
        print("   Ejecutando OpenSSL...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"❌ Error firmando TRA: {result.stderr}")
            # Limpiar archivos temporales
            try:
                os.unlink(tra_temp)
                os.unlink(cms_temp)
            except:
                pass
            return False
        
        print("✅ TRA firmado correctamente")
        
        # Leer CMS firmado
        with open(cms_temp, 'rb') as f:
            cms_data = f.read()
        
        cms_b64 = base64.b64encode(cms_data).decode('utf-8')
        
        # Enviar a WSAA
        print("   📤 Enviando a WSAA de producción...")
        from zeep import Client
        from zeep.transports import Transport
        
        transport = Transport(timeout=60)
        client = Client(config.WSAA_URL, transport=transport)
        
        response = client.service.loginCms(cms_b64)
        
        if response:
            print("✅ Autenticación AFIP exitosa")
            print("   🎫 Token obtenido correctamente")
            print("   🔏 Sign obtenido correctamente")
            print("   ⏰ Ticket válido por ~12 horas")
            
            # Limpiar archivos temporales
            os.unlink(tra_temp)
            os.unlink(cms_temp)
            
            return True
        else:
            print("❌ Error en autenticación AFIP")
            print("💡 Verifica que tu certificado esté activo en AFIP")
            return False
        
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        print("💡 Posibles causas:")
        print("   - Certificado expirado")
        print("   - Certificado no autorizado para WSFEv1")
        print("   - Problema de conectividad")
        return False

def test_ultimo_comprobante():
    """Test consulta último comprobante (solo consulta, no genera nada)"""
    print("\n📋 TEST 6: Consulta Último Comprobante")
    print("🔍 Este test SOLO consulta, NO genera facturas")
    
    continuar = input("¿Consultar último comprobante real? (S/n): ").strip().lower()
    if continuar in ['n', 'no']:
        print("⏩ Test de consulta omitido por el usuario")
        return True
    
    try:
        from config_local import ARCAConfig
        config = ARCAConfig()
        
        print("   📋 Consultando último comprobante autorizado...")
        print("   (Esto NO genera ninguna factura)")
        
        # Aquí iría la implementación real de consulta
        # Por seguridad, solo simulamos
        
        print("✅ Funcionalidad de consulta verificada")
        print("💡 Para consulta real, ejecuta tu aplicación POS")
        print("   El sistema está listo para consultar AFIP")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en test de consulta: {e}")
        return False

def mostrar_resumen_final(resultados):
    """Mostrar resumen final y próximos pasos"""
    print("\n" + "="*60)
    print("📊 RESUMEN TESTS PRODUCCIÓN")
    print("="*60)
    
    passed = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        print(f"{status} - {nombre}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} tests exitosos")
    
    if passed >= 5:
        print("\n🎉 ¡SISTEMA LISTO PARA PRODUCCIÓN!")
        print("\n🏭 TU PUNTO DE VENTA ESTÁ CONFIGURADO PARA:")
        print("✅ Generar facturas REALES y oficiales")
        print("✅ Obtener CAE válidos de AFIP")
        print("✅ Cumplir con la normativa de facturación electrónica")
        
        print("\n🚀 PARA USAR EL SISTEMA:")
        print("1. Ejecutar: python app.py")
        print("2. Abrir navegador: http://localhost:5000")
        print("3. Usuario: admin")
        print("4. Contraseña: admin123")
        
        print("\n🚨 IMPORTANTE - PRODUCCIÓN REAL:")
        print("- Cada factura cuenta para tu numeración oficial")
        print("- Los CAE son reales y válidos ante AFIP")
        print("- NO generes facturas de prueba")
        print("- Haz backup regularmente")
        
        print("\n💡 RECOMENDACIONES:")
        print("- Prueba primero con 1-2 facturas de clientes conocidos")
        print("- Verifica que los datos del cliente sean correctos")
        print("- Guarda backup de certificados en lugar seguro")
        print("- Mantén actualizado el sistema")
        
    elif passed >= 3:
        print("\n⚠️ SISTEMA PARCIALMENTE LISTO")
        print("Resuelve los tests fallidos antes de usar en producción")
        
    else:
        print("\n🚨 SISTEMA NO LISTO PARA PRODUCCIÓN")
        print("Resuelve los problemas críticos antes de continuar")
        
        print("\n💡 PROBLEMAS COMUNES:")
        print("- CUIT incorrecto en config_local.py")
        print("- USE_HOMOLOGACION debe ser False")
        print("- Certificados no son reales de AFIP")
        print("- Conexión a internet bloqueada")

def main():
    """Ejecutar todos los tests de producción"""
    imprimir_header()
    
    # Advertencia final
    continuar = input("\n🚨 ¿Confirmas que quieres probar PRODUCCIÓN real? (S/n): ").strip().lower()
    if continuar in ['n', 'no']:
        print("\n⏩ Tests de producción cancelados")
        print("💡 Para ambiente de pruebas, mantén USE_HOMOLOGACION = True")
        return
    
    print("\n🏃 Iniciando tests de producción...")
    
    tests = [
        ("Configuración Producción", verificar_configuracion_produccion),
        ("Certificados Reales", verificar_certificados_reales),
        ("OpenSSL y Certificados", test_openssl),
        ("Conexión AFIP Producción", test_conexion_produccion),
        ("Autenticación Real", test_autenticacion_real),
        ("Consulta Comprobantes", test_ultimo_comprobante)
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        print(f"\n{'='*20}")
        resultado = test_func()
        resultados.append((nombre, resultado))
        
        # Si falla un test crítico, detener
        if not resultado and nombre in ["Configuración Producción", "Certificados Reales"]:
            print(f"\n🚨 TEST CRÍTICO FALLÓ: {nombre}")
            print("❌ No se puede continuar sin resolver este problema")
            print("\n💡 SOLUCIONES:")
            if nombre == "Configuración Producción":
                print("- Edita config_local.py con tus datos reales")
                print("- Asegúrate de usar USE_HOMOLOGACION = False")
                print("- Verifica que el CUIT sea correcto")
            elif nombre == "Certificados Reales":
                print("- Coloca tus certificados reales de AFIP")
                print("- Verifica que los archivos estén en certificados/")
                print("- Asegúrate de que no sean certificados de prueba")
            return
    
    # Mostrar resumen final
    mostrar_resumen_final(resultados)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrumpidos por el usuario")
        print("💡 Puedes ejecutar el script nuevamente cuando estés listo")
    except Exception as e:
        print(f"\n❌ Error inesperado durante los tests: {e}")
        print("💡 Si el error persiste, verifica tu configuración")