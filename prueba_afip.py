#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuración inicial para el sistema POS con AFIP
Ejecutar: python setup_afip.py
"""

import os
import json
from datetime import datetime

def crear_directorios():
    """Crear directorios necesarios"""
    directorios = [
        'certificados',
        'cache',
        'logs',
        'backups'
    ]
    
    print("📁 Creando directorios...")
    for directorio in directorios:
        os.makedirs(directorio, exist_ok=True)
        print(f"   ✅ {directorio}/")

def crear_config_local():
    """Crear archivo de configuración local"""
    print("\n⚙️ Configurando parámetros AFIP...")
    
    # Solicitar datos al usuario
    print("\n📝 Ingresa los datos de tu empresa:")
    
    cuit = input("CUIT (sin guiones, ej: 20123456789): ").strip()
    while len(cuit) != 11 or not cuit.isdigit():
        print("❌ CUIT inválido. Debe tener 11 dígitos.")
        cuit = input("CUIT (sin guiones, ej: 20123456789): ").strip()
    
    punto_venta = input("Punto de Venta (ej: 1): ").strip()
    while not punto_venta.isdigit() or int(punto_venta) < 1:
        print("❌ Punto de venta inválido.")
        punto_venta = input("Punto de Venta (ej: 1): ").strip()
    punto_venta = int(punto_venta)
    
    ambiente = input("¿Usar ambiente de homologación? (S/n): ").strip().lower()
    use_homologacion = ambiente in ['', 's', 'si', 'sí', 'y', 'yes']
    
    # Crear archivo config_local.py
    config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración local del sistema POS AFIP
Archivo generado automáticamente el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

class Config:
    """Configuración de Flask"""
    SECRET_KEY = 'tu_clave_secreta_{datetime.now().strftime("%Y%m%d")}'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://pos_user:pos_password@localhost/pos_argentina'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración adicional
    DEBUG = True
    TESTING = False

class ARCAConfig:
    """Configuración de AFIP/ARCA"""
    
    # Datos de la empresa
    CUIT = '{cuit}'
    PUNTO_VENTA = {punto_venta}
    
    # Certificados digitales
    CERT_PATH = 'certificados/certificado.crt'
    KEY_PATH = 'certificados/private.key'
    
    # Ambiente (True = Homologación, False = Producción)
    USE_HOMOLOGACION = {use_homologacion}
    
    # URLs de servicios AFIP
    @property
    def WSAA_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
        else:
            return 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
    
    @property
    def WSFEv1_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
        else:
            return 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # Cache de tokens
    TOKEN_CACHE_FILE = 'cache/token_afip.json'
    
    # Logging
    LOG_FILE = 'logs/afip.log'
    LOG_LEVEL = 'DEBUG' if USE_HOMOLOGACION else 'INFO'
'''
    
    with open('config_local.py', 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    print(f"✅ Archivo config_local.py creado")
    print(f"   CUIT: {cuit}")
    print(f"   Punto de Venta: {punto_venta}")
    print(f"   Ambiente: {'HOMOLOGACIÓN' if use_homologacion else 'PRODUCCIÓN'}")

def crear_readme_certificados():
    """Crear README con instrucciones para certificados"""
    readme_content = """# CERTIFICADOS AFIP

## ¿Qué necesitas?

Para facturar electrónicamente necesitas un certificado digital de AFIP.

## ¿Cómo obtener el certificado?

### Paso 1: Ingresar a AFIP
1. Ve a https://www.afip.gob.ar
2. Ingresa con tu CUIT y Clave Fiscal

### Paso 2: Administrador de Relaciones
1. Busca "Administrador de Relaciones de Clave Fiscal"
2. Click en "Ingresar"

### Paso 3: Generar Certificado
1. Ve a "Certificados"
2. Click en "Generar nuevo certificado"
3. Selecciona "Facturación Electrónica"
4. Sigue las instrucciones para generar el certificado

### Paso 4: Descargar archivos
Debes descargar 2 archivos:
- `certificado.crt` (certificado público)
- `private.key` (clave privada)

### Paso 5: Colocar en carpeta
Coloca ambos archivos en esta carpeta (`certificados/`):
```
certificados/
├── certificado.crt
└── private.key
```

## ¿Problemas?

- Verifica que los archivos tengan exactamente esos nombres
- Asegúrate de que el certificado no haya expirado
- En homologación, puedes usar certificados de prueba

## Verificar certificados

