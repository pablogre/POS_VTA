import win32print

# Test básico con POS-58
try:
    print("Probando POS-58...")
    handle = win32print.OpenPrinter("POS-58")
    print("✅ POS-58 se puede abrir")
    
    # Test mínimo de escritura
    #job = win32print.StartDocPrinter(handle, 1, ("Test", None, "TEXT"))
    Job = win32print.StartDocPrinter(hPrinter, 1, ("POS_Test", None, "RAW"))
    win32print.StartPagePrinter(handle)
    win32print.WritePrinter(handle, b"Test simple\n\n\n")
    win32print.EndPagePrinter(handle)
    win32print.EndDocPrinter(handle)
    win32print.ClosePrinter(handle)
    print("✅ Test exitoso con POS-58")
    
except Exception as e:
    print(f"❌ Error con POS-58: {e}")

# Test con EPSON TM-m30II
try:
    print("\nProbando EPSON TM-m30II...")
    handle = win32print.OpenPrinter("EPSON TM-m30II Receipt")
    print("✅ EPSON se puede abrir")
    win32print.ClosePrinter(handle)
    
except Exception as e:
    print(f"❌ Error con EPSON: {e}")