#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qr_simple_tm_m30ii.py - GENERADOR QR SIMPLE PARA TM-m30II
Versión simplificada que evita errores de Pillow
Ejecutar: python qr_simple_tm_m30ii.py
"""

import os
import sys
from datetime import datetime
import win32print

print("🔧 GENERADOR QR SIMPLE - TM-m30II")
print("="*50)

# Verificar dependencias
try:
    import qrcode
    print("✅ qrcode disponible")
except ImportError:
    print("❌ Instalar: pip install qrcode[pil]")
    input("Enter para salir...")
    sys.exit()

try:
    from PIL import Image
    print("✅ Pillow disponible")
except ImportError:
    print("❌ Instalar: pip install Pillow")
    input("Enter para salir...")
    sys.exit()

class GeneradorQRSimple:
    def __init__(self):
        self.ancho_papel = 384  # Píxeles de ancho para TM-m30II
        self.impresora = self._buscar_impresora()
        
    def _buscar_impresora(self):
        """Buscar TM-m30II"""
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            for impresora in impresoras:
                nombre = impresora[2]
                if 'tm-m30ii' in nombre.lower():
                    print(f"✅ Impresora encontrada: {nombre}")
                    return nombre
            
            print("❌ TM-m30II no encontrada")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def generar_qr_simple(self, contenido):
        """Generar QR simple sin texto adicional"""
        try:
            print(f"📋 Generando QR: {contenido[:50]}...")
            
            # Crear QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,  # Tamaño más grande para mejor visibilidad
                border=4,
            )
            qr.add_data(contenido)
            qr.make(fit=True)
            
            # Crear imagen QR
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Redimensionar para ajustar al papel
            qr_size = min(280, qr_img.size[0])  # Máximo 280px de ancho
            qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
            
            # Convertir a bitmap para impresora
            return self._convertir_a_bitmap(qr_img)
            
        except Exception as e:
            print(f"❌ Error generando QR: {e}")
            return None
    
    def _convertir_a_bitmap(self, imagen):
        """Convertir imagen QR a formato bitmap ESC/POS"""
        try:
            # Convertir a 1-bit (blanco y negro)
            imagen = imagen.convert('1')
            
            ancho, alto = imagen.size
            
            # Crear comandos ESC/POS
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')  # Inicializar
            datos.extend(ESC + b'a\x01')  # Centrar
            
            # Texto antes del QR
            datos.extend(b'*** QR CODE ***\n\n')
            
            # Comando para imagen bitmap GS v 0
            bytes_por_linea = (ancho + 7) // 8
            
            datos.extend(GS + b'v0')  # Comando imagen raster
            datos.extend(bytes([0]))  # Modo normal
            datos.extend(bytes([bytes_por_linea & 0xFF, (bytes_por_linea >> 8) & 0xFF]))  # xL, xH
            datos.extend(bytes([alto & 0xFF, (alto >> 8) & 0xFF]))  # yL, yH
            
            # Convertir píxeles a bytes
            pixels = list(imagen.getdata())
            
            for y in range(alto):
                linea_bytes = []
                for x in range(0, ancho, 8):
                    byte_val = 0
                    for bit in range(8):
                        if x + bit < ancho:
                            pixel_idx = y * ancho + x + bit
                            # 0 = negro, 255 = blanco en modo '1'
                            if pixels[pixel_idx] == 0:  # Pixel negro
                                byte_val |= (1 << (7 - bit))
                    linea_bytes.append(byte_val)
                
                datos.extend(bytes(linea_bytes))
            
            # Texto después del QR
            datos.extend(ESC + b'a\x00')  # Alinear izquierda
            datos.extend(f'\nFecha: {datetime.now().strftime("%d/%m/%Y %H:%M")}\n'.encode('cp437'))
            datos.extend(b'QR generado correctamente\n')
            datos.extend(b'=' * 40 + b'\n\n\n')
            
            return bytes(datos)
            
        except Exception as e:
            print(f"❌ Error convirtiendo bitmap: {e}")
            return None
    
    def imprimir_qr(self, datos_qr):
        """Imprimir QR en TM-m30II"""
        if not self.impresora:
            print("❌ Impresora no disponible")
            return False
        
        if not datos_qr:
            print("❌ No hay datos para imprimir")
            return False
        
        try:
            print("🖨️ Enviando QR a impresora...")
            
            handle = win32print.OpenPrinter(self.impresora)
            job = win32print.StartDocPrinter(handle, 1, ("QR Simple", None, "RAW"))
            win32print.StartPagePrinter(handle)
            bytes_written = win32print.WritePrinter(handle, datos_qr)
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)
            
            print(f"✅ QR enviado: {bytes_written} bytes")
            return True
            
        except Exception as e:
            print(f"❌ Error imprimiendo: {e}")
            return False
    
    def generar_qr_arca(self, cuit, tipo_comprobante, numero, importe, fecha=None):
        """Generar QR específico para ARCA"""
        if not fecha:
            fecha = datetime.now().strftime('%Y-%m-%d')
        
        url_arca = f"https://www.arca.gob.ar/fe/qr/?p={cuit}&p=3&p={tipo_comprobante}&p={numero}&p={importe}&p={fecha}"
        
        print(f"📋 QR ARCA:")
        print(f"   CUIT: {cuit}")
        print(f"   Tipo: {tipo_comprobante}")
        print(f"   Número: {numero}")
        print(f"   Importe: ${importe}")
        
        return self.generar_qr_simple(url_arca)

def main():
    """Función principal"""
    generador = GeneradorQRSimple()
    
    if not generador.impresora:
        print("❌ No se encontró impresora TM-m30II")
        input("Enter para salir...")
        return
    
    while True:
        print("\n" + "="*50)
        print("OPCIONES:")
        print("1. QR de prueba simple")
        print("2. QR de ARCA")
        print("3. QR personalizado")
        print("0. Salir")
        
        opcion = input("\nSelecciona opción: ").strip()
        
        if opcion == "0":
            break
        elif opcion == "1":
            print("\n🧪 Generando QR de prueba...")
            datos = generador.generar_qr_simple("HOLA MUNDO - TEST TM-m30II")
            if datos:
                if generador.imprimir_qr(datos):
                    print("🎉 ¡QR de prueba impreso correctamente!")
                    print("Si ves un código QR en el papel, ¡funciona!")
            
        elif opcion == "2":
            print("\n📋 DATOS PARA QR DE ARCA:")
            cuit = input("CUIT (ej: 20203852100): ").strip()
            tipo = input("Tipo comprobante (ej: 11): ").strip()
            numero = input("Número (ej: 1): ").strip()
            importe = input("Importe (ej: 100.00): ").strip()
            
            if cuit and tipo and numero and importe:
                datos = generador.generar_qr_arca(cuit, tipo, numero, importe)
                if datos:
                    if generador.imprimir_qr(datos):
                        print("🎉 ¡QR de ARCA impreso correctamente!")
            else:
                print("❌ Todos los campos son obligatorios")
                
        elif opcion == "3":
            texto = input("\nTexto para QR: ").strip()
            if texto:
                datos = generador.generar_qr_simple(texto)
                if datos:
                    if generador.imprimir_qr(datos):
                        print("🎉 ¡QR personalizado impreso correctamente!")
            else:
                print("❌ Debe ingresar texto")
        else:
            print("❌ Opción inválida")
    
    print("\n✅ ¡Gracias por usar el generador!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Enter para salir...")