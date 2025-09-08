# CERTIFICADOS AFIP

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
