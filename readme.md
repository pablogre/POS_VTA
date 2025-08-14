# Sistema POS Argentina 🇦🇷

Sistema de Punto de Venta completo para Argentina con integración ARCA/AFIP, desarrollado en Python Flask con MySQL.

## ✨ Características

- 🏪 **Punto de Venta completo** - Gestión de ventas, productos y clientes
- 🧾 **Facturación Electrónica** - Integración con ARCA/AFIP para autorización automática
- 📊 **Dashboard** - Resumen de ventas y estadísticas
- 👥 **Gestión de Clientes** - Base de datos completa de clientes
- 📦 **Control de Inventario** - Gestión de productos y stock
- 🖨️ **Impresión** - Facturas listas para imprimir
- 🔐 **Sistema de Usuarios** - Control de acceso y roles
- 📱 **Responsive** - Compatible con dispositivos móviles

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.8 o superior
- MySQL 5.7 o superior
- Certificados digitales AFIP (opcional para pruebas)

### 1. Clonar o descargar el proyecto

```bash
# Crear directorio del proyecto
mkdir pos-argentina
cd pos-argentina

# Copiar todos los archivos del proyecto aquí
```

### 2. Ejecutar el instalador

```bash
python install.py
```

El instalador automáticamente:
- ✅ Verifica requisitos del sistema
- ✅ Instala dependencias de Python
- ✅ Configura la base de datos MySQL
- ✅ Crea las tablas necesarias
- ✅ Configura el usuario administrador
- ✅ Genera archivo de configuración

### 3. Iniciar el sistema

```bash
python run.py
```

### 4. Acceder al sistema

- **URL:** http://localhost:5000
- **Usuario:** admin
- **Contraseña:** admin123

## 📋 Configuración Manual

### Base de Datos MySQL

Si prefieres configurar MySQL manualmente:

```sql
-- Crear base de datos
CREATE DATABASE pos_argentina CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario
CREATE USER 'pos_user'@'localhost' IDENTIFIED BY 'pos_password';
GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost';
FLUSH PRIVILEGES;

-- Ejecutar script de tablas
mysql -u pos_user -p pos_argentina < setup_database.sql
```

### Variables de Entorno

Crear archivo `.env`:

```env
SECRET_KEY=tu_clave_secreta_aqui
MYSQL_HOST=localhost
MYSQL_USER=pos_user
MYSQL_PASSWORD=pos_password
MYSQL_DATABASE=pos_argentina
```

## 🔐 Configuración ARCA/AFIP

### 1. Obtener Certificados Digitales

