#!/usr/bin/env python3
# install.py - Script de instalación para POS Argentina

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error
import getpass
from pathlib import Path

def print_header():
    print("=" * 60)
    print("  INSTALADOR POS ARGENTINA - FLASK + MYSQL + ARCA")
    print("=" * 60)
    print()

def check_python_version():
    """Verifica que la versión de Python sea compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Se requiere Python 3.8 o superior")
        print(f"   Versión actual: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} - OK")

def install_requirements():
    """Instala las dependencias de Python"""
    print("\n📦 Instalando dependencias de Python...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
    except subprocess.CalledProcessError:
        print("❌ Error al instalar dependencias")
        sys.exit(1)

def create_directories():
    """Crea los directorios necesarios"""
    print("\n📁 Creando directorios...")
    directories = [
        "templates",
        "static/css",
        "static/js",
        "certificados",
        "cache",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")

def setup_mysql():
    """Configura la base de datos MySQL"""
    print("\n🗄️  Configuración de MySQL")
    print("Por favor, ingrese los datos de conexión a MySQL:")
    
    host = input("Host de MySQL [localhost]: ").strip() or "localhost"
    port = input("Puerto [3306]: ").strip() or "3306"
    admin_user = input("Usuario administrador de MySQL [root]: ").strip() or "root"
    admin_password = getpass.getpass("Contraseña del administrador: ")
    
    try:
        # Conectar como administrador
        connection = mysql.connector.connect(
            host=host,
            port=int(port),
            user=admin_user,
            password=admin_password
        )
        
        cursor = connection.cursor()
        
        print("✅ Conexión a MySQL exitosa")
        
        # Crear base de datos
        print("   Creando base de datos 'pos_argentina'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS pos_argentina CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # Crear usuario de la aplicación
        app_password = input("Contraseña para el usuario 'pos_user' [pos_password]: ").strip() or "pos_password"
        
        print("   Creando usuario 'pos_user'...")
        cursor.execute("CREATE USER IF NOT EXISTS 'pos_user'@'localhost' IDENTIFIED BY %s", (app_password,))
        cursor.execute("GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost'")
        cursor.execute("FLUSH PRIVILEGES")
        
        # Ejecutar script de creación de tablas
        print("   Ejecutando script de base de datos...")
        with open('setup_database.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Ejecutar cada comando por separado
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)
        
        connection.commit()
        cursor.close()
        connection.close()
     
        print("✅ Base de datos configurada correctamente")
        
        # Crear archivo de configuración
        config_content = f"""# config_local.py - Configuración local generada automáticamente

import os

class Config:
    SECRET_KEY = '{os.urandom(24).hex()}'
    
    # Configuración MySQL
    MYSQL_HOST = '{host}'
    MYSQL_PORT = {port}
    MYSQL_USER = 'pos_user'
    MYSQL_PASSWORD = '{app_password}'
    MYSQL_DATABASE = 'pos_argentina'
    
    # URI de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{{MYSQL_USER}}:{{MYSQL_PASSWORD}}@{{MYSQL_HOST}}:{{MYSQL_PORT}}/{{MYSQL_DATABASE}}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ARCAConfig:
    # CAMBIAR POR TUS DATOS REALES
    CUIT = '20203852100'  # ⚠️ REEMPLAZAR CON TU CUIT
    PUNTO_VENTA = 1       # ⚠️ REEMPLAZAR CON TU PUNTO DE VENTA
    RAZON_SOCIAL = 'SQLDATA'  # ⚠️ REEMPLAZAR CON TU RAZÓN SOCIAL
    
    # CERTIFICADOS (colocar en carpeta certificados/)
    CERT_PATH = 'certificados/pablo_7db7c098314de1a4.crt'
    KEY_PATH = 'certificados/privada.key'
    
    # USAR HOMOLOGACIÓN POR DEFECTO
    USE_HOMOLOGACION = True
    
    # URLs de AFIP
    @property
    def WSAA_URL(self):
        return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms' if self.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    
    @property
    def WSFEv1_URL(self):
        return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
