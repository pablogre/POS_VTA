#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qr_debug_tm_m30ii.py - VERSION CON DEBUG COMPLETO
"""

print("🔧 INICIANDO GENERADOR QR CON DEBUG")
print("="*50)

# Debug paso a paso
try:
    print("🔍 Paso 1: Importando librerías...")
    
    print("   - Importando qrcode...")
    import qrcode
    try:
        print(f"   ✅ qrcode version: {qrcode.__version__}")
    except:
        print("   ✅ qrcode importado (versión no disponible)")
    
    print("   - Importando PIL...")
    from PIL import Image
    import PIL
    try:
        print(f"   ✅ Pillow version: {PIL.__version__}")
    except:
        print("   ✅ Pillow importado (versión no disponible)")
    
    print("   - Importando win32print...")
    import win32print
    print("   ✅ win32print OK")
    
    print("   - Importando otros módulos...")
    import os, sys
    from datetime import datetime
    print("   ✅ Módulos básicos OK")
    
except ImportError as e:
    print(f"❌ Error importando: {e}")
    print("💡 Ejecuta: pip install qrcode[pil] Pillow pywin32")
    input("Enter para salir...")
    sys.exit()

print("\n🔍 Paso 2: Buscando impresora...")

def buscar_impresora():
    try:
        impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
        print(f"   📄 Impresoras encontradas: {len(impresoras)}")
        
        for i, impresora in enumerate(impresoras):
            nombre = impresora[2]
            print(f"      {i+1}. {nombre}")
            if 'tm-m30ii' in nombre.lower():
                print(f"      ⭐ TM-m30II encontrada: {nombre}")
                return nombre
        
        print("   ❌ TM-m30II no encontrada")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

impresora = buscar_impresora()

if not impresora:
    print("❌ No se puede continuar sin impresora")
    input("Enter para salir...")
    sys.exit()

print("\n🔍 Paso 3: Generando QR de prueba...")

def generar_qr_test():
    try:
        print("   - Creando objeto QR...")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=2,
        )
        print("   ✅ Objeto QR creado")
        
        print("   - Agregando datos...")
        contenido = "TEST SIMPLE"
        qr.add_data(contenido)
        qr.make(fit=True)
        print("   ✅ Datos agregados")
        
        print("   - Generando imagen...")
        qr_img = qr.make_image(fill_color="black", back_color="white")
        print(f"   ✅ Imagen generada: {qr_img.size}")
        
        print("   - Convirtiendo a bitmap...")
        qr_img = qr_img.convert('1')  # 1-bit
        print("   ✅ Convertido a 1-bit")
        
        return qr_img
        
    except Exception as e:
        print(f"   ❌ Error generando QR: {e}")
        import traceback
        traceback.print_exc()
        return None

qr_imagen = generar_qr_test()

if not qr_imagen:
    print("❌ No se pudo generar QR")
    input("Enter para salir...")
    sys.exit()

print("\n🔍 Paso 4: Convirtiendo a ESC/POS...")

def convertir_a_escpos(imagen):
    try:
        print("   - Obteniendo dimensiones...")
        ancho, alto = imagen.size
        print(f"   ✅ Dimensiones: {ancho}x{alto}")
        
        print("   - Obteniendo píxeles...")
        pixels = list(imagen.getdata())
        print(f"   ✅ Píxeles obtenidos: {len(pixels)}")
        
        print("   - Creando comandos ESC/POS...")
        ESC = b'\x1B'
        GS = b'\x1D'
        
        datos = bytearray()
        datos.extend(ESC + b'@')  # Inicializar
        datos.extend(ESC + b'a\x01')  # Centrar
        datos.extend(b'=== QR DEBUG TEST ===\n\n')
        
        # Comando imagen simple
        bytes_por_linea = (ancho + 7) // 8
        print(f"   ✅ Bytes por línea: {bytes_por_linea}")
        
        datos.extend(GS + b'v0')  # Imagen raster
        datos.extend(bytes([0]))  # Modo
        datos.extend(bytes([bytes_por_linea & 0xFF, (bytes_por_linea >> 8) & 0xFF]))
        datos.extend(bytes([alto & 0xFF, (alto >> 8) & 0xFF]))
        
        print("   - Procesando líneas de imagen...")
        for y in range(alto):
            linea_bytes = []
            for x in range(0, ancho, 8):
                byte_val = 0
                for bit in range(8):
                    if x + bit < ancho:
                        pixel_idx = y * ancho + x + bit
                        if pixels[pixel_idx] == 0:  # Negro
                            byte_val |= (1 << (7 - bit))
                linea_bytes.append(byte_val)
            datos.extend(bytes(linea_bytes))
        
        datos.extend(b'\n\nQR Debug completado\n')
        datos.extend(f'Fecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'.encode('cp437'))
        datos.extend(b'=' * 30 + b'\n\n\n')
        
        print(f"   ✅ Datos ESC/POS generados: {len(datos)} bytes")
        return bytes(datos)
        
    except Exception as e:
        print(f"   ❌ Error convirtiendo: {e}")
        import traceback
        traceback.print_exc()
        return None

datos_escpos = convertir_a_escpos(qr_imagen)

if not datos_escpos:
    print("❌ No se pudo convertir a ESC/POS")
    input("Enter para salir...")
    sys.exit()

print("\n🔍 Paso 5: Enviando a impresora...")

def imprimir_debug(impresora, datos):
    try:
        print(f"   - Abriendo impresora: {impresora}")
        handle = win32print.OpenPrinter(impresora)
        print("   ✅ Impresora abierta")
        
        print("   - Iniciando trabajo...")
        job = win32print.StartDocPrinter(handle, 1, ("QR Debug", None, "RAW"))
        print(f"   ✅ Trabajo iniciado: {job}")
        
        print("   - Iniciando página...")
        win32print.StartPagePrinter(handle)
        print("   ✅ Página iniciada")
        
        print(f"   - Enviando {len(datos)} bytes...")
        bytes_written = win32print.WritePrinter(handle, datos)
        print(f"   ✅ Bytes enviados: {bytes_written}")
        
        print("   - Finalizando página...")
        win32print.EndPagePrinter(handle)
        print("   ✅ Página finalizada")
        
        print("   - Finalizando trabajo...")
        win32print.EndDocPrinter(handle)
        print("   ✅ Trabajo finalizado")
        
        print("   - Cerrando impresora...")
        win32print.ClosePrinter(handle)
        print("   ✅ Impresora cerrada")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error imprimiendo: {e}")
        import traceback
        traceback.print_exc()
        return False

print("\n⚠️ Se va a imprimir una página de prueba con QR")
respuesta = input("¿Continuar? (s/N): ").lower()

if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
    resultado = imprimir_debug(impresora, datos_escpos)
    
    if resultado:
        print("\n🎉 ¡ÉXITO!")
        print("✅ QR enviado correctamente a la impresora")
        print("📄 Verifica si se imprimió el QR en el papel")
        print("📱 Escanea el QR para verificar que contenga 'TEST SIMPLE'")
    else:
        print("\n❌ Error en la impresión")
else:
    print("❌ Impresión cancelada")

print(f"\n📋 RESUMEN DEBUG:")
print(f"   Librerías: ✅")
print(f"   Impresora: ✅ {impresora}")
print(f"   QR generado: ✅")
print(f"   ESC/POS creado: ✅ {len(datos_escpos)} bytes")
print(f"   Impresión: {'✅' if 'resultado' in locals() and resultado else '❌'}")

input("\nPresiona Enter para salir...")