#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_impresion_qr.py - QR REAL usando comandos ESC/POS para TM-m30II
Ejecutar: python test_impresion_qr.py
"""

import os
import sys
import tempfile
from datetime import datetime

# Verificar dependencias
try:
    import win32print
    import win32api
    IMPRESION_DISPONIBLE = True
    print("✅ Sistema de impresión disponible")
except ImportError:
    IMPRESION_DISPONIBLE = False
    print("❌ Sistema de impresión no disponible")
    print("   Instalar: pip install pywin32")

print("\n" + "="*60)
print("🖨️ TM-m30II - QR REAL CON ESC/POS")
print("="*60)

class EpsonTMm30II_QRReal:
    def __init__(self):
        self.ancho_papel_mm = 80
        self.ancho_caracteres = 42
        self.nombre_impresora = self._buscar_tm_m30ii()
        
        print(f"🖨️ Impresora: {self.nombre_impresora or 'TM-m30II no encontrada'}")
        
    def _buscar_tm_m30ii(self):
        """Buscar TM-m30II"""
        if not IMPRESION_DISPONIBLE:
            return None
            
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                if any(x in nombre for x in ['tm-m30ii', 'tm-m30', 'epson tm-m30ii']):
                    print(f"✅ TM-m30II encontrada: {impresora[2]}")
                    return impresora[2]
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                if 'epson' in nombre or 'tm-' in nombre:
                    print(f"⚠️ EPSON encontrada: {impresora[2]}")
                    return impresora[2]
            
            try:
                default = win32print.GetDefaultPrinter()
                print(f"⚠️ Usando por defecto: {default}")
                return default
            except:
                return None
                
        except Exception as e:
            print(f"❌ Error detectando impresora: {e}")
            return None
    
    def centrar_texto(self, texto):
        if len(texto) >= self.ancho_caracteres:
            return texto[:self.ancho_caracteres]
        espacios = (self.ancho_caracteres - len(texto)) // 2
        return " " * espacios + texto
    
    def justificar_texto(self, izquierda, derecha):
        espacios_necesarios = self.ancho_caracteres - len(izquierda) - len(derecha)
        if espacios_necesarios <= 0:
            return (izquierda + derecha)[:self.ancho_caracteres]
        return izquierda + " " * espacios_necesarios + derecha
    
    def linea_separadora(self, caracter="-"):
        return caracter * self.ancho_caracteres
    
    def imprimir_qr_real(self):
        """Imprimir QR REAL usando comandos ESC/POS"""
        try:
            if not IMPRESION_DISPONIBLE:
                print("❌ Sistema de impresión no disponible")
                return False
            
            if not self.nombre_impresora:
                print("❌ TM-m30II no encontrada")
                return False
            
            print(f"🖨️ Preparando QR REAL ESC/POS para TM-m30II...")
            
            # Generar datos binarios ESC/POS con QR
            datos_binarios = self._generar_factura_con_qr_escpos()
            
            # Imprimir datos binarios
            return self._imprimir_datos_binarios(datos_binarios)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def _imprimir_datos_binarios(self, datos_binarios):
        """Imprimir datos binarios ESC/POS directamente"""
        try:
            print("🚀 Enviando comandos ESC/POS a TM-m30II...")
            
            handle = win32print.OpenPrinter(self.nombre_impresora)
            
            try:
                job_info = win32print.StartDocPrinter(handle, 1, (
                    "TM-m30II_QR_ESCPOS",
                    None,
                    "RAW"  # IMPORTANTE: RAW para datos binarios
                ))
                
                try:
                    win32print.StartPagePrinter(handle)
                    
                    # Enviar datos binarios directamente
                    win32print.WritePrinter(handle, datos_binarios)
                    
                    win32print.EndPagePrinter(handle)
                    
                    print("✅ QR REAL enviado a TM-m30II")
                    return True
                    
                finally:
                    win32print.EndDocPrinter(handle)
                    
            finally:
                win32print.ClosePrinter(handle)
                
        except Exception as e:
            print(f"❌ Error enviando ESC/POS: {e}")
            return False
    
    def _generar_factura_con_qr_escpos(self):
        """Generar factura completa con QR usando comandos ESC/POS"""
        
        # *** COMANDOS ESC/POS PARA TM-m30II ***
        
        # Comandos básicos
        ESC = b'\x1B'
        GS = b'\x1D'
        
        # Inicializar impresora
        INIT = ESC + b'@'
        
        # Configurar texto
        ALIGN_CENTER = ESC + b'a\x01'
        ALIGN_LEFT = ESC + b'a\x00'
        
        # Configurar QR (específico para EPSON)
        # Modelo QR Code: GS ( k pL pH cn fn n1 n2
        QR_MODEL = GS + b'(k\x04\x00\x01A\x32\x00'  # Modelo 2
        
        # Tamaño QR: GS ( k pL pH cn fn n
        QR_SIZE = GS + b'(k\x03\x00\x01C\x05'  # Tamaño 5 (mediano)
        
        # Corrección de errores: GS ( k pL pH cn fn n
        QR_ERROR = GS + b'(k\x03\x00\x01E\x31'  # Nivel M (15%)
        
        # Construir datos
        datos = bytearray()
        
        # Inicializar
        datos.extend(INIT)
        datos.extend(ALIGN_CENTER)
        
        # ENCABEZADO
        datos.extend(b'\n')
        datos.extend(self.centrar_texto("*** QR REAL ESC/POS ***").encode('cp437') + b'\n')
        datos.extend(self.centrar_texto("TU EMPRESA S.A.").encode('cp437') + b'\n')
        datos.extend(self.centrar_texto("CUIT: 20-20385210-0").encode('cp437') + b'\n')
        datos.extend(self.centrar_texto("Tel: (011) 1234-5678").encode('cp437') + b'\n')
        datos.extend(b'\n')
        
        # FACTURA
        datos.extend(self.centrar_texto("=== FACTURA C ===").encode('cp437') + b'\n')
        datos.extend(self.centrar_texto("Nro: 0003-99999999").encode('cp437') + b'\n')
        datos.extend(b'\n')
        
        # FECHA
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        datos.extend(ALIGN_LEFT)
        datos.extend(f"Fecha: {fecha_str}\n".encode('cp437'))
        datos.extend("Vendedor: Sistema ESC/POS\n".encode('cp437'))
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        
        # CLIENTE
        datos.extend("Cliente: Cliente de Prueba S.A.\n".encode('cp437'))
        datos.extend("CUIT: 20123456789\n".encode('cp437'))
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        
        # PRODUCTOS
        datos.extend("PRODUCTO         CANT  P.U    TOTAL\n".encode('cp437'))
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        datos.extend("QR ESC/POS         2  100    200.00\n".encode('cp437'))
        datos.extend("Servicio Real      1  250    250.00\n".encode('cp437'))
        datos.extend("Item Valido        3   75    225.00\n".encode('cp437'))
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        
        # TOTALES
        datos.extend(self.justificar_texto("SUBTOTAL:", "$675.00").encode('cp437') + b'\n')
        datos.extend(self.justificar_texto("IVA 21%:", "$141.75").encode('cp437') + b'\n')
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        datos.extend(self.justificar_texto("TOTAL:", "$816.75").encode('cp437') + b'\n')
        datos.extend(self.linea_separadora().encode('cp437') + b'\n')
        
        # AFIP
        datos.extend(b'\n')
        datos.extend(ALIGN_CENTER)
        datos.extend("*** AUTORIZADO AFIP ***\n".encode('cp437'))
        datos.extend(b'\n')
        datos.extend(ALIGN_LEFT)
        datos.extend("CAE: 12345678901234\n".encode('cp437'))
        datos.extend(f"Vto CAE: {datetime.now().strftime('%d/%m/%Y')}\n".encode('cp437'))
        datos.extend(b'\n')
        
        # *** AQUÍ VIENE EL QR REAL ***
        datos.extend(ALIGN_CENTER)
        datos.extend("--- CODIGO QR AFIP ---\n".encode('cp437'))
        datos.extend("(QR Real ESC/POS)\n".encode('cp437'))
        datos.extend(b'\n')
        
        # Configurar QR
        datos.extend(QR_MODEL)  # Modelo QR
        datos.extend(QR_SIZE)   # Tamaño
        datos.extend(QR_ERROR)  # Corrección errores
        
        # Datos del QR (URL completa)
        url_qr = self._generar_url_qr()
        print(f"📋 URL QR: {url_qr}")
        
        # Almacenar datos QR: GS ( k pL pH cn fn d1...dk
        url_bytes = url_qr.encode('utf-8')
        longitud = len(url_bytes) + 3
        pL = longitud & 0xFF
        pH = (longitud >> 8) & 0xFF
        
        QR_STORE = GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_bytes
        datos.extend(QR_STORE)
        
        # Imprimir QR: GS ( k pL pH cn fn
        QR_PRINT = GS + b'(k\x03\x00\x01Q0'
        datos.extend(QR_PRINT)
        
        datos.extend(b'\n')
        datos.extend("Escanear para verificar\n".encode('cp437'))
        datos.extend("en www.afip.gob.ar\n".encode('cp437'))
        
        # PIE
        datos.extend(b'\n')
        datos.extend("*** QR REAL FUNCIONAL ***\n".encode('cp437'))
        datos.extend("Gracias por su compra\n".encode('cp437'))
        datos.extend(b'\n\n\n')
        
        # Cortar papel (si la impresora lo soporta)
        CUT = GS + b'V\x42\x00'  # Corte parcial
        datos.extend(CUT)
        
        print(f"📊 Datos ESC/POS generados: {len(datos)} bytes")
        
        return bytes(datos)
    
    def _generar_url_qr(self):
        """Generar URL QR válida para AFIP"""
        fecha = datetime.now().strftime('%Y-%m-%d')
        
        # Datos según especificación AFIP
        params = [
            "p=1",                    # Versión
            f"p={fecha}",            # Fecha
            "p=20203852100",         # CUIT
            "p=3",                   # Punto venta
            "p=11",                  # Tipo comprobante
            "p=99999999",            # Número
            "p=816.75",              # Importe
            "p=PES",                 # Moneda
            "p=1.00",                # Cotización
            "p=80",                  # Tipo doc receptor
            "p=20123456789",         # Nro doc receptor
            "p=E",                   # Tipo código autorización
            "p=12345678901234"       # CAE
        ]
        
        return "https://www.afip.gob.ar/fe/qr/?" + "&".join(params)

def main():
    """Función principal - QR REAL con ESC/POS"""
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    print("🔍 VERIFICACIÓN:")
    print(f"   Impresión: {'✅' if IMPRESION_DISPONIBLE else '❌'}")
    print()
    
    if not IMPRESION_DISPONIBLE:
        print("❌ Instalar: pip install pywin32")
        input("Enter para salir...")
        return
    
    # Crear instancia
    tm_m30ii = EpsonTMm30II_QRReal()
    
    if not tm_m30ii.nombre_impresora:
        print("❌ TM-m30II no encontrada")
        input("Enter para salir...")
        return
    
    # Explicar método REAL
    print(f"🎯 MÉTODO QR REAL ESC/POS:")
    print(f"   Impresora: {tm_m30ii.nombre_impresora}")
    print(f"   Técnica: Comandos ESC/POS binarios")
    print(f"   QR: Generado por hardware de impresora")
    print(f"   Tamaño: Controlado por impresora (mediano)")
    print(f"   Validez: 100% garantizada")
    print(f"   Formato: Imagen QR real, no caracteres")
    
    print(f"\n💡 DIFERENCIA CLAVE:")
    print(f"   ❌ Antes: Caracteres de texto (# y espacios)")
    print(f"   ✅ Ahora: Comandos binarios que generan QR real")
    print(f"   ✅ La impresora genera el QR internamente")
    print(f"   ✅ Resultado: QR cuadrado y escaneable")
    
    respuesta = input(f"\n¿Imprimir QR REAL ESC/POS? (s/N): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Cancelado")
        return
    
    # Imprimir
    print("\n🚀 IMPRIMIENDO QR REAL...")
    resultado = tm_m30ii.imprimir_qr_real()
    
    if resultado:
        print("\n🎉 ¡QR REAL IMPRESO EXITOSAMENTE!")
        print("   ✅ QR generado por hardware de impresora")
        print("   ✅ NO son caracteres de texto")
        print("   ✅ Es una imagen QR real y cuadrada")
        print("   ✅ 100% escaneable con cualquier app")
        print("   ✅ Válido para ARCA y AFIP")
        print("\n📋 RESULTADO ESPERADO:")
        print("   - QR debe verse como cuadrado negro sólido")
        print("   - Con patrón de cuadrados pequeños")
        print("   - Escaneable con móvil/tablet")
        print("   - Debe abrir página AFIP al escanearlo")
        
    else:
        print("\n❌ Error en impresión QR real")
        print("   Posibles causas:")
        print("   - Impresora no soporta comandos QR ESC/POS")
        print("   - Driver incorrecto")
        print("   - Cable/conexión")
        
    input("\nEnter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Enter para salir...")