"""
        
        with open('config_local.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("✅ Archivo de configuración creado: config_local.py")
        
    except Error as e:
        print(f"❌ Error de MySQL: {e}")
        sys.exit(1)

def setup_arca_certificates():
    """Guía para configurar certificados ARCA"""
    print("\n🔐 Configuración de Certificados ARCA/AFIP")
    print()
    print("Para utilizar la integración con ARCA/AFIP, necesitas:")
    print("1. Certificado digital (.crt)")
    print("2. Clave privada (.key)")
    print()
    print("Pasos para obtener los certificados:")
    print("1. Ingresar a https://auth.afip.gob.ar")
    print("2. Ir a 'Administrador de Relaciones de Clave Fiscal'")
    print("3. Generar certificado para 'Facturación Electrónica'")
    print("4. Descargar el certificado y la clave")
    print("5. Colocar los archivos en la carpeta 'certificados/' con los nombres:")
    print("   - certificado.crt")
    print("   - private.key")
    print()
    
    cert_exists = os.path.exists('certificados/certificado.crt')
    key_exists = os.path.exists('certificados/private.key')
    
    if cert_exists and key_exists:
        print("✅ Certificados encontrados")
    else:
        print("⚠️  Certificados no encontrados")
        print("   El sistema funcionará en modo local hasta que configures los certificados")

def create_templates():
    """Crea los archivos de templates HTML"""
    print("\n📄 Creando templates HTML...")
    
    # Aquí deberías copiar los templates que creamos anteriormente
    # Por brevedad, solo creo un mensaje
    print("   ✅ Templates HTML (usar los archivos proporcionados)")

def create_run_script():
    """Crea script para ejecutar la aplicación"""
    run_script = """#!/usr/bin/env python3
# run.py - Script para ejecutar el POS Argentina

from app import app
import os

if __name__ == '__main__':
    # Crear directorios si no existen
    os.makedirs('cache', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    print("🚀 Iniciando POS Argentina...")
    print("📍 URL: http://localhost:5000")
    print("👤 Usuario: admin")
    print("🔑 Contraseña: admin123")
    print()
    print("Presiona Ctrl+C para detener el servidor")
    print()
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )
"""
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(run_script)
    
    # Hacer ejecutable en sistemas Unix
    if os.name != 'nt':
        os.chmod('run.py', 0o755)
    
    print("✅ Script de ejecución creado: run.py")

def show_final_instructions():
    """Muestra las instrucciones finales"""
    print("\n" + "=" * 60)
    print("  🎉 INSTALACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("Para iniciar el sistema:")
    print("  python run.py")
    print()
    print("Acceder al sistema:")
    print("  URL: http://localhost:5000")
    print("  Usuario: admin")
    print("  Contraseña: admin123")
    print()
    print("⚠️  CONFIGURACIÓN IMPORTANTE:")
    print("1. Editar config_local.py con tus datos reales:")
    print("   - CUIT de tu empresa")
    print("   - Punto de venta asignado por AFIP")
    print("   - Razón social")
    print()
    print("2. Colocar certificados ARCA en certificados/:")
    print("   - certificado.crt")
    print("   - private.key")
    print()
    print("3. Para producción, cambiar USE_HOMOLOGACION = False")
    print()
    print("📚 Documentación AFIP: https://www.afip.gob.ar/ws/")
    print()

def main():
    """Función principal del instalador"""
    print_header()
    
    print("Este script instalará y configurará el sistema POS Argentina")
    confirm = input("¿Continuar? (s/N): ").lower().strip()
    
    if confirm not in ['s', 'si', 'y', 'yes']:
        print("Instalación cancelada")
        sys.exit(0)
    
    print("\n🔍 Verificando requisitos...")
    check_python_version()
    
    create_directories()
    install_requirements()
    setup_mysql()
    setup_arca_certificates()
    create_run_script()
    
    show_final_instructions()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Instalación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la instalación: {e}")
        sys.exit(1)