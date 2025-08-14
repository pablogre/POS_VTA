#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico de certificados AFIP
Ejecutar: python diagnosticar_certificados.py
"""

import subprocess
import os

def verificar_certificado():
    """Verificar certificado"""
    print("🔐 VERIFICANDO CERTIFICADO")
    print("=" * 30)
    
    cert_path = 'certificados/certificado.crt'
    
    if not os.path.exists(cert_path):
        print(f"❌ No existe: {cert_path}")
        return False
    
    try:
        # Información del certificado
        print("📋 Información del certificado:")
        result = subprocess.run([
            './openssl.exe', 'x509', '-in', cert_path, 
            '-subject', '-issuer', '-dates', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'subject=' in line:
                    print(f"   👤 {line}")
                elif 'issuer=' in line:
                    print(f"   🏢 {line}")
                elif 'notBefore=' in line:
                    print(f"   📅 Válido desde: {line.split('=')[1]}")
                elif 'notAfter=' in line:
                    print(f"   ⏰ Válido hasta: {line.split('=')[1]}")
        
        # Obtener módulo del certificado
        print("\n🔢 Obteniendo huella del certificado...")
        result = subprocess.run([
            './openssl.exe', 'x509', '-in', cert_path, 
            '-modulus', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            cert_modulus = result.stdout.strip()
            print(f"   📊 Módulo cert: {cert_modulus[:50]}...")
            return cert_modulus
        else:
            print(f"   ❌ Error obteniendo módulo: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error verificando certificado: {e}")
        return None

def verificar_clave_privada():
    """Verificar clave privada"""
    print("\n🔑 VERIFICANDO CLAVE PRIVADA")
    print("=" * 30)
    
    key_path = 'certificados/private.key'
    
    if not os.path.exists(key_path):
        print(f"❌ No existe: {key_path}")
        return False
    
    try:
        # Verificar formato de la clave
        print("🔍 Verificando formato de clave privada...")
        
        # Intentar con RSA
        result = subprocess.run([
            './openssl.exe', 'rsa', '-in', key_path, 
            '-check', '-noout'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("   ✅ Clave RSA válida")
            key_type = "rsa"
        else:
            # Intentar con formato genérico
            result = subprocess.run([
                './openssl.exe', 'pkey', '-in', key_path, 
                '-check', '-noout'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                print("   ✅ Clave privada válida (formato genérico)")
                key_type = "pkey"
            else:
                print(f"   ❌ Clave inválida: {result.stderr}")
                return None
        
        # Obtener módulo de la clave privada
        print("🔢 Obteniendo huella de la clave privada...")
        
        if key_type == "rsa":
            result = subprocess.run([
                './openssl.exe', 'rsa', '-in', key_path, 
                '-modulus', '-noout'
            ], capture_output=True, text=True, timeout=15)
        else:
            # Para formato genérico, extraer clave pública
            result = subprocess.run([
                './openssl.exe', 'pkey', '-in', key_path, 
                '-pubout'
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                # Obtener módulo de la clave pública extraída
                pubkey_data = result.stdout
                
                # Guardar temporalmente
                with open('temp_pubkey.pem', 'w') as f:
                    f.write(pubkey_data)
                
                result = subprocess.run([
                    './openssl.exe', 'pkey', '-pubin', '-in', 'temp_pubkey.pem',
                    '-text', '-noout'
                ], capture_output=True, text=True, timeout=15)
                
                # Limpiar archivo temporal
                if os.path.exists('temp_pubkey.pem'):
                    os.remove('temp_pubkey.pem')
        
        if result.returncode == 0:
            if key_type == "rsa":
                key_modulus = result.stdout.strip()
                print(f"   📊 Módulo clave: {key_modulus[:50]}...")
                return key_modulus
            else:
                print("   ✅ Clave privada procesada (formato complejo)")
                return "FORMATO_COMPLEJO"
        else:
            print(f"   ❌ Error obteniendo módulo: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error verificando clave privada: {e}")
        return None

def verificar_compatibilidad(cert_mod, key_mod):
    """Verificar que certificado y clave coincidan"""
    print("\n🔗 VERIFICANDO COMPATIBILIDAD")
    print("=" * 30)
    
    if cert_mod is None or key_mod is None:
        print("❌ No se pueden comparar (faltan datos)")
        return False
    
    if key_mod == "FORMATO_COMPLEJO":
        print("⚠️  No se puede verificar compatibilidad automáticamente")
        print("   Usando test de firma...")
        return test_firma()
    
    if cert_mod == key_mod:
        print("✅ ¡Certificado y clave privada SON COMPATIBLES!")
        return True
    else:
        print("❌ Certificado y clave privada NO son compatibles")
        print("💡 Los archivos no pertenecen al mismo par de claves")
        return False

def test_firma():
    """Test de firma para verificar compatibilidad"""
    print("\n✍️ TEST DE FIRMA")
    print("=" * 20)
    
    try:
        # Crear archivo de prueba
        with open('test_sign.txt', 'w') as f:
            f.write("Test de compatibilidad AFIP")
        
        # Intentar firmar
        result = subprocess.run([
            './openssl.exe', 'smime', '-sign',
            '-in', 'test_sign.txt',
            '-out', 'test_sign.cms',
            '-signer', 'certificados/certificado.crt',
            '-inkey', 'certificados/private.key',
            '-outform', 'DER',
            '-nodetach'
        ], capture_output=True, text=True, timeout=30)
        
        # Limpiar archivos
        if os.path.exists('test_sign.txt'):
            os.remove('test_sign.txt')
        if os.path.exists('test_sign.cms'):
            os.remove('test_sign.cms')
        
        if result.returncode == 0:
            print("✅ Test de firma exitoso - Certificados compatibles")
            return True
        else:
            print(f"❌ Test de firma falló: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test de firma: {e}")
        return False

def mostrar_soluciones():
    """Mostrar soluciones para certificados incompatibles"""
    print("\n" + "="*50)
    print("💡 SOLUCIONES PARA CERTIFICADOS INCOMPATIBLES")
    print("="*50)
    
    print("\n🔐 PROBLEMA: Certificado y clave privada no coinciden")
    print("\n📋 POSIBLES CAUSAS:")
    print("1. Se mezclaron archivos de diferentes certificados")
    print("2. Se descargó solo el certificado sin la clave correspondiente")
    print("3. Los archivos están corruptos")
    print("4. Se usó una clave antigua con un certificado nuevo")
    
    print("\n💡 SOLUCIONES:")
    print("\n🔄 OPCIÓN 1: Re-descargar desde AFIP")
    print("1. Ve a https://www.afip.gob.ar")
    print("2. Ingresa con tu CUIT y Clave Fiscal")
    print("3. Ve a 'Administrador de Relaciones de Clave Fiscal'")
    print("4. Busca tu certificado actual")
    print("5. Descarga AMBOS archivos nuevamente:")
    print("   - certificado.crt")
    print("   - private.key (o clave privada)")
    print("6. Asegúrate de que sean del MISMO certificado")
    
    print("\n🆕 OPCIÓN 2: Generar nuevo certificado")
    print("1. Genera un nuevo par certificado/clave en AFIP")
    print("2. Asócalo a WSFEv1 (Facturación Electrónica)")
    print("3. Descarga ambos archivos")
    print("4. Reemplaza los archivos en certificados/")
    
    print("\n🔍 OPCIÓN 3: Verificar archivos")
    print("1. Verifica que certificado.crt tenga:")
    print("   -----BEGIN CERTIFICATE-----")
    print("   -----END CERTIFICATE-----")
    print("2. Verifica que private.key tenga:")
    print("   -----BEGIN PRIVATE KEY----- o")
    print("   -----BEGIN RSA PRIVATE KEY-----")
    
    print("\n⚠️  IMPORTANTE:")
    print("- Ambos archivos deben ser del MISMO certificado")
    print("- La clave privada NO debe tener contraseña")
    print("- Descarga desde la misma sesión de AFIP")

def main():
    """Ejecutar diagnóstico completo"""
    print("🔍 DIAGNÓSTICO DE CERTIFICADOS AFIP")
    print("=" * 40)
    
    if not os.path.exists('./openssl.exe'):
        print("❌ OpenSSL no encontrado en el proyecto")
        print("💡 Ejecuta primero los pasos anteriores")
        return
    
    # Verificar certificado
    cert_modulus = verificar_certificado()
    
    # Verificar clave privada
    key_modulus = verificar_clave_privada()
    
    # Verificar compatibilidad
    compatibles = verificar_compatibilidad(cert_modulus, key_modulus)
    
    # Resumen final
    print("\n" + "="*40)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("="*40)
    
    if compatibles:
        print("🎉 ¡CERTIFICADOS CORRECTOS!")
        print("El problema no está en los certificados.")
        print("Puede ser un problema de conectividad con AFIP.")
    else:
        print("🚨 PROBLEMA ENCONTRADO:")
        print("Los certificados no son compatibles")
        mostrar_soluciones()

if __name__ == "__main__":
    main()