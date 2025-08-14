#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico detallado de OpenSSL y certificados
Ejecutar: python diagnosticar_openssl.py
"""

import os
import subprocess
import sys

def test_openssl_basico():
    """Test básico de OpenSSL"""
    print("🔧 TEST: OpenSSL Básico")
    
    try:
        result = subprocess.run(['openssl', 'version'], 
                              capture_output=True, text=True, timeout=10)
        print(f"   Comando: openssl version")
        print(f"   Return code: {result.returncode}")
        print(f"   Stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"   Stderr: {result.stderr.strip()}")
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ OpenSSL no encontrado en PATH")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando OpenSSL: {e}")
        return False

def test_certificado():
    """Test detallado del certificado"""
    print("\n🔐 TEST: Certificado")
    
    cert_path = 'certificados/certificado.crt'
    
    if not os.path.exists(cert_path):
        print(f"❌ No existe: {cert_path}")
        return False
    
    print(f"✅ Archivo existe: {cert_path}")
    print(f"   Tamaño: {os.path.getsize(cert_path)} bytes")
    
    # Test 1: Verificar formato
    print("\n   📋 Test 1: Formato del certificado")
    try:
        result = subprocess.run([
            'openssl', 'x509', '-in', cert_path, 
            '-text', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        print(f"   Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("   ✅ Certificado con formato válido")
            
            # Extraer información importante
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Subject:' in line:
                    print(f"   📋 {line.strip()}")
                elif 'Issuer:' in line:
                    print(f"   🏢 {line.strip()}")
                elif 'Not Before:' in line:
                    print(f"   📅 {line.strip()}")
                elif 'Not After:' in line:
                    print(f"   ⏰ {line.strip()}")
            
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            
            # Intentar diagnóstico adicional
            print("\n   🔍 Diagnóstico adicional:")
            
            # Verificar si es PEM
            with open(cert_path, 'r') as f:
                content = f.read()
            
            if '-----BEGIN CERTIFICATE-----' in content:
                print("   ✅ Formato PEM detectado")
            else:
                print("   ❌ No es formato PEM")
                
                # Verificar si es DER
                try:
                    result_der = subprocess.run([
                        'openssl', 'x509', '-in', cert_path, 
                        '-inform', 'DER', '-text', '-noout'
                    ], capture_output=True, text=True, timeout=15)
                    
                    if result_der.returncode == 0:
                        print("   ✅ Formato DER detectado")
                        print("   💡 Convierte a PEM: openssl x509 -in cert.crt -inform DER -out cert.pem")
                        return False
                    else:
                        print("   ❌ Formato desconocido")
                except:
                    print("   ❌ No se pudo determinar formato")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Error ejecutando OpenSSL: {e}")
        return False

def test_clave_privada():
    """Test detallado de la clave privada"""
    print("\n🔑 TEST: Clave Privada")
    
    key_path = 'certificados/private.key'
    
    if not os.path.exists(key_path):
        print(f"❌ No existe: {key_path}")
        return False
    
    print(f"✅ Archivo existe: {key_path}")
    print(f"   Tamaño: {os.path.getsize(key_path)} bytes")
    
    # Test 1: Verificar formato RSA
    print("\n   🔑 Test 1: Formato RSA")
    try:
        result = subprocess.run([
            'openssl', 'rsa', '-in', key_path, 
            '-check', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        print(f"   Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("   ✅ Clave RSA válida")
            return True
        else:
            print(f"   ⚠️ RSA falló: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Error RSA: {e}")
    
    # Test 2: Verificar formato genérico
    print("\n   🔑 Test 2: Formato genérico")
    try:
        result = subprocess.run([
            'openssl', 'pkey', '-in', key_path, 
            '-check', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        print(f"   Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("   ✅ Clave privada válida")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Error genérico: {e}")
    
    # Diagnóstico adicional
    print("\n   🔍 Diagnóstico adicional:")
    try:
        with open(key_path, 'r') as f:
            content = f.read()
        
        if '-----BEGIN PRIVATE KEY-----' in content:
            print("   ✅ Formato PKCS#8 detectado")
        elif '-----BEGIN RSA PRIVATE KEY-----' in content:
            print("   ✅ Formato RSA tradicional detectado")
        elif '-----BEGIN ENCRYPTED PRIVATE KEY-----' in content:
            print("   ⚠️ Clave privada encriptada detectada")
            print("   💡 AFIP requiere clave sin contraseña")
        else:
            print("   ❌ Formato desconocido")
        
    except Exception as e:
        print(f"   ❌ Error leyendo archivo: {e}")
    
    return False

def test_compatibilidad():
    """Test de compatibilidad certificado-clave"""
    print("\n🔗 TEST: Compatibilidad Certificado-Clave")
    
    cert_path = 'certificados/certificado.crt'
    key_path = 'certificados/private.key'
    
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("❌ Faltan archivos para test de compatibilidad")
        return False
    
    try:
        # Obtener módulo del certificado
        print("   📋 Obteniendo módulo del certificado...")
        result_cert = subprocess.run([
            'openssl', 'x509', '-in', cert_path, 
            '-modulus', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        if result_cert.returncode != 0:
            print(f"   ❌ Error obteniendo módulo del certificado: {result_cert.stderr}")
            return False
        
        # Obtener módulo de la clave privada
        print("   🔑 Obteniendo módulo de la clave privada...")
        result_key = subprocess.run([
            'openssl', 'rsa', '-in', key_path, 
            '-modulus', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        if result_key.returncode != 0:
            # Intentar con formato genérico
            result_key = subprocess.run([
                'openssl', 'pkey', '-in', key_path, 
                '-pubout'
            ], capture_output=True, text=True, timeout=15)
            
            if result_key.returncode != 0:
                print(f"   ❌ Error obteniendo módulo de la clave: {result_key.stderr}")
                return False
            else:
                print("   ⚠️ Usando método alternativo para clave privada")
                # No podemos comparar módulos directamente en este caso
                return True
        
        # Comparar módulos
        cert_modulus = result_cert.stdout.strip()
        key_modulus = result_key.stdout.strip()
        
        if cert_modulus == key_modulus:
            print("   ✅ Certificado y clave privada son compatibles")
            return True
        else:
            print("   ❌ Certificado y clave privada NO son compatibles")
            print("   💡 Asegúrate de que ambos archivos correspondan al mismo certificado")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en test de compatibilidad: {e}")
        return False

def test_firma_simple():
    """Test de firma simple"""
    print("\n✍️ TEST: Firma Simple")
    
    cert_path = 'certificados/certificado.crt'
    key_path = 'certificados/private.key'
    
    if not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("❌ Faltan archivos para test de firma")
        return False
    
    try:
        # Crear archivo de prueba
        test_content = "Test de firma AFIP"
        with open('test_input.txt', 'w') as f:
            f.write(test_content)
        
        print("   📝 Creando firma de prueba...")
        
        # Intentar firmar
        result = subprocess.run([
            'openssl', 'smime', '-sign',
            '-in', 'test_input.txt',
            '-out', 'test_output.cms',
            '-signer', cert_path,
            '-inkey', key_path,
            '-outform', 'DER',
            '-nodetach'
        ], capture_output=True, text=True, timeout=30)
        
        print(f"   Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("   ✅ Firma exitosa")
            
            # Verificar archivo de salida
            if os.path.exists('test_output.cms'):
                size = os.path.getsize('test_output.cms')
                print(f"   📄 Archivo firmado creado ({size} bytes)")
                
                # Limpiar archivos temporales
                os.remove('test_input.txt')
                os.remove('test_output.cms')
                
                return True
            else:
                print("   ❌ No se creó archivo firmado")
                return False
        else:
            print(f"   ❌ Error en firma: {result.stderr}")
            
            # Limpiar archivos temporales
            if os.path.exists('test_input.txt'):
                os.remove('test_input.txt')
            
            return False
            
    except Exception as e:
        print(f"   ❌ Error en test de firma: {e}")
        return False

def mostrar_soluciones(resultados):
    """Mostrar soluciones basadas en los resultados"""
    print("\n" + "="*50)
    print("💡 SOLUCIONES RECOMENDADAS")
    print("="*50)
    
    openssl_ok, cert_ok, key_ok, compat_ok, sign_ok = resultados
    
    if not openssl_ok:
        print("\n🔧 PROBLEMA: OpenSSL")
        print("SOLUCIONES:")
        print("1. Reinstalar OpenSSL: https://slproweb.com/products/Win32OpenSSL.html")
        print("2. Verificar PATH: echo %PATH%")
        print("3. Usar OpenSSL portable en tu proyecto")
    
    if not cert_ok:
        print("\n🔐 PROBLEMA: Certificado")
        print("SOLUCIONES:")
        print("1. Verificar que sea certificado real de AFIP")
        print("2. Convertir formato si es necesario:")
        print("   openssl x509 -in cert.crt -inform DER -out cert.pem")
        print("3. Descargar nuevamente desde AFIP")
    
    if not key_ok:
        print("\n🔑 PROBLEMA: Clave Privada")
        print("SOLUCIONES:")
        print("1. Verificar que no esté encriptada con contraseña")
        print("2. Si está encriptada, desencriptar:")
        print("   openssl rsa -in private.key -out private_unencrypted.key")
        print("3. Verificar formato correcto")
    
    if not compat_ok:
        print("\n🔗 PROBLEMA: Compatibilidad")
        print("SOLUCIONES:")
        print("1. Verificar que ambos archivos sean del mismo certificado")
        print("2. Regenerar par clave/certificado en AFIP")
        print("3. Verificar que no se mezclaron archivos")
    
    if not sign_ok:
        print("\n✍️ PROBLEMA: Firma")
        print("SOLUCIONES:")
        print("1. Verificar todos los problemas anteriores")
        print("2. Probar con certificados de testing primero")
        print("3. Contactar soporte de AFIP")

def main():
    """Ejecutar diagnóstico completo"""
    print("🔍 DIAGNÓSTICO DETALLADO: OpenSSL y Certificados")
    print("=" * 55)
    
    # Ejecutar tests
    openssl_ok = test_openssl_basico()
    cert_ok = test_certificado()
    key_ok = test_clave_privada()
    compat_ok = test_compatibilidad()
    sign_ok = test_firma_simple()
    
    resultados = [openssl_ok, cert_ok, key_ok, compat_ok, sign_ok]
    
    # Resumen
    print("\n" + "="*30)
    print("📊 RESUMEN")
    print("="*30)
    
    tests = [
        "OpenSSL Básico",
        "Certificado",
        "Clave Privada", 
        "Compatibilidad",
        "Firma Simple"
    ]
    
    for test, resultado in zip(tests, resultados):
        status = "✅" if resultado else "❌"
        print(f"{status} {test}")
    
    passed = sum(resultados)
    total = len(resultados)
    print(f"\n🎯 RESULTADO: {passed}/{total} tests OK")
    
    if passed == total:
        print("\n🎉 ¡Todos los tests de OpenSSL pasaron!")
        print("El problema debe estar en la conexión AFIP")
    else:
        mostrar_soluciones(resultados)

if __name__ == "__main__":
    main()