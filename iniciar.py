#!/usr/bin/env python3
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
        print("\n🚨 ERRORES ENCONTRADOS:")
        for error in errores:
            print(f"   {error}")
        print("\n💡 SOLUCIÓN:")
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
        print("\n💡 SOLUCIÓN:")
        print("   Verifica que tengas instaladas las dependencias:")
        print("   pip install flask flask-sqlalchemy pymysql zeep cryptography")

if __name__ == "__main__":
    if verificar_requisitos():
        iniciar_aplicacion()
    else:
        sys.exit(1)
