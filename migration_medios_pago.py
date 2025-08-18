# migration_medios_pago_mysql.py
# EJECUTAR ESTE SCRIPT UNA SOLA VEZ para crear la tabla medios_pago

import mysql.connector
from datetime import datetime

# *** CONFIGURAR TUS DATOS DE MySQL AQUÍ ***
MYSQL_CONFIG = {
    'host': 'localhost',  # Cambiar si es necesario
    'user': 'pos_user',   # Tu usuario MySQL
    'password': 'pos_password',  # Tu contraseña MySQL
    'database': 'pos_argentina'  # Tu base de datos
}

def crear_tabla_medios_pago():
    """Crear tabla medios_pago en MySQL"""
    
    try:
        print("🔌 Conectando a MySQL...")
        
        # Conectar a MySQL
        conexion = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conexion.cursor()
        
        print(f"✅ Conectado a MySQL en {MYSQL_CONFIG['host']}")
        
        # SQL para crear la tabla
        sql_crear_tabla = """
        CREATE TABLE IF NOT EXISTS medios_pago (
            id INT AUTO_INCREMENT PRIMARY KEY,
            factura_id INT NOT NULL,
            medio_pago VARCHAR(20) NOT NULL,
            importe DECIMAL(10,2) NOT NULL,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_medios_pago_factura (factura_id),
            INDEX idx_medios_pago_fecha (fecha_registro),
            INDEX idx_medios_pago_medio (medio_pago),
            FOREIGN KEY (factura_id) REFERENCES factura (id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        print("📋 Creando tabla medios_pago...")
        cursor.execute(sql_crear_tabla)
        print("✅ Tabla 'medios_pago' creada correctamente")
        
        # Verificar que la tabla existe
        cursor.execute("SHOW TABLES LIKE 'medios_pago'")
        resultado = cursor.fetchone()
        
        if resultado:
            print("✅ Verificación: Tabla 'medios_pago' existe en la base de datos")
            
            # Mostrar estructura de la tabla
            cursor.execute("DESCRIBE medios_pago")
            estructura = cursor.fetchall()
            
            print("\n📋 Estructura de la tabla 'medios_pago':")
            for columna in estructura:
                print(f"   - {columna[0]} ({columna[1]})")
            
            return True
        else:
            print("❌ Error: La tabla no fue creada correctamente")
            return False
            
    except mysql.connector.Error as e:
        print(f"❌ Error MySQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()
        print("🔌 Conexión cerrada")

def verificar_tablas_existentes():
    """Verificar qué tablas existen en MySQL"""
    try:
        conexion = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conexion.cursor()
        
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        
        print("📋 Tablas existentes en la base de datos MySQL:")
        for tabla in tablas:
            print(f"   - {tabla[0]}")
        
        return [tabla[0] for tabla in tablas]
        
    except mysql.connector.Error as e:
        print(f"❌ Error MySQL verificando tablas: {e}")
        return []
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

def insertar_datos_prueba():
    """Insertar algunos datos de prueba en MySQL"""
    try:
        conexion = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conexion.cursor()
        
        # Solo insertar si hay facturas existentes
        cursor.execute("SELECT COUNT(*) FROM factura")
        cantidad_facturas = cursor.fetchone()[0]
        
        if cantidad_facturas > 0:
            print(f"📊 Se encontraron {cantidad_facturas} facturas existentes")
            
            # Obtener una factura de ejemplo
            cursor.execute("SELECT id, total FROM factura LIMIT 1")
            factura_ejemplo = cursor.fetchone()
            
            if factura_ejemplo:
                factura_id, total = factura_ejemplo
                
                # Insertar medio de pago de ejemplo
                sql_ejemplo = """
                INSERT INTO medios_pago (factura_id, medio_pago, importe, fecha_registro)
                VALUES (%s, 'efectivo', %s, NOW())
                """
                
                cursor.execute(sql_ejemplo, (factura_id, total))
                conexion.commit()
                
                print(f"✅ Medio de pago de ejemplo insertado para factura {factura_id}")
                
        else:
            print("⚠️ No hay facturas existentes para insertar datos de prueba")
            
    except mysql.connector.Error as e:
        print(f"❌ Error MySQL insertando datos: {e}")
    except Exception as e:
        print(f"❌ Error insertando datos de prueba: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

def verificar_conexion_mysql():
    """Verificar que la conexión a MySQL funciona"""
    try:
        conexion = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conexion.cursor()
        
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Conectado a MySQL versión: {version}")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error conectando a MySQL: {e}")
        print("💡 Verifica tu configuración de conexión en MYSQL_CONFIG")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conexion' in locals():
            conexion.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración para medios de pago en MySQL...")
    print("=" * 60)
    
    # Verificar conexión a MySQL
    if not verificar_conexion_mysql():
        print("❌ No se pudo conectar a MySQL. Verifica tu configuración.")
        print("💡 Edita las variables en MYSQL_CONFIG con tus datos:")
        print(f"   Host: {MYSQL_CONFIG['host']}")
        print(f"   Usuario: {MYSQL_CONFIG['user']}")
        print(f"   Base de datos: {MYSQL_CONFIG['database']}")
        exit(1)
    
    print("\n")
    
    # Verificar tablas existentes
    tablas_existentes = verificar_tablas_existentes()
    
    # Verificar que existe la tabla factura
    if 'factura' not in tablas_existentes:
        print("❌ Error: No se encontró la tabla 'factura'")
        print("💡 Asegúrate de que tu aplicación Flask esté corriendo y haya creado las tablas")
        exit(1)
    
    print("\n")
    
    # Crear tabla medios_pago
    if crear_tabla_medios_pago():
        print("\n✅ Migración completada exitosamente")
        
        # Preguntar si insertar datos de prueba
        respuesta = input("\n¿Desea insertar datos de prueba? (s/n): ")
        if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            insertar_datos_prueba()
            
        print("\n🎉 ¡Sistema de medios de pago listo para usar en MySQL!")
        print("\n📋 Próximos pasos:")
        print("   1. Agrega el modelo MedioPago a tu app.py")
        print("   2. Reemplaza la función procesar_venta en app.py")
        print("   3. Agrega las nuevas rutas a tu app.py")
        print("   4. Agrega el modal HTML a nueva_venta.html")
        print("   5. Agrega el JavaScript a nueva_venta.html")
        print("   6. Reinicia tu aplicación Flask")
        
    else:
        print("\n❌ Error en la migración")
        
    print("=" * 60)