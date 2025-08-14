# test_mysql.py - Script para probar y arreglar la conexión MySQL

import mysql.connector
from mysql.connector import Error

def test_mysql_connection():
    """Prueba diferentes combinaciones de credenciales MySQL"""
    
    print("🔧 Probando conexión a MySQL...")
    print()
    
    # Combinaciones a probar
    credenciales = [
        # (host, user, password, database)
        ('localhost', 'pos_user', 'cl1v2', 'pos_argentina'),
        ('localhost', 'pos_user', 'pos_password', 'pos_argentina'),
        ('localhost', 'root', '', 'pos_argentina'),
        ('localhost', 'root', 'admin', 'pos_argentina'),
        ('localhost', 'root', 'root', 'pos_argentina'),
        ('127.0.0.1', 'pos_user', 'cl1v2', 'pos_argentina'),
    ]
    
    for host, user, password, database in credenciales:
        print(f"Probando: {user}@{host} con contraseña: {'***' if password else 'SIN CONTRASEÑA'}")
        
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            
            if connection.is_connected():
                print("✅ ¡CONEXIÓN EXITOSA!")
                print(f"   Host: {host}")
                print(f"   Usuario: {user}")
                print(f"   Base de datos: {database}")
                
                # Probar una consulta simple
                cursor = connection.cursor()
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"   Tablas encontradas: {len(tables)}")
                
                cursor.close()
                connection.close()
                
                return host, user, password, database
                
        except Error as e:
            print(f"❌ Error: {e}")
            print()
    
    print("❌ No se pudo conectar con ninguna combinación")
    return None

def create_mysql_user():
    """Crear el usuario pos_user desde cero"""
    print("\n🔧 Creando usuario MySQL desde cero...")
    
    # Intentar conectar como root
    root_passwords = ['', 'admin', 'root', 'password', '123456']
    
    for root_pwd in root_passwords:
        try:
            print(f"Intentando conectar como root con contraseña: {'SIN CONTRASEÑA' if not root_pwd else '***'}")
            
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=root_pwd
            )
            
            cursor = connection.cursor()
            
            print("✅ Conectado como root!")
            
            # Crear base de datos
            print("Creando base de datos...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS pos_argentina CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            # Crear usuario
            print("Creando usuario pos_user...")
            cursor.execute("DROP USER IF EXISTS 'pos_user'@'localhost'")
            cursor.execute("CREATE USER 'pos_user'@'localhost' IDENTIFIED BY 'cl1v2'")
            cursor.execute("GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print("✅ Usuario pos_user creado correctamente!")
            print("   Usuario: pos_user")
            print("   Contraseña: cl1v2")
            print("   Base de datos: pos_argentina")
            
            cursor.close()
            connection.close()
            
            return True
            
        except Error as e:
            print(f"❌ Error con root: {e}")
    
    return False

def get_mysql_info():
    """Obtiene información del servidor MySQL"""
    print("\n📊 Información del servidor MySQL:")
    
    # Probar conexión básica
    try:
        connection = mysql.connector.connect(host='localhost')
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ Versión MySQL: {version[0]}")
            
            cursor.execute("SELECT USER()")
            user_info = cursor.fetchone()
            print(f"✅ Usuario actual: {user_info[0]}")
            
            cursor.close()
            connection.close()
    except Error as e:
        print(f"❌ No se pudo obtener información: {e}")

def main():
    print("=" * 60)
    print("  SOLUCIONADOR DE CONEXIÓN MYSQL - POS ARGENTINA")
    print("=" * 60)
    print()
    
    # Paso 1: Probar conexiones existentes
    result = test_mysql_connection()
    
    if result:
        host, user, password, database = result
        print("\n✅ SOLUCIÓN ENCONTRADA:")
        print("Usa esta configuración en tu app.py:")
        print()
        print("# En la configuración por defecto, cambiar:")
        print(f"app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{user}:{password}@{host}/{database}'")
        print()
        return
    
    print("\n🔧 No se encontró conexión válida. Intentando crear usuario...")
    
    # Paso 2: Crear usuario desde cero
    if create_mysql_user():
        print("\n✅ Usuario creado. Probando conexión...")
        result = test_mysql_connection()
        
        if result:
            print("✅ ¡Problema resuelto!")
        else:
            print("❌ Aún hay problemas. Verifica MySQL manualmente.")
    else:
        print("\n❌ No se pudo crear el usuario automáticamente.")
        print("\nSoluciones manuales:")
        print("1. Abrir MySQL Workbench o línea de comandos")
        print("2. Conectar como root")
        print("3. Ejecutar estos comandos:")
        print()
        print("   CREATE DATABASE IF NOT EXISTS pos_argentina;")
        print("   CREATE USER 'pos_user'@'localhost' IDENTIFIED BY 'cl1v2';")
        print("   GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost';")
        print("   FLUSH PRIVILEGES;")
    
    # Información adicional
    get_mysql_info()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operación cancelada")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

print()
print("💡 SOLUCIONES ALTERNATIVAS:")
print()
print("OPCIÓN 1 - Usar XAMPP/WAMP:")
print("- Instalar XAMPP")
print("- Iniciar Apache y MySQL")
print("- Usuario: root, Contraseña: (vacía)")
print()
print("OPCIÓN 2 - Cambiar credenciales en app.py:")
print("- Buscar la línea SQLALCHEMY_DATABASE_URI")
print("- Cambiar por tus credenciales reales")
print()
print("OPCIÓN 3 - Usar DBeaver:")
print("- Verificar qué usuario y contraseña funcionan")
print("- Usar esas mismas credenciales en app.py")