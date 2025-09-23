# migration_caja.py - Script para corregir tabla movimientos_caja

from flask import Flask
from sqlalchemy import text
import sys
import os

def migrar_tabla_movimientos_caja():
    """Migrar tabla movimientos_caja agregando columna usuario_id"""
    
    # Importar desde tu app principal
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import app, db
    
    with app.app_context():
        try:
            print("🔄 Iniciando migración de tabla movimientos_caja...")
            
            # Verificar si la columna usuario_id ya existe
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'movimientos_caja' 
                AND COLUMN_NAME = 'usuario_id'
                AND TABLE_SCHEMA = DATABASE()
            """)).fetchone()
            
            if result.count > 0:
                print("✅ La columna usuario_id ya existe")
                return True
            
            print("➕ Agregando columna usuario_id...")
            
            # Agregar columna usuario_id
            db.session.execute(text("""
                ALTER TABLE movimientos_caja 
                ADD COLUMN usuario_id INT NOT NULL DEFAULT 1
            """))
            
            # Agregar clave foránea
            db.session.execute(text("""
                ALTER TABLE movimientos_caja 
                ADD CONSTRAINT fk_movimientos_caja_usuario 
                FOREIGN KEY (usuario_id) REFERENCES usuario(id)
            """))
            
            db.session.commit()
            
            print("✅ Columna usuario_id agregada exitosamente")
            print("✅ Clave foránea configurada")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            db.session.rollback()
            return False

def verificar_estructura_tablas():
    """Verificar que todas las tablas tengan la estructura correcta"""
    
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import app, db
    
    with app.app_context():
        try:
            print("🔍 Verificando estructura de tablas...")
            
            # Verificar tabla caja_aperturas
            result_caja = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'caja_aperturas' 
                AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
            """)).fetchall()
            
            print("📋 Columnas en caja_aperturas:")
            for col in result_caja:
                print(f"   - {col[0]}")
            
            # Verificar tabla movimientos_caja
            result_mov = db.session.execute(text("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'movimientos_caja' 
                AND TABLE_SCHEMA = DATABASE()
                ORDER BY ORDINAL_POSITION
            """)).fetchall()
            
            print("📋 Columnas en movimientos_caja:")
            for col in result_mov:
                print(f"   - {col[0]}")
            
            # Verificar si las tablas existen
            tablas_esperadas = ['caja_aperturas', 'movimientos_caja']
            for tabla in tablas_esperadas:
                existe = db.session.execute(text(f"""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = '{tabla}' 
                    AND TABLE_SCHEMA = DATABASE()
                """)).fetchone()
                
                if existe.count > 0:
                    print(f"✅ Tabla {tabla} existe")
                else:
                    print(f"❌ Tabla {tabla} NO existe")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verificando tablas: {e}")
            return False

def crear_tablas_caja_completas():
    """Crear las tablas de caja desde cero si no existen"""
    
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from app import app, db
    
    with app.app_context():
        try:
            print("🏗️ Creando tablas de caja completas...")
            
            # Crear tabla caja_aperturas
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS caja_aperturas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    fecha_apertura DATETIME NOT NULL,
                    fecha_cierre DATETIME NULL,
                    monto_inicial DECIMAL(10,2) NOT NULL,
                    monto_cierre DECIMAL(10,2) NULL,
                    efectivo_teorico DECIMAL(10,2) NULL,
                    efectivo_real DECIMAL(10,2) NULL,
                    diferencia DECIMAL(10,2) NULL,
                    observaciones_apertura TEXT NULL,
                    observaciones_cierre TEXT NULL,
                    usuario_apertura_id INT NOT NULL,
                    usuario_cierre_id INT NULL,
                    estado VARCHAR(20) DEFAULT 'abierta',
                    activa BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (usuario_apertura_id) REFERENCES usuario(id),
                    FOREIGN KEY (usuario_cierre_id) REFERENCES usuario(id)
                )
            """))
            
            # Crear tabla movimientos_caja
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS movimientos_caja (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    caja_id INT NOT NULL,
                    tipo VARCHAR(10) NOT NULL,
                    descripcion VARCHAR(200) NOT NULL,
                    monto DECIMAL(10,2) NOT NULL,
                    notas TEXT NULL,
                    fecha DATETIME NOT NULL,
                    usuario_id INT NOT NULL,
                    FOREIGN KEY (caja_id) REFERENCES caja_aperturas(id),
                    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
                )
            """))
            
            db.session.commit()
            
            print("✅ Tablas de caja creadas exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🚀 Script de Migración de Caja")
    print("=" * 40)
    
    # Paso 1: Verificar estructura actual
    print("\n1. Verificando estructura actual...")
    verificar_estructura_tablas()
    
    # Paso 2: Crear tablas completas si no existen
    print("\n2. Creando tablas si no existen...")
    crear_tablas_caja_completas()
    
    # Paso 3: Migrar columna usuario_id si es necesario
    print("\n3. Migrando columna usuario_id...")
    migrar_tabla_movimientos_caja()
    
    # Paso 4: Verificación final
    print("\n4. Verificación final...")
    verificar_estructura_tablas()
    
    print("\n✅ Migración completada")
    print("🔄 Reinicia tu aplicación para aplicar los cambios")