#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_basico_tm_m30ii.py - TEST BÁSICO PARA VERIFICAR COMUNICACIÓN
Ejecutar: python test_basico_tm_m30ii.py
"""

import win32print
import win32api
from datetime import datetime

def verificar_impresora():
    """Verificar que la impresora esté bien configurada"""
    print("🔍 VERIFICANDO IMPRESORA TM-m30II...")
    
    # Buscar impresora
    impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
    tm_m30ii = None
    
    for impresora in impresoras:
        nombre = impresora[2]
        if 'tm-m30ii' in nombre.lower():
            tm_m30ii = nombre
            break
    
    if not tm_m30ii:
        print("❌ No se encontró TM-m30II")
        return None
    
    print(f"✅ Impresora encontrada: {tm_m30ii}")
    
    # Verificar configuración
    try:
        handle = win32print.OpenPrinter(tm_m30ii)
        info = win32print.GetPrinter(handle, 2)
        
        print(f"   Driver: {info.get('pDriverName', 'N/A')}")
        print(f"   Puerto: {info.get('pPortName', 'N/A')}")
        print(f"   Estado: {info.get('Status', 'N/A')}")
        
        win32print.ClosePrinter(handle)
        return tm_m30ii
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return None

def test_texto_simple(impresora):
    """Test de texto simple - debe funcionar siempre"""
    print("\n📝 TEST 1: Texto simple...")
    
    try:
        contenido = f"""
*** TEST COMUNICACION BASICA ***
TM-m30II Detectada
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}
========================================
Si ves esto, la comunicacion funciona
========================================