Ejecuta el diagnóstico:
```bash
python diagnostico_afip.py
```
"""
    
    with open('certificados/README.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ Instrucciones creadas en certificados/README.md")

def crear_script_inicio():
    """Crear script de inicio mejorado"""
    script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de inicio del sistema POS con diagnóstico
"""

import os
import sys

def verificar_requisitos():
    """Verificar que todo esté configurado"""
    print("🔍 Verificando configuración...")
    
    errores = []
    
    # Verificar config_local.py
    if not os.path.exists('config_local.py'):
        errores.append("❌ Falta config_local.py (ejecuta: python setup_afip.py)")
    
    # Verificar certificados
    if not os.path.exists('certificados/certificado.crt'):
        errores.append("❌ Falta certificado.crt")
    
    if not os.path.exists('certificados/private.key'):
        errores.append("❌ Falta private.key")
    
    # Verificar directorios
    dirs_necesarios = ['cache', 'logs', 'certificados']
    for directorio in dirs_necesarios:
        if not os.path.exists(directorio):
            errores.append(f"❌ Falta directorio {directorio}/")
    
    if errores:
        print("\\n🚨 ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"   {error}")
        print("\\n💡 SOLUCIÓN:")
        print("   1. Ejecuta: python setup_afip.py")
        print("   2. Lee: certificados/README.md")
        print("   3. Ejecuta: python diagnostico_afip.py")
        return False
    
    print("✅ Configuración OK")
    return True

def iniciar_aplicacion():
    """Iniciar la aplicación Flask"""
    try:
        # Importar la aplicación
        from app import app, create_tables
        
        print("🚀 Iniciando POS Argentina...")
        print("📍 URL: http://localhost:5000")
        print("👤 Usuario: admin")
        print("🔑 Contraseña: admin123")
        print()
        
        # Crear tablas
        with app.app_context():
            create_tables()
        
        # Iniciar servidor
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ Error iniciando aplicación: {e}")
        print("\\n💡 SOLUCIÓN:")
        print("   Verifica que tengas instaladas las dependencias:")
        print("   pip install flask flask-sqlalchemy pymysql zeep cryptography")

if __name__ == "__main__":
    if verificar_requisitos():
        iniciar_aplicacion()
    else:
        sys.exit(1)
'''
    
    with open('iniciar.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("✅ Script de inicio creado: iniciar.py")

def crear_requirements():
    """Crear archivo requirements.txt"""
    requirements = """# Dependencias del sistema POS AFIP
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
PyMySQL==1.1.0
zeep==4.2.1
cryptography==41.0.4
requests==2.31.0
python-dateutil==2.8.2
lxml==4.9.3
urllib3==2.0.4
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✅ Archivo requirements.txt creado")

def mostrar_resumen():
    """Mostrar resumen de configuración"""
    print("\n" + "="*50)
    print("🎉 CONFIGURACIÓN COMPLETADA")
    print("="*50)
    
    print("\n📁 ARCHIVOS CREADOS:")
    archivos = [
        "config_local.py - Configuración del sistema",
        "requirements.txt - Dependencias Python", 
        "iniciar.py - Script de inicio",
        "certificados/README.md - Instrucciones"
    ]
    
    for archivo in archivos:
        print(f"   ✅ {archivo}")
    
    print("\n📋 PRÓXIMOS PASOS:")
    
    print("\n1️⃣ INSTALAR DEPENDENCIAS:")
    print("   pip install -r requirements.txt")
    
    print("\n2️⃣ OBTENER CERTIFICADOS AFIP:")
    print("   - Lee: certificados/README.md")
    print("   - Descarga certificado.crt y private.key de AFIP")
    print("   - Colócalos en certificados/")
    
    print("\n3️⃣ PROBAR CONEXIÓN:")
    print("   python diagnostico_afip.py")
    
    print("\n4️⃣ INICIAR SISTEMA:")
    print("   python iniciar.py")
    
    print("\n🌐 ACCESO:")
    print("   URL: http://localhost:5000")
    print("   Usuario: admin")
    print("   Contraseña: admin123")

def main():
    """Función principal"""
    print("🔧 CONFIGURACIÓN INICIAL - POS AFIP")
    print("="*40)
    
    print("\nEste script configurará tu sistema para facturar con AFIP.")
    continuar = input("¿Continuar? (S/n): ").strip().lower()
    
    if continuar not in ['', 's', 'si', 'sí', 'y', 'yes']:
        print("Configuración cancelada.")
        return
    
    try:
        crear_directorios()
        crear_config_local()
        crear_readme_certificados()
        crear_script_inicio()
        crear_requirements()
        mostrar_resumen()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Configuración interrumpida.")
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")

if __name__ == "__main__":
    main()