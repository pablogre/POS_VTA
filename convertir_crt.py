#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertir certificados a formato estándar para OpenSSL
Ejecutar: python convertir_certificados.py
"""

import subprocess
import os
import shutil

def hacer_backup():
    """Hacer backup de certificados actuales"""
    print("💾 Haciendo backup de certificados...")
    
    backup_dir = 'certificados_originales'
    os.makedirs(backup_dir, exist_ok=True)
    
    archivos = ['certificados/certificado.crt', 'certificados/private.key']
    
    for archivo in archivos:
        if os.path.exists(archivo):
            nombre = os.path.basename(archivo)
            backup_path = os.path.join(backup_dir, nombre)
            shutil.copy2(archivo, backup_path)
            print(f"   ✅ Backup: {archivo} -> {backup_path}")

def convertir_certificado():
    """Convertir certificado a formato PEM estándar"""
    print("\n🔐 Convirtiendo certificado...")
    
    try:
        # Convertir certificado a PEM estándar
        result = subprocess.run([
            './openssl.exe', 'x509', 
            '-in', 'certificados/certificado.crt',
            '-out', 'certificados/certificado_new.crt',
            '-outform', 'PEM'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("   ✅ Certificado convertido a PEM estándar")
            
            # Reemplazar el original
            shutil.move('certificados/certificado_new.crt', 'certificados/certificado.crt')
            print("   ✅ Certificado reemplazado")
            return True
        else:
            print(f"   ❌ Error convirtiendo certificado: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def convertir_clave_privada():
    """Convertir clave privada a formato PEM estándar"""
    print("\n🔑 Convirtiendo clave privada...")
    
    try:
        # Convertir clave privada a PEM estándar (sin contraseña)
        result = subprocess.run([
            './openssl.exe', 'rsa', 
            '-in', 'certificados/private.key',
            '-out', 'certificados/private_new.key',
            '-outform', 'PEM'
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            print("   ✅ Clave privada convertida a PEM estándar")
            
            # Reemplazar la original
            shutil.move('certificados/private_new.key', 'certificados/private.key')
            print("   ✅ Clave privada reemplazada")
            return True
        else:
            print(f"   ❌ Error convirtiendo clave: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def probar_firma_nueva():
    """Probar firma con certificados convertidos"""
    print("\n✍️ Probando firma con certificados convertidos...")
    
    try:
        # Crear archivo de prueba
        with open('test_converted.txt', 'w') as f:
            f.write("Test con certificados convertidos")
        
        # Intentar firmar
        result = subprocess.run([
            './openssl.exe', 'smime', '-sign',
            '-in', 'test_converted.txt',
            '-out', 'test_converted.cms',
            '-signer', 'certificados/certificado.crt',
            '-inkey', 'certificados/private.key',
            '-outform', 'DER',
            '-nodetach'
        ], capture_output=True, text=True, timeout=30)
        
        # Limpiar archivos
        if os.path.exists('test_converted.txt'):
            os.remove('test_converted.txt')
        if os.path.exists('test_converted.cms'):
            os.remove('test_converted.cms')
        
        if result.returncode == 0:
            print("   ✅ Firma exitosa con certificados convertidos")
            return True
        else:
            print(f"   ❌ Firma falló: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Convertir certificados"""
    print("🔄 CONVERSIÓN DE CERTIFICADOS A FORMATO ESTÁNDAR")
    print("=" * 50)
    print("Esto puede solucionar problemas de formato con OpenSSL")
    
    continuar = input("\n¿Continuar con la conversión? (S/n): ").strip().lower()
    if continuar in ['n', 'no']:
        print("Conversión cancelada")
        return
    
    # Hacer backup
    hacer_backup()
    
    # Convertir certificado
    cert_ok = convertir_certificado()
    
    # Convertir clave privada
    key_ok = convertir_clave_privada()
    
    if cert_ok and key_ok:
        # Probar firma
        if probar_firma_nueva():
            print("\n🎉 ¡CERTIFICADOS CONVERTIDOS Y FUNCIONANDO!")
            print("\n🚀 SIGUIENTE PASO:")
            print("   Ejecuta: python app.py")
            print("   Prueba una venta")
            
            print("\n💾 BACKUP:")
            print("   Originales guardados en: certificados_originales/")
            
        else:
            print("\n❌ La conversión no solucionó el problema")
            print("💡 Puedes restaurar los originales desde: certificados_originales/")
    else:
        print("\n❌ Error en la conversión")
        print("💡 Restaura los originales desde: certificados_originales/")

if __name__ == "__main__":
    main()