""".encode('cp437')
        
        handle = win32print.OpenPrinter(impresora)
        job = win32print.StartDocPrinter(handle, 1, ("Test Basico", None, "RAW"))
        win32print.StartPagePrinter(handle)
        bytes_written = win32print.WritePrinter(handle, contenido)
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
        win32print.ClosePrinter(handle)
        
        print(f"✅ Texto enviado: {bytes_written} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error texto: {e}")
        return False

def test_comandos_basicos(impresora):
    """Test de comandos ESC/POS básicos"""
    print("\n🔧 TEST 2: Comandos ESC/POS básicos...")
    
    try:
        ESC = b'\x1B'
        
        datos = bytearray()
        datos.extend(ESC + b'@')  # Inicializar
        datos.extend(ESC + b'a\x01')  # Centrar
        datos.extend(b'*** COMANDOS ESC/POS ***\n\n')
        datos.extend(ESC + b'a\x00')  # Izquierda
        datos.extend(b'Comandos basicos funcionando\n')
        datos.extend(b'TM-m30II respondiendo\n')
        datos.extend(b'Preparado para QR\n')
        datos.extend(b'========================================\n\n\n')
        
        handle = win32print.OpenPrinter(impresora)
        job = win32print.StartDocPrinter(handle, 1, ("Test ESC/POS", None, "RAW"))
        win32print.StartPagePrinter(handle)
        bytes_written = win32print.WritePrinter(handle, bytes(datos))
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
        win32print.ClosePrinter(handle)
        
        print(f"✅ Comandos enviados: {bytes_written} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error comandos: {e}")
        return False

def test_qr_minimo(impresora):
    """Test QR con datos mínimos"""
    print("\n🔳 TEST 3: QR mínimo...")
    
    try:
        ESC = b'\x1B'
        GS = b'\x1D'
        
        datos = bytearray()
        datos.extend(ESC + b'@')  # Inicializar
        datos.extend(ESC + b'a\x01')  # Centrar
        datos.extend(b'=== TEST QR MINIMO ===\n\n')
        
        # QR con texto simple "HOLA"
        texto_qr = "HOLA"
        
        # Comandos QR básicos
        datos.extend(GS + b'(k\x04\x00\x01A\x32\x00')  # Modelo 2
        datos.extend(GS + b'(k\x03\x00\x01C\x03')      # Tamaño 3
        datos.extend(GS + b'(k\x03\x00\x01E\x30')      # Error L
        
        # Almacenar datos
        texto_bytes = texto_qr.encode('ascii')
        longitud = len(texto_bytes) + 3
        pL = longitud & 0xFF
        pH = (longitud >> 8) & 0xFF
        datos.extend(GS + b'(k' + bytes([pL, pH]) + b'\x01P0' + texto_bytes)
        
        # Imprimir QR
        datos.extend(GS + b'(k\x03\x00\x01Q0')
        
        datos.extend(b'\n\nTexto: HOLA\n')
        datos.extend(b'Si ves QR arriba: FUNCIONA!\n')
        datos.extend(b'========================================\n\n\n')
        
        handle = win32print.OpenPrinter(impresora)
        job = win32print.StartDocPrinter(handle, 1, ("Test QR Mini", None, "RAW"))
        win32print.StartPagePrinter(handle)
        bytes_written = win32print.WritePrinter(handle, bytes(datos))
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
        win32print.ClosePrinter(handle)
        
        print(f"✅ QR enviado: {bytes_written} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error QR: {e}")
        return False

def mostrar_instrucciones_configuracion():
    """Mostrar instrucciones de configuración si falla"""
    print("\n🔧 CONFIGURACIÓN NECESARIA:")
    print("\n1️⃣ CONFIGURAR IMPRESORA COMO RAW:")
    print("   - Panel Control > Dispositivos e impresoras")
    print("   - Clic derecho en TM-m30II > Propiedades")
    print("   - Pestaña Avanzado:")
    print("     * Procesador: winprint")
    print("     * Tipo de datos: RAW")
    print("     * ☑ Imprimir directamente a la impresora")
    
    print("\n2️⃣ VERIFICAR PUERTO:")
    print("   - En Propiedades > Puertos")
    print("   - Debe estar en puerto USB correcto")
    print("   - NO debe estar en LPT1 o puerto genérico")
    
    print("\n3️⃣ REINICIAR SERVICIOS:")
    print("   - Windows + R > services.msc")
    print("   - Buscar 'Spooler de impresión'")
    print("   - Clic derecho > Reiniciar")
    
    print("\n4️⃣ VERIFICAR FIRMWARE:")
    print("   - La TM-m30II debe tener firmware que soporte QR")
    print("   - Imprimir autotest: mantener botón FEED al encender")
    print("   - Verificar versión de firmware en el autotest")

def main():
    """Función principal de test básico"""
    print("🔧 TEST BÁSICO TM-m30II")
    print("="*50)
    
    # Verificar impresora
    impresora = verificar_impresora()
    if not impresora:
        mostrar_instrucciones_configuracion()
        input("\nPresiona Enter para salir...")
        return
    
    print(f"\n🚀 Ejecutando tests básicos...")
    print("⚠️ Se imprimirán 3 páginas de prueba")
    
    respuesta = input("\n¿Continuar? (s/N): ").lower()
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        return
    
    # Ejecutar tests
    test1 = test_texto_simple(impresora)
    test2 = test_comandos_basicos(impresora)
    test3 = test_qr_minimo(impresora)
    
    # Resultados
    print("\n📋 RESULTADOS:")
    print(f"   Texto simple: {'✅' if test1 else '❌'}")
    print(f"   Comandos ESC/POS: {'✅' if test2 else '❌'}")
    print(f"   QR mínimo: {'✅' if test3 else '❌'}")
    
    if test1 and test2 and test3:
        print("\n🎉 ¡TODOS LOS TESTS EXITOSOS!")
        print("Tu impresora puede imprimir QR")
        print("Puedes usar comandos QR en tu aplicación")
    elif test1 and test2:
        print("\n⚠️ COMUNICACIÓN OK, PERO QR NO FUNCIONA")
        print("Problema específico con comandos QR")
        mostrar_solucion_qr()
    elif test1:
        print("\n⚠️ TEXTO OK, PERO COMANDOS ESC/POS NO")
        print("Problema con configuración RAW")
        mostrar_instrucciones_configuracion()
    else:
        print("\n❌ PROBLEMAS DE COMUNICACIÓN BÁSICA")
        mostrar_instrucciones_configuracion()
    
    input("\nPresiona Enter para salir...")

def mostrar_solucion_qr():
    """Mostrar soluciones específicas para QR"""
    print("\n💡 SOLUCIONES PARA QR:")
    print("\n1️⃣ VERIFICAR FIRMWARE:")
    print("   - Mantén botón FEED al encender > autotest")
    print("   - Busca versión firmware en la página impresa")
    print("   - Firmware debe ser v3.0 o superior para QR")
    
    print("\n2️⃣ COMANDOS ALTERNATIVOS:")
    print("   - Algunos TM-m30II no soportan comandos (k")
    print("   - Usar imagen QR en lugar de comandos")
    print("   - Generar QR como bitmap y enviar como imagen")
    
    print("\n3️⃣ VERIFICAR MODELO:")
    print("   - TM-m30II-SL: soporte QR limitado")
    print("   - TM-m30II-H: soporte QR completo")
    print("   - TM-m30II-NT: soporte QR completo")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Enter para salir...")