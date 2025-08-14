#!/usr/bin/env python3
# setup_production.py - Configurar sistema para producción

import os
import sys
import shutil
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from datetime import datetime
import json

def print_header():
    print("=" * 60)
    print("  CONFIGURACIÓN PARA PRODUCCIÓN - POS ARGENTINA")
    print("=" * 60)
    print()

def check_certificates():
    """Verifica que los certificados estén presentes y sean válidos"""
    print("🔐 Verificando certificados AFIP...")
    
    cert_path = 'certificados/certificado.crt'
    key_path = 'certificados/private.key'
    
    if not os.path.exists(cert_path):
        print(f"❌ ERROR: No se encuentra {cert_path}")
        print("   Copia tu archivo .crt a la carpeta certificados/")
        return False
    
    if not os.path.exists(key_path):
        print(f"❌ ERROR: No se encuentra {key_path}")
        print("   Copia tu archivo .key a la carpeta certificados/")
        return False
    
    try:
        # Verificar certificado
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        cert = x509.load_pem_x509_certificate(cert_data)
        
        # Obtener información del certificado
        subject = cert.subject
        issuer = cert.issuer
        not_after = cert.not_valid_after
        
        # Buscar el CUIT en el certificado
        cuit_found = None
        for attribute in subject:
            if 'serialNumber' in str(attribute.oid) or 'CUIT' in str(attribute.value):
                cuit_found = str(attribute.value)
                break
        
        print("✅ Certificado válido:")
        print(f"   Emisor: {issuer.rfc4514_string()}")
        print(f"   Válido hasta: {not_after.strftime('%d/%m/%Y')}")
        if cuit_found:
            print(f"   CUIT encontrado: {cuit_found}")
        
        # Verificar si está por vencer (30 días)
        days_to_expire = (not_after - datetime.now()).days
        if days_to_expire < 30:
            print(f"⚠️  ADVERTENCIA: El certificado vence en {days_to_expire} días")
        
        # Verificar clave privada
        with open(key_path, 'rb') as f:
            key_data = f.read()
        
        private_key = serialization.load_pem_private_key(key_data, password=None)
        print("✅ Clave privada válida")
        
        return True, cuit_found
        
    except Exception as e:
        print(f"❌ ERROR al verificar certificados: {e}")
        return False, None