1. Ingresar a [AFIP](https://auth.afip.gob.ar)
2. Ir a "Administrador de Relaciones de Clave Fiscal"
3. Generar certificado para "Facturación Electrónica"
4. Descargar certificado (.crt) y clave privada (.key)

### 2. Configurar Certificados

Colocar en la carpeta `certificados/`:
- `certificado.crt` - Certificado digital
- `private.key` - Clave privada

### 3. Configurar Datos de Empresa

Editar `config_local.py`:

```python
class ARCAConfig:
    CUIT = '20123456789'  # ⚠️ TU CUIT AQUÍ
    PUNTO_VENTA = 1       # ⚠️ TU PUNTO DE VENTA
    RAZON_SOCIAL = 'MI EMPRESA SRL'  # ⚠️ TU RAZÓN SOCIAL
    
    # Para producción, cambiar a False
    USE_HOMOLOGACION = True
```

### 4. Tipos de Comprobante Soportados

- **Factura A** - Para Responsables Inscriptos
- **Factura B** - Para Monotributistas y Exentos  
- **Factura C** - Para Consumidores Finales

## 📁 Estructura del Proyecto

```
pos-argentina/
├── app.py                 # Aplicación principal Flask
├── config.py             # Configuración base
├── config_local.py       # Configuración local (generada)
├── requirements.txt      # Dependencias Python
├── setup_database.sql    # Script de base de datos
├── install.py           # Instalador automático
├── run.py               # Script para ejecutar
├── README.md            # Esta documentación
├── templates/           # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── nueva_venta.html
│   ├── facturas.html
│   ├── productos.html
│   ├── clientes.html
│   └── factura_detalle.html
├── certificados/        # Certificados AFIP
│   ├── certificado.crt
│   └── private.key
├── cache/               # Cache de tokens AFIP
└── logs/                # Archivos de log
```

## 🛠️ Uso del Sistema

### Dashboard Principal

- Resumen de ventas del día
- Estadísticas de productos
- Accesos rápidos a funciones principales

### Nueva Venta

1. Seleccionar cliente
2. Agregar productos (por código o nombre)
3. Verificar totales
4. Procesar venta
5. El sistema automáticamente:
   - Genera número de factura
   - Solicita autorización a AFIP
   - Actualiza stock
   - Permite imprimir

### Gestión de Productos

- Crear/editar productos
- Control de stock
- Configuración de precios e IVA
- Categorización

### Gestión de Clientes

- Registro de clientes
- Tipos de documento (DNI, CUIT, etc.)
- Condición ante el IVA
- Historial de compras

### Facturas

- Listado de todas las facturas
- Estados: Autorizada, Error AFIP, Pendiente
- Visualización e impresión
- Números CAE y fechas de vencimiento

## 🔧 Personalización

### Cambiar Datos de Empresa

Editar en `config_local.py` o directamente en la base de datos:

```sql
UPDATE configuracion SET valor = 'MI EMPRESA SRL' WHERE clave = 'empresa_razon_social';
UPDATE configuracion SET valor = '20123456789' WHERE clave = 'empresa_cuit';
```

### Agregar Nuevos Usuarios

```python
from werkzeug.security import generate_password_hash
from app import db, Usuario

nuevo_usuario = Usuario(
    username='vendedor1',
    password_hash=generate_password_hash('contraseña123'),
    nombre='Juan Pérez',
    rol='vendedor'
)
db.session.add(nuevo_usuario)
db.session.commit()
```

### Personalizar Templates

Los templates HTML están en la carpeta `templates/` y utilizan Bootstrap 5. Puedes modificarlos según tus necesidades.

## 🚨 Solución de Problemas

### Error de Conexión MySQL

```bash
# Verificar que MySQL esté ejecutándose
sudo systemctl status mysql

# Verificar usuario y permisos
mysql -u pos_user -p
```

### Error de Certificados AFIP

- Verificar que los archivos estén en `certificados/`
- Comprobar que el CUIT coincida con el certificado
- Verificar fechas de vencimiento del certificado

### Error de Autorización AFIP

- Verificar conexión a internet
- Comprobar que el punto de venta esté habilitado
- Revisar logs en la carpeta `logs/`

### Puerto 5000 en Uso

```bash
# Cambiar puerto en run.py
app.run(port=8080)  # Usar puerto 8080
```

## 📊 Base de Datos

### Tablas Principales

- `usuario` - Usuarios del sistema
- `cliente` - Clientes registrados
- `producto` - Productos disponibles
- `factura` - Facturas emitidas
- `detalle_factura` - Items de cada factura
- `movimiento_stock` - Movimientos de inventario
- `configuracion` - Configuración del sistema

### Respaldos

```bash
# Crear respaldo
mysqldump -u pos_user -p pos_argentina > backup_$(date +%Y%m%d).sql

# Restaurar respaldo
mysql -u pos_user -p pos_argentina < backup_20241201.sql
```

## 🔒 Seguridad

### Recomendaciones para Producción

1. **Cambiar contraseñas por defecto**
2. **Usar HTTPS** (certificado SSL)
3. **Configurar firewall** (solo puertos necesarios)
4. **Backups regulares** de la base de datos
5. **Actualizar dependencias** regularmente
6. **Logs de auditoría** para todas las operaciones

### Configuración HTTPS

```python
# En app.py para producción
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=443,
        ssl_context='adhoc',  # O usar certificados reales
        debug=False
    )
```

## 📚 Documentación Adicional

- [Documentación AFIP Web Services](https://www.afip.gob.ar/ws/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [MySQL Documentation](https://dev.mysql.com/doc/)
- [Bootstrap 5](https://getbootstrap.com/docs/5.1/)

## 🤝 Soporte

Para soporte técnico o reportar problemas:

1. Verificar los logs en `logs/`
2. Revisar la configuración en `config_local.py`
3. Comprobar estado de servicios (MySQL, conexión AFIP)

## 📝 Licencia

Este proyecto es de código abierto. Puedes modificarlo y distribuirlo según tus necesidades.

## 🚀 Próximas Funcionalidades

- [ ] Reportes avanzados
- [ ] Integración con medios de pago
- [ ] App móvil
- [ ] API REST
- [ ] Integración con sistemas contables
- [ ] Facturación de servicios recurrentes

---

**¡Listo para facturar en Argentina! 🇦🇷✨**