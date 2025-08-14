#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico_tm_m30ii.py - DIAGNÓSTICO COMPLETO y SOLUCIONES MÚLTIPLES
Ejecutar: python diagnostico_tm_m30ii.py
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

print("\n" + "="*60)
print("🔧 DIAGNÓSTICO COMPLETO TM-m30II")
print("="*60)

class DiagnosticoTMm30II:
    def __init__(self):
        self.ancho_caracteres = 42
        self.nombre_impresora = self._buscar_tm_m30ii()
        
    def _buscar_tm_m30ii(self):
        """Buscar TM-m30II y obtener información"""
        if not IMPRESION_DISPONIBLE:
            return None
            
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            
            print("🖨️ IMPRESORAS DETECTADAS:")
            for i, impresora in enumerate(impresoras, 1):
                nombre = impresora[2]
                print(f"   {i}. {nombre}")
                
                # Verificar si es TM-m30II
                if any(x in nombre.lower() for x in ['tm-m30ii', 'tm-m30', 'epson tm-m30ii']):
                    print(f"      ⭐ TM-m30II ENCONTRADA")
                    return nombre
            
            # Si no encuentra específica, usar la primera EPSON
            for impresora in impresoras:
                nombre = impresora[2].lower()
                if 'epson' in nombre or 'tm-' in nombre:
                    print(f"      ⚠️ EPSON encontrada: {impresora[2]}")
                    return impresora[2]
            
            # Usar por defecto
            try:
                default = win32print.GetDefaultPrinter()
                print(f"   📌 Por defecto: {default}")
                return default
            except:
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def diagnostico_completo(self):
        """Ejecutar diagnóstico completo"""
        print(f"\n📋 DIAGNÓSTICO INICIADO")
        print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if not self.nombre_impresora:
            print("❌ NO SE ENCONTRÓ IMPRESORA")
            return False
        
        print(f"🎯 IMPRESORA SELECCIONADA: {self.nombre_impresora}")
        
        # Test 1: Imprimir texto básico
        print(f"\n🧪 TEST 1: Texto básico")
        if self._test_texto_basico():
            print("✅ Texto básico: OK")
        else:
            print("❌ Texto básico: FALLO")
            return False
        
        # Test 2: Comandos ESC/POS básicos
        print(f"\n🧪 TEST 2: Comandos ESC/POS básicos")
        if self._test_escpos_basico():
            print("✅ ESC/POS básico: OK")
        else:
            print("❌ ESC/POS básico: FALLO")
        
        # Test 3: QR con diferentes comandos
        print(f"\n🧪 TEST 3: Múltiples comandos QR")
        self._test_multiples_qr()
        
        # Test 4: Información del driver
        print(f"\n🧪 TEST 4: Información del driver")
        self._test_driver_info()
        
        return True
    
    def _test_texto_basico(self):
        """Test de texto básico"""
        try:
            contenido = f"""
*** TEST TEXTO BASICO ***
TM-m30II Funcionando
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
----------------------------------------
Si ves esto, la impresora funciona
----------------------------------------



"""
            return self._imprimir_contenido(contenido.encode('cp437'))
        except Exception as e:
            print(f"Error test básico: {e}")
            return False
    
    def _test_escpos_basico(self):
        """Test de comandos ESC/POS básicos"""
        try:
            # Comandos básicos ESC/POS
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            
            # Inicializar
            datos.extend(ESC + b'@')  # Inicializar
            
            # Centrar
            datos.extend(ESC + b'a\x01')  # Centrar
            datos.extend(b'*** TEST ESC/POS BASICO ***\n\n')
            
            # Izquierda
            datos.extend(ESC + b'a\x00')  # Izquierda
            datos.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp437'))
            datos.extend(b"Comandos ESC/POS funcionando\n")
            datos.extend(b"TM-m30II detectada\n")
            datos.extend(b"-" * 42 + b"\n")
            datos.extend(b"Si ves esto centrado y alineado,\n")
            datos.extend(b"los comandos ESC/POS funcionan\n")
            datos.extend(b"-" * 42 + b"\n\n\n")
            
            return self._imprimir_contenido(bytes(datos))
        except Exception as e:
            print(f"Error ESC/POS básico: {e}")
            return False
    
    def _test_multiples_qr(self):
        """Probar múltiples comandos QR diferentes"""
        print("   Probando diferentes comandos QR...")
        
        # MÉTODO 1: Comandos QR estándar EPSON
        print("   📋 Método 1: QR estándar EPSON")
        if self._test_qr_metodo1():
            print("   ✅ Método 1: QR generado")
        else:
            print("   ❌ Método 1: No funcionó")
        
        # MÉTODO 2: Comandos QR alternativos
        print("   📋 Método 2: QR alternativo")
        if self._test_qr_metodo2():
            print("   ✅ Método 2: QR generado")
        else:
            print("   ❌ Método 2: No funcionó")
        
        # MÉTODO 3: QR con comandos genéricos
        print("   📋 Método 3: QR genérico")
        if self._test_qr_metodo3():
            print("   ✅ Método 3: QR generado")
        else:
            print("   ❌ Método 3: No funcionó")
    
    def _test_qr_metodo1(self):
        """Método 1: QR con comandos EPSON estándar"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')  # Init
            datos.extend(ESC + b'a\x01')  # Center
            
            datos.extend(b"=== QR METODO 1 ===\n")
            datos.extend(b"Comandos EPSON estandar\n\n")
            
            # URL de prueba CORTA
            url = "https://www.arca.gob.ar/fe/qr/?p=1&p=2025-08-13&p=20203852100&p=3&p=11&p=1&p=100"
            
            # Configurar QR (comandos EPSON TM-m30II)
            datos.extend(GS + b'(k\x04\x00\x01A\x32\x00')  # Modelo 2
            datos.extend(GS + b'(k\x03\x00\x01C\x03')      # Tamaño 3
            datos.extend(GS + b'(k\x03\x00\x01E\x30')      # Error correction L
            
            # Almacenar datos
            url_bytes = url.encode('utf-8')
            longitud = len(url_bytes) + 3
            pL = longitud & 0xFF
            pH = (longitud >> 8) & 0xFF
            datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_bytes)
            
            # Imprimir QR
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            datos.extend(b"\n\nSi ves QR arriba: METODO 1 OK\n")
            datos.extend(b"URL: " + url[:30].encode('cp437') + b"...\n\n")
            
            return self._imprimir_contenido(bytes(datos))
        except Exception as e:
            print(f"   Error método 1: {e}")
            return False
    
    def _test_qr_metodo2(self):
        """Método 2: QR con comandos alternativos"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')
            datos.extend(ESC + b'a\x01')
            
            datos.extend(b"=== QR METODO 2 ===\n")
            datos.extend(b"Comandos alternativos\n\n")
            
            # URL más simple
            url = "https://arca.gob.ar/test"
            
            # Comandos diferentes
            datos.extend(GS + b'(k\x04\x00\x01A\x31\x00')  # Modelo 1
            datos.extend(GS + b'(k\x03\x00\x01C\x05')      # Tamaño 5
            datos.extend(GS + b'(k\x03\x00\x01E\x31')      # Error correction M
            
            # Datos
            url_bytes = url.encode('ascii')
            longitud = len(url_bytes) + 3
            pL = longitud & 0xFF
            pH = (longitud >> 8) & 0xFF
            datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_bytes)
            
            # Imprimir
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            datos.extend(b"\n\nSi ves QR arriba: METODO 2 OK\n")
            datos.extend(b"URL: " + url.encode('cp437') + b"\n\n")
            
            return self._imprimir_contenido(bytes(datos))
        except Exception as e:
            print(f"   Error método 2: {e}")
            return False
    
    def _test_qr_metodo3(self):
        """Método 3: QR con comandos genéricos"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')
            datos.extend(ESC + b'a\x01')
            
            datos.extend(b"=== QR METODO 3 ===\n")
            datos.extend(b"Comandos genericos\n\n")
            
            # URL muy simple
            url = "TEST123"
            
            # Comandos más básicos
            datos.extend(GS + b'(k\x04\x00\x01A\x32\x00')  # Modelo
            datos.extend(GS + b'(k\x03\x00\x01C\x04')      # Tamaño
            datos.extend(GS + b'(k\x03\x00\x01E\x30')      # Error
            
            # Datos simples
            url_bytes = url.encode('ascii')
            longitud = len(url_bytes) + 3
            datos.extend(GS + b'(k' + bytes([longitud, 0]) + b'\x01P0' + url_bytes)
            
            # Imprimir
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            datos.extend(b"\n\nSi ves QR arriba: METODO 3 OK\n")
            datos.extend(b"URL: " + url.encode('cp437') + b"\n\n")
            
            return self._imprimir_contenido(bytes(datos))
        except Exception as e:
            print(f"   Error método 3: {e}")
            return False
    
    def _test_driver_info(self):
        """Obtener información del driver"""
        try:
            handle = win32print.OpenPrinter(self.nombre_impresora)
            try:
                info = win32print.GetPrinter(handle, 2)
                print(f"   Driver: {info.get('pDriverName', 'N/A')}")
                print(f"   Puerto: {info.get('pPortName', 'N/A')}")
                print(f"   Estado: {info.get('Status', 'N/A')}")
                print(f"   Servidor: {info.get('pServerName', 'Local')}")
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            print(f"   Error obteniendo info: {e}")
    
    def _imprimir_contenido(self, datos_binarios):
        """Imprimir datos binarios"""
        try:
            handle = win32print.OpenPrinter(self.nombre_impresora)
            try:
                job = win32print.StartDocPrinter(handle, 1, ("Diagnostico", None, "RAW"))
                try:
                    win32print.StartPagePrinter(handle)
                    win32print.WritePrinter(handle, datos_binarios)
                    win32print.EndPagePrinter(handle)
                    return True
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            print(f"Error imprimiendo: {e}")
            return False
    
    def mostrar_soluciones(self):
        """Mostrar posibles soluciones"""
        print(f"\n💡 POSIBLES SOLUCIONES:")
        print(f"")
        print(f"1️⃣ DRIVER CORRECTO:")
        print(f"   - Descargar driver oficial EPSON TM-m30II")
        print(f"   - NO usar driver genérico")
        print(f"   - Configurar como 'RAW' o 'Generic/Text'")
        print(f"")
        print(f"2️⃣ CONFIGURACIÓN WINDOWS:")
        print(f"   - Panel Control > Impresoras")
        print(f"   - Clic derecho en TM-m30II > Propiedades")
        print(f"   - Avanzado > Tipo de datos: RAW")
        print(f"")
        print(f"3️⃣ CONEXIÓN:")
        print(f"   - USB: Cable original EPSON")
        print(f"   - Ethernet: IP fija configurada")
        print(f"   - No usar puerto LPT o COM genérico")
        print(f"")
        print(f"4️⃣ FIRMWARE:")
        print(f"   - Actualizar firmware TM-m30II")
        print(f"   - Verificar que soporte comandos QR")
        print(f"")
        print(f"5️⃣ ALTERNATIVAS:")
        print(f"   - Usar software EPSON oficial")
        print(f"   - Generar QR como imagen y enviar")
        print(f"   - Usar comandos de imagen en lugar de QR")

def main():
    """Función principal de diagnóstico"""
    print(f"🔧 DIAGNÓSTICO TM-m30II INICIADO")
    
    if not IMPRESION_DISPONIBLE:
        print("❌ Instalar: pip install pywin32")
        input("Enter para salir...")
        return
    
    diagnostico = DiagnosticoTMm30II()
    
    if not diagnostico.nombre_impresora:
        print("❌ No se detectó ninguna impresora")
        input("Enter para salir...")
        return
    
    print(f"\n⚠️ IMPORTANTE:")
    print(f"Este diagnóstico imprimirá varias páginas de prueba")
    print(f"para determinar qué comandos QR funcionan")
    
    respuesta = input(f"\n¿Continuar con diagnóstico completo? (s/N): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Diagnóstico cancelado")
        return
    
    # Ejecutar diagnóstico
    print(f"\n🚀 EJECUTANDO DIAGNÓSTICO...")
    resultado = diagnostico.diagnostico_completo()
    
    # Mostrar soluciones
    diagnostico.mostrar_soluciones()
    
    print(f"\n📋 INSTRUCCIONES:")
    print(f"1. Revisar las páginas impresas")
    print(f"2. Identificar qué método QR funcionó (si alguno)")
    print(f"3. Aplicar las soluciones sugeridas")
    print(f"4. Si ningún QR aparece, problema de driver/config")
    
    input(f"\n✅ Diagnóstico completado. Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Enter para salir...")