def setup_production_config():
    """Configura el archivo de producción"""
    print("\n⚙️  Configurando archivo de producción...")
    
    # Solicitar datos de la empresa
    print("\nIngresa los datos de tu empresa:")
    cuit = input("CUIT (sin guiones): ").strip()
    punto_venta = input("Punto de venta AFIP: ").strip()
    razon_social = input("Razón social: ").strip()
    
    # Validar CUIT
    if len(cuit) != 11 or not cuit.isdigit():
        print("❌ ERROR: El CUIT debe tener 11 dígitos sin guiones")
        return False
    
    # Crear configuración personalizada
    config_content = f'''# config_production.py - Configuración de PRODUCCIÓN

import os
from datetime import timedelta

class Config:
    # Seguridad - CAMBIAR EN PRODUCCIÓN
    SECRET_KEY = '{os.urandom(32).hex()}'
    
    # Base de datos
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'pos_user'
    MYSQL_PASSWORD = 'TU_PASSWORD_MYSQL_AQUI'  # ⚠️ CAMBIAR
    MYSQL_DATABASE = 'pos_argentina'
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{{MYSQL_USER}}:{{MYSQL_PASSWORD}}@{{MYSQL_HOST}}/{{MYSQL_DATABASE}}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {{
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }}
    
    # Flask para producción
    DEBUG = False
    TESTING = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

class ARCAConfig:
    # DATOS REALES DE TU EMPRESA
    CUIT = '{cuit}'
    PUNTO_VENTA = {punto_venta}
    RAZON_SOCIAL = '{razon_social}'
    
    # Certificados
    CERT_PATH = 'certificados/certificado.crt'
    KEY_PATH = 'certificados/private.key'
    
    # ⚠️ PRODUCCIÓN - URLs REALES DE AFIP
    USE_HOMOLOGACION = False
    
    WSAA_URL = 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    WSFEv1_URL = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    TOKEN_CACHE_FILE = 'cache/token_arca_prod.json'
    
    # Configuración de producción
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    LOG_ALL_REQUESTS = True
'''
    
    with open('config_production.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print("✅ Archivo config_production.py creado")
    return True

def setup_production_app():
    """Crea el archivo app_production.py"""
    print("\n🚀 Creando aplicación de producción...")
    
    app_content = '''#!/usr/bin/env python3
# app_production.py - Aplicación para PRODUCCIÓN

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Asegurar que estamos en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar configuración de producción
from config_production import Config, ARCAConfig

# Importar la aplicación base
from app import app, db

# Aplicar configuración de producción
app.config.from_object(Config)

# Configurar logging para producción
def setup_logging():
    """Configura logs para producción"""
    
    # Crear directorios si no existen
    os.makedirs('logs', exist_ok=True)
    
    # Configurar formato de logs
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
    )
    
    # Log principal
    file_handler = RotatingFileHandler(
        'logs/pos_produccion.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Log de AFIP
    afip_handler = RotatingFileHandler(
        'logs/afip_produccion.log',
        maxBytes=10*1024*1024,
        backupCount=10
    )
    afip_handler.setFormatter(formatter)
    afip_handler.setLevel(logging.DEBUG)
    
    # Configurar logger de la aplicación
    app.logger.addHandler(file_handler)
    app.logger.addHandler(afip_handler)
    app.logger.setLevel(logging.INFO)
    
    # Solo errores en consola para producción
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

def validate_production_setup():
    """Valida que todo esté configurado para producción"""
    
    print("🔍 Validando configuración de producción...")
    
    # Verificar certificados
    if not os.path.exists('certificados/certificado.crt'):
        print("❌ ERROR: Falta certificado.crt")
        return False
    
    if not os.path.exists('certificados/private.key'):
        print("❌ ERROR: Falta private.key")
        return False
    
    # Verificar configuración
    if ARCAConfig.CUIT == '20123456789':
        print("❌ ERROR: Debes configurar tu CUIT real")
        return False
    
    if ARCAConfig.USE_HOMOLOGACION:
        print("❌ ERROR: USE_HOMOLOGACION debe ser False para producción")
        return False
    
    # Verificar directorios
    os.makedirs('cache', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("✅ Configuración de producción válida")
    return True

if __name__ == '__main__':
    
    print("🚀 INICIANDO POS ARGENTINA - MODO PRODUCCIÓN")
    print("=" * 50)
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"CUIT: {ARCAConfig.CUIT}")
    print(f"Punto de Venta: {ARCAConfig.PUNTO_VENTA}")
    print(f"Ambiente: {'HOMOLOGACIÓN' if ARCAConfig.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    print("=" * 50)
    
    # Validar configuración
    if not validate_production_setup():
        print("❌ Configuración inválida. Revisa los errores arriba.")
        sys.exit(1)
    
    # Configurar logging
    setup_logging()
    
    # Log de inicio
    app.logger.info("=== INICIANDO POS ARGENTINA PRODUCCIÓN ===")
    app.logger.info(f"CUIT: {ARCAConfig.CUIT}")
    app.logger.info(f"Punto de Venta: {ARCAConfig.PUNTO_VENTA}")
    app.logger.info(f"Ambiente: {'HOMOLOGACIÓN' if ARCAConfig.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    
    print("✅ Sistema configurado para PRODUCCIÓN")
    print("📍 URL: http://localhost:5000")
    print("📊 Logs en: logs/pos_produccion.log")
    print("🔒 Certificados validados")
    print()
    print("⚠️  IMPORTANTE: Este es el ambiente de PRODUCCIÓN real")
    print("   Todas las facturas serán válidas ante AFIP")
    print()
    print("Presiona Ctrl+C para detener")
    print()
    
    try:
        # Crear tablas si no existen
        with app.app_context():
            db.create_all()
        
        # Iniciar aplicación en modo producción
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        app.logger.info("=== DETENIENDO POS ARGENTINA ===")
        print("\\n🛑 Sistema detenido por el usuario")
    except Exception as e:
        app.logger.error(f"Error fatal: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)
'''
    
    with open('app_production.py', 'w', encoding='utf-8') as f:
        f.write(app_content)
    
    # Hacer ejecutable en Linux/Mac
    if os.name != 'nt':
        os.chmod('app_production.py', 0o755)
    
    print("✅ Archivo app_production.py creado")

def create_production_scripts():
    """Crea scripts para manejo de producción"""
    print("\n📋 Creando scripts de producción...")
    
    # Script de inicio
    start_script = '''#!/bin/bash
# start_production.sh - Iniciar POS en producción

echo "🚀 Iniciando POS Argentina - PRODUCCIÓN"
echo "⚠️  MODO PRODUCCIÓN: Las facturas serán reales"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi

# Verificar archivos
if [ ! -f "app_production.py" ]; then
    echo "❌ app_production.py no encontrado"
    exit 1
fi

if [ ! -f "certificados/certificado.crt" ]; then
    echo "❌ Certificado AFIP no encontrado"
    exit 1
fi

# Crear logs
mkdir -p logs

# Iniciar aplicación
python3 app_production.py
'''
    
    with open('start_production.sh', 'w') as f:
        f.write(start_script)
    
    if os.name != 'nt':
        os.chmod('start_production.sh', 0o755)
    
    # Script de Windows
    start_bat = '''@echo off
REM start_production.bat - Iniciar POS en producción (Windows)

echo 🚀 Iniciando POS Argentina - PRODUCCIÓN
echo ⚠️  MODO PRODUCCIÓN: Las facturas serán reales
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado
    pause
    exit /b 1
)

REM Verificar archivos
if not exist "app_production.py" (
    echo ❌ app_production.py no encontrado
    pause
    exit /b 1
)

if not exist "certificados\\certificado.crt" (
    echo ❌ Certificado AFIP no encontrado
    pause
    exit /b 1
)

REM Crear logs
if not exist "logs" mkdir logs

REM Iniciar aplicación
python app_production.py
pause
'''
    
    with open('start_production.bat', 'w') as f:
        f.write(start_bat)
    
    print("✅ Scripts de inicio creados")

def main():
    """Función principal"""
    print_header()
    
    print("Este script configurará el sistema para PRODUCCIÓN real.")
    print("⚠️  IMPORTANTE: Las facturas emitidas serán válidas ante AFIP")
    print()
    
    confirm = input("¿Continuar con la configuración de PRODUCCIÓN? (SI/no): ").strip()
    if confirm.lower() not in ['si', 's', 'yes', 'y', '']:
        print("Configuración cancelada")
        return
    
    # Verificar certificados
    cert_valid, cuit_cert = check_certificates()
    if not cert_valid:
        print("❌ ERROR: Los certificados no son válidos")
        return
    
    # Configurar producción
    if not setup_production_config():
        print("❌ ERROR: No se pudo crear la configuración")
        return
    
    setup_production_app()
    create_production_scripts()
    
    print("\n" + "=" * 60)
    print("  ✅ CONFIGURACIÓN DE PRODUCCIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("📋 PRÓXIMOS PASOS:")
    print()
    print("1. ⚠️  EDITAR config_production.py:")
    print("   - Cambiar la contraseña de MySQL")
    print("   - Verificar que el CUIT sea correcto")
    print()
    print("2. 🚀 INICIAR EN PRODUCCIÓN:")
    print("   Linux/Mac: ./start_production.sh")
    print("   Windows:   start_production.bat")
    print("   Manual:    python app_production.py")
    print()
    print("3. 🔍 MONITOREAR LOGS:")
    print("   - logs/pos_produccion.log")
    print("   - logs/afip_produccion.log")
    print()
    print("⚠️  RECORDATORIO IMPORTANTE:")
    print("   - Este es el ambiente de PRODUCCIÓN")
    print("   - Todas las facturas serán reales")
    print("   - Verifica todo antes de procesar ventas")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n❌ Configuración interrumpida")
    except Exception as e:
        print(f"\\n❌ Error: {e}")