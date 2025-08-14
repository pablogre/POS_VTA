#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qr_imagen_tm_m30ii.py - GENERAR QR COMO IMAGEN PARA TM-m30II
Método alternativo cuando comandos QR no funcionan
Ejecutar: python qr_imagen_tm_m30ii.py
"""

import os
import sys
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import qrcode
import win32print

print("🔧 GENERADOR QR COMO IMAGEN - TM-m30II")
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
    from PIL import Image, ImageDraw, ImageFont
    print("✅ Pillow disponible")
except ImportError:
    print("❌ Instalar: pip install Pillow")
    input("Enter para salir...")
    sys.exit()

try:
    import win32print
    print("✅ win32print disponible")
except ImportError:
    print("❌ Instalar: pip install pywin32")
    input("Enter para salir...")
    sys.exit()

class GeneradorQRImagen:
    def __init__(self):
        self.ancho_papel = 384  # Píxeles de ancho para TM-m30II (48mm * 8 dots/mm)
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
    
    def generar_qr_arca(self, cuit, tipo_comprobante, numero, importe, fecha=None):
        """Generar QR específico para ARCA"""
        if not fecha:
            fecha = datetime.now().strftime('%Y-%m-%d')
        
        # URL de ARCA
        url_arca = f"https://www.arca.gob.ar/fe/qr/?p={cuit}&p=3&p={tipo_comprobante}&p={numero}&p={importe}&p={fecha}"
        
        print(f"📋 Generando QR ARCA:")
        print(f"   CUIT: {cuit}")
        print(f"   Tipo: {tipo_comprobante}")
        print(f"   Número: {numero}")
        print(f"   Importe: ${importe}")
        print(f"   Fecha: {fecha}")
        
        return self._generar_ticket_con_qr(url_arca, {
            'titulo': '*** COMPROBANTE FISCAL ***',
            'cuit': f'CUIT: {cuit}',
            'tipo': f'Tipo: {tipo_comprobante}',
            'numero': f'Número: {numero}',
            'importe': f'Importe: ${importe}',
            'fecha': f'Fecha: {fecha}'
        })
    
    def generar_qr_personalizado(self, texto, titulo="QR PERSONALIZADO"):
        """Generar QR con texto personalizado"""
        print(f"📋 Generando QR: {texto[:50]}...")
        
        return self._generar_ticket_con_qr(texto, {
            'titulo': f'*** {titulo} ***',
            'contenido': texto[:100] + ('...' if len(texto) > 100 else '')
        })
    
    def _generar_ticket_con_qr(self, contenido_qr, info_texto):
        """Generar imagen de ticket completo con QR"""
        try:
            # Crear QR
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,  # Tamaño de cada cuadrito
                border=2,
            )
            qr.add_data(contenido_qr)
            qr.make(fit=True)
            
            # Crear imagen QR
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Calcular dimensiones del ticket
            qr_size = qr_img.size[0]
            
            # Crear imagen del ticket completo
            altura_texto = 150  # Espacio para texto
            altura_total = altura_texto + qr_size + 50  # Padding
            
            ticket = Image.new('1', (self.ancho_papel, altura_total), 1)  # 1 = blanco
            draw = ImageDraw.Draw(ticket)
            
            # Intentar cargar fuente, si no usar por defecto
            try:
                fuente = ImageFont.truetype("arial.ttf", 14)
                fuente_pequena = ImageFont.truetype("arial.ttf", 10)
            except:
                fuente = ImageFont.load_default()
                fuente_pequena = ImageFont.load_default()
            
            # Dibujar texto
            y_pos = 10
            for key, valor in info_texto.items():
                if key == 'titulo':
                    # Centrar título
                    try:
                        bbox = draw.textbbox((0, 0), valor, font=fuente)
                        ancho_texto = bbox[2] - bbox[0]
                    except:
                        # Fallback para versiones antiguas de Pillow
                        ancho_texto = len(valor) * 8
                    
                    x_centro = (self.ancho_papel - ancho_texto) // 2
                    draw.text((x_centro, y_pos), valor, fill=0, font=fuente)
                    y_pos += 25
                    # Línea separadora
                    draw.line([(20, y_pos), (self.ancho_papel - 20, y_pos)], fill=0, width=1)
                    y_pos += 15
                else:
                    draw.text((20, y_pos), valor, fill=0, font=fuente_pequena)
                    y_pos += 18
            
            # Centrar y pegar QR
            x_qr = (self.ancho_papel - qr_size) // 2
            ticket.paste(qr_img, (x_qr, altura_texto))
            
            # Convertir a formato bitmap para impresora
            return self._convertir_a_bitmap_impresora(ticket)
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            return None
    
    def _convertir_a_bitmap_impresora(self, imagen):
        """Convertir imagen a formato bitmap ESC/POS"""
        try:
            # Redimensionar si es necesario
            if imagen.size[0] != self.ancho_papel:
                nuevo_alto = int(imagen.size[1] * self.ancho_papel / imagen.size[0])
                imagen = imagen.resize((self.ancho_papel, nuevo_alto), Image.Resampling.LANCZOS)
            
            # Convertir a bitmap 1-bit
            imagen = imagen.convert('1')
            
            # Obtener datos de píxeles
            ancho, alto = imagen.size
            pixels = list(imagen.getdata())
            
            # Crear comandos ESC/POS para imagen
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')  # Inicializar
            datos.extend(ESC + b'a\x01')  # Centrar
            
            # Comando para imagen bitmap
            # GS v 0: Imprimir imagen raster
            bytes_por_linea = (ancho + 7) // 8  # Redondear hacia arriba
            
            # Encabezado del comando
            datos.extend(GS + b'v0')  # Comando imagen
            datos.extend(bytes([0]))  # m = 0 (normal)
            datos.extend(bytes([bytes_por_linea & 0xFF, (bytes_por_linea >> 8) & 0xFF]))  # xL, xH
            datos.extend(bytes([alto & 0xFF, (alto >> 8) & 0xFF]))  # yL, yH
            
            # Convertir píxeles a bytes
            for y in range(alto):
                linea_bytes = []
                for x in range(0, ancho, 8):
                    byte_val = 0
                    for bit in range(8):
                        if x + bit < ancho:
                            pixel_idx = y * ancho + x + bit
                            if pixels[pixel_idx] == 0:  # Pixel negro
                                byte_val |= (1 << (7 - bit))
                    linea_bytes.append(byte_val)
                
                datos.extend(bytes(linea_bytes))
            
            # Saltos de línea finales
            datos.extend(b'\n\n\n')
            
            return bytes(datos)
            
        except Exception as e:
            print(f"❌ Error convirtiendo bitmap: {e}")
            return None
    
    def imprimir_imagen(self, datos_imagen):
        """Imprimir imagen en TM-m30II"""
        if not self.impresora:
            print("❌ Impresora no disponible")
            return False
        
        if not datos_imagen:
            print("❌ No hay datos para imprimir")
            return False
        
        try:
            print("🖨️ Enviando imagen a impresora...")
            
            handle = win32print.OpenPrinter(self.impresora)
            job = win32print.StartDocPrinter(handle, 1, ("QR Imagen", None, "RAW"))
            win32print.StartPagePrinter(handle)
            bytes_written = win32print.WritePrinter(handle, datos_imagen)
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            win32print.ClosePrinter(handle)
            
            print(f"✅ Imagen enviada: {bytes_written} bytes")
            return True
            
        except Exception as e:
            print(f"❌ Error imprimiendo: {e}")
            return False

def main():
    """Función principal"""
    print("\n🎯 GENERADOR QR COMO IMAGEN")
    
    generador = GeneradorQRImagen()
    
    if not generador.impresora:
        print("❌ No se encontró impresora TM-m30II")
        input("Enter para salir...")
        return
    
    while True:
        print("\n" + "="*50)
        print("OPCIONES:")
        print("1. QR de ARCA (Factura Electrónica)")
        print("2. QR personalizado")
        print("3. QR de prueba simple")
        print("0. Salir")
        
        opcion = input("\nSelecciona opción: ").strip()
        
        if opcion == "0":
            break
        elif opcion == "1":
            print("\n📋 DATOS PARA QR DE ARCA:")
            cuit = input("CUIT (ej: 20203852100): ").strip()
            tipo = input("Tipo comprobante (ej: 11): ").strip()
            numero = input("Número (ej: 1): ").strip()
            importe = input("Importe (ej: 100.00): ").strip()
            
            if cuit and tipo and numero and importe:
                datos = generador.generar_qr_arca(cuit, tipo, numero, importe)
                if datos:
                    generador.imprimir_imagen(datos)
            else:
                print("❌ Todos los campos son obligatorios")
                
        elif opcion == "2":
            texto = input("\nTexto para QR: ").strip()
            titulo = input("Título (opcional): ").strip() or "QR PERSONALIZADO"
            
            if texto:
                datos = generador.generar_qr_personalizado(texto, titulo)
                if datos:
                    generador.imprimir_imagen(datos)
            else:
                print("❌ Debe ingresar texto")
                
        elif opcion == "3":
            print("\n🧪 Generando QR de prueba...")
            datos = generador.generar_qr_personalizado("HOLA MUNDO - TEST TM-m30II", "PRUEBA")
            if datos:
                generador.imprimir_imagen(datos)
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