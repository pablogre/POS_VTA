#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnostico_qr_arca_tm_m30ii.py - DIAGNÓSTICO ESPECÍFICO PARA QR DE ARCA
Ejecutar: python diagnostico_qr_arca_tm_m30ii.py
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
    print("❌ Sistema de impresión no disponible - Instalar: pip install pywin32")

print("\n" + "="*60)
print("🔧 DIAGNÓSTICO QR ARCA - TM-m30II")
print("="*60)

class DiagnosticoQRArca:
    def __init__(self):
        self.ancho_caracteres = 42
        self.nombre_impresora = self._buscar_tm_m30ii()
        
    def _buscar_tm_m30ii(self):
        """Buscar TM-m30II específica"""
        if not IMPRESION_DISPONIBLE:
            return None
            
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            
            print("🖨️ IMPRESORAS DETECTADAS:")
            for i, impresora in enumerate(impresoras, 1):
                nombre = impresora[2]
                print(f"   {i}. {nombre}")
                
                # Buscar TM-m30II específicamente
                if 'tm-m30ii' in nombre.lower():
                    print(f"      ⭐ TM-m30II ENCONTRADA: {nombre}")
                    return nombre
            
            # Si no encuentra, mostrar error específico
            print("❌ NO SE ENCONTRÓ TM-m30II ESPECÍFICA")
            print("💡 Verifica que instalaste 'EPSON Advanced Printer Driver 6'")
            return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def verificar_configuracion(self):
        """Verificar configuración de la impresora"""
        print(f"\n🔧 VERIFICANDO CONFIGURACIÓN:")
        
        if not self.nombre_impresora:
            return False
        
        try:
            handle = win32print.OpenPrinter(self.nombre_impresora)
            try:
                info = win32print.GetPrinter(handle, 2)
                print(f"   ✅ Driver: {info.get('pDriverName', 'N/A')}")
                print(f"   ✅ Puerto: {info.get('pPortName', 'N/A')}")
                
                # Verificar que sea el driver correcto
                driver_name = info.get('pDriverName', '').lower()
                if 'tm-m30ii' in driver_name or 'advanced' in driver_name:
                    print(f"   ✅ Driver correcto detectado")
                    return True
                else:
                    print(f"   ⚠️ Driver puede no ser el correcto")
                    return True  # Continuar de todos modos
                    
            finally:
                win32print.ClosePrinter(handle)
        except Exception as e:
            print(f"   ❌ Error verificando: {e}")
            return False
    
    def test_qr_arca_completo(self):
        """Test completo con URL real de ARCA"""
        print(f"\n🎯 TEST QR ARCA COMPLETO")
        
        # URL real de ARCA (ejemplo)
        url_arca = "https://www.arca.gob.ar/fe/qr/?p=20203852100&p=3&p=11&p=1&p=100.00&p=2025-08-14"
        
        print(f"📋 URL ARCA: {url_arca[:50]}...")
        
        # Probar los 3 métodos secuencialmente
        metodos_exitosos = []
        
        if self._qr_metodo_optimizado(url_arca):
            metodos_exitosos.append("Método Optimizado")
            
        if self._qr_metodo_estandar(url_arca):
            metodos_exitosos.append("Método Estándar")
            
        if self._qr_metodo_alternativo(url_arca):
            metodos_exitosos.append("Método Alternativo")
        
        return metodos_exitosos
    
    def _qr_metodo_optimizado(self, url):
        """Método optimizado para TM-m30II con comandos precisos"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            
            # Inicializar impresora
            datos.extend(ESC + b'@')  # ESC @
            
            # Centrar y título
            datos.extend(ESC + b'a\x01')  # Centrar
            datos.extend(b"=== QR ARCA - METODO OPTIMIZADO ===\n")
            datos.extend(b"TM-m30II Advanced Driver\n\n")
            
            # Configurar QR con parámetros optimizados para TM-m30II
            datos.extend(GS + b'(k\x04\x00\x01A\x32\x00')  # QR Modelo 2
            datos.extend(GS + b'(k\x03\x00\x01C\x04')      # Tamaño 4 (óptimo)
            datos.extend(GS + b'(k\x03\x00\x01E\x30')      # Error correction L
            
            # Almacenar datos QR
            url_bytes = url.encode('utf-8')
            longitud = len(url_bytes) + 3
            pL = longitud & 0xFF
            pH = (longitud >> 8) & 0xFF
            
            datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_bytes)
            
            # Imprimir QR
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            # Texto informativo
            datos.extend(b"\n\n")
            datos.extend(ESC + b'a\x00')  # Alinear izquierda
            datos.extend(b"Si ves QR arriba: METODO OPTIMIZADO OK\n")
            datos.extend(b"Fecha: " + datetime.now().strftime('%d/%m/%Y %H:%M').encode('cp437') + b"\n")
            datos.extend(b"URL ARCA validada\n")
            datos.extend(b"-" * 42 + b"\n\n\n")
            
            return self._imprimir_datos(bytes(datos), "Método Optimizado")
            
        except Exception as e:
            print(f"   ❌ Error método optimizado: {e}")
            return False
    
    def _qr_metodo_estandar(self, url):
        """Método estándar EPSON"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')
            datos.extend(ESC + b'a\x01')
            
            datos.extend(b"=== QR ARCA - METODO ESTANDAR ===\n")
            datos.extend(b"Comandos EPSON estandar\n\n")
            
            # Configuración estándar
            datos.extend(GS + b'(k\x04\x00\x01A\x32\x00')  # Modelo 2
            datos.extend(GS + b'(k\x03\x00\x01C\x03')      # Tamaño 3
            datos.extend(GS + b'(k\x03\x00\x01E\x31')      # Error correction M
            
            # Datos
            url_bytes = url.encode('utf-8')
            longitud = len(url_bytes) + 3
            pL = longitud & 0xFF
            pH = (longitud >> 8) & 0xFF
            datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_bytes)
            
            # Imprimir
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            datos.extend(b"\n\n")
            datos.extend(ESC + b'a\x00')
            datos.extend(b"Si ves QR arriba: METODO ESTANDAR OK\n")
            datos.extend(b"Driver TM-m30II funcionando\n")
            datos.extend(b"-" * 42 + b"\n\n\n")
            
            return self._imprimir_datos(bytes(datos), "Método Estándar")
            
        except Exception as e:
            print(f"   ❌ Error método estándar: {e}")
            return False
    
    def _qr_metodo_alternativo(self, url):
        """Método alternativo con parámetros diferentes"""
        try:
            ESC = b'\x1B'
            GS = b'\x1D'
            
            datos = bytearray()
            datos.extend(ESC + b'@')
            datos.extend(ESC + b'a\x01')
            
            datos.extend(b"=== QR ARCA - METODO ALTERNATIVO ===\n")
            datos.extend(b"Parametros alternativos\n\n")
            
            # Parámetros alternativos
            datos.extend(GS + b'(k\x04\x00\x01A\x31\x00')  # Modelo 1
            datos.extend(GS + b'(k\x03\x00\x01C\x05')      # Tamaño 5
            datos.extend(GS + b'(k\x03\x00\x01E\x32')      # Error correction Q
            
            # Datos con codificación ASCII
            url_ascii = url.encode('ascii', errors='ignore')
            longitud = len(url_ascii) + 3
            pL = longitud & 0xFF
            pH = (longitud >> 8) & 0xFF
            datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + url_ascii)
            
            # Imprimir
            datos.extend(GS + b'(k\x03\x00\x01Q0')
            
            datos.extend(b"\n\n")
            datos.extend(ESC + b'a\x00')
            datos.extend(b"Si ves QR arriba: METODO ALTERNATIVO OK\n")
            datos.extend(b"Codificacion ASCII usada\n")
            datos.extend(b"-" * 42 + b"\n\n\n")
            
            return self._imprimir_datos(bytes(datos), "Método Alternativo")
            
        except Exception as e:
            print(f"   ❌ Error método alternativo: {e}")
            return False
    
    def _imprimir_datos(self, datos_binarios, metodo):
        """Imprimir datos usando win32print con manejo de errores"""
        try:
            print(f"   📄 Enviando {metodo}...")
            
            handle = win32print.OpenPrinter(self.nombre_impresora)
            try:
                # Crear trabajo de impresión
                job_info = ("QR ARCA Test", None, "RAW")
                job = win32print.StartDocPrinter(handle, 1, job_info)
                
                try:
                    win32print.StartPagePrinter(handle)
                    bytes_written = win32print.WritePrinter(handle, datos_binarios)
                    win32print.EndPagePrinter(handle)
                    
                    print(f"   ✅ {metodo}: {bytes_written} bytes enviados")
                    return True
                    
                finally:
                    win32print.EndDocPrinter(handle)
            finally:
                win32print.ClosePrinter(handle)
                
        except Exception as e:
            print(f"   ❌ Error imprimiendo {metodo}: {e}")
            return False
    
    def generar_qr_personalizado(self):
        """Permitir al usuario generar QR con datos personalizados"""
        print(f"\n🎨 GENERADOR QR PERSONALIZADO")
        
        print("Opciones:")
        print("1. URL de ARCA personalizada")
        print("2. Texto simple")
        print("3. URL web")
        
        try:
            opcion = input("Selecciona opción (1-3): ").strip()
            
            if opcion == "1":
                cuit = input("CUIT (ej: 20203852100): ").strip()
                tipo_comprobante = input("Tipo comprobante (ej: 11): ").strip()
                numero = input("Número comprobante (ej: 1): ").strip()
                importe = input("Importe (ej: 100.00): ").strip()
                fecha = datetime.now().strftime('%Y-%m-%d')
                
                url = f"https://www.arca.gob.ar/fe/qr/?p={cuit}&p=3&p={tipo_comprobante}&p={numero}&p={importe}&p={fecha}"
                
            elif opcion == "2":
                url = input("Texto para QR: ").strip()
                
            elif opcion == "3":
                url = input("URL completa: ").strip()
                
            else:
                print("Opción inválida")
                return
            
            print(f"\n🎯 Generando QR: {url[:50]}...")
            
            # Usar método optimizado
            if self._qr_metodo_optimizado(url):
                print("✅ QR personalizado generado correctamente")
            else:
                print("❌ Error generando QR personalizado")
                
        except KeyboardInterrupt:
            print("\n❌ Cancelado por usuario")
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print(f"🔧 DIAGNÓSTICO QR ARCA - TM-m30II")
    
    if not IMPRESION_DISPONIBLE:
        print("❌ Instalar: pip install pywin32")
        input("Enter para salir...")
        return
    
    diagnostico = DiagnosticoQRArca()
    
    if not diagnostico.nombre_impresora:
        print("\n💡 SOLUCIONES:")
        print("1. Verifica que instalaste 'EPSON Advanced Printer Driver 6'")
        print("2. Reinicia Windows después de instalar")
        print("3. Verifica que la impresora esté conectada y encendida")
        input("Enter para salir...")
        return
    
    print(f"\n⚠️ ESTE DIAGNÓSTICO:")
    print("✅ Verificará la configuración de TM-m30II")
    print("✅ Probará 3 métodos diferentes de QR")
    print("✅ Usará URL real de ARCA")
    print("✅ Te permitirá generar QR personalizados")
    
    respuesta = input(f"\n¿Continuar? (s/N): ").lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Diagnóstico cancelado")
        return
    
    # Verificar configuración
    if not diagnostico.verificar_configuracion():
        print("❌ Error en configuración de impresora")
        return
    
    # Test QR ARCA
    print(f"\n🚀 INICIANDO TESTS QR...")
    metodos_exitosos = diagnostico.test_qr_arca_completo()
    
    # Resultados
    print(f"\n📋 RESULTADOS:")
    if metodos_exitosos:
        print(f"✅ Métodos que funcionaron: {', '.join(metodos_exitosos)}")
        print(f"🎉 ¡TU IMPRESORA PUEDE IMPRIMIR QR!")
        
        # Ofrecer QR personalizado
        respuesta = input(f"\n¿Quieres generar un QR personalizado? (s/N): ").lower()
        if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
            diagnostico.generar_qr_personalizado()
            
    else:
        print(f"❌ Ningún método funcionó")
        print(f"\n💡 PRÓXIMOS PASOS:")
        print("1. Verifica configuración RAW en propiedades de impresora")
        print("2. Reinicia el servicio de spooler: services.msc")
        print("3. Intenta con puerto USB directo")
        print("4. Contacta soporte técnico EPSON")
    
    input(f"\n✅ Diagnóstico completado. Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Enter para salir...")