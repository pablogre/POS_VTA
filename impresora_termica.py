import os
import platform
from datetime import datetime
import win32print
import win32api
import tempfile
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImpresoraTermica:
    def __init__(self, nombre_impresora=None, ancho_mm=80):
        # Para impresoras térmicas de 80mm, el ancho típico es 42-48 caracteres
        if ancho_mm == 80:
            self.ancho = 42  # Caracteres por línea para 80mm
        elif ancho_mm == 58:
            self.ancho = 32  # Caracteres por línea para 58mm
        else:
            self.ancho = ancho_mm  # Si se especifica directamente
            
        self.ancho_mm = ancho_mm
        self.nombre_impresora = nombre_impresora or self._buscar_impresora_termica()
        
        print(f"🖨️ Configuración: {ancho_mm}mm = {self.ancho} caracteres por línea")
        
    # Reemplaza la función _buscar_impresora_termica en tu impresora_termica.py:

    def _buscar_impresora_termica(self):
        """Buscar impresora térmica automáticamente - EPSON TM-m30II prioritaria"""
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            
            # ORDEN DE PRIORIDAD: EPSON TM-m30II PRIMERO
            nombres_termicas_prioritarios = [
                'EPSON TM-m30II Receipt',  # ✅ Esta es la mejor - nombre exacto
                'epson tm-m30ii receipt',  # Variación en minúsculas
                'tm-m30ii receipt',        # Sin marca
            ]
            
            # Buscar EPSON TM-m30II primero (prioritario)
            for impresora in impresoras:
                nombre = impresora[2].lower()
                for prioritario in nombres_termicas_prioritarios:
                    if prioritario.lower() in nombre:
                        print(f"🖨️ ✅ EPSON TM-m30II detectada: {impresora[2]}")
                        print(f"🎯 Esta impresora térmica profesional será usada")
                        return impresora[2]
            
            # Si no encuentra EPSON, buscar otras térmicas
            nombres_termicas_secundarios = [
                'pos-58', 'pos58',
                'tm-m30ii', 'tm-m30', 'epson tm-m30',
                'thermal', 'receipt', 'pos', 'tm-', 'rp-', 'sp-',
                'termica', 'ticket', 'epson', 'star', 'citizen',
                'xprinter', 'godex', 'zebra', 'bixolon'
            ]
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                for termico in nombres_termicas_secundarios:
                    if termico in nombre:
                        print(f"🖨️ ⚠️ Impresora térmica secundaria detectada: {impresora[2]}")
                        print(f"💡 Recomendación: Usar EPSON TM-m30II si está disponible")
                        return impresora[2]
            
            # Si no encuentra térmica, usar impresora por defecto
            try:
                impresora_default = win32print.GetDefaultPrinter()
                print(f"🖨️ 📄 Usando impresora por defecto: {impresora_default}")
                print(f"⚠️ Esta puede no ser una impresora térmica")
                return impresora_default
            except:
                print("❌ No se pudo obtener impresora por defecto")
                return None
            
        except Exception as e:
            print(f"❌ Error detectando impresora: {e}")
            return None
            
    def centrar_texto(self, texto, ancho=None):
        """Centrar texto en el ancho especificado"""
        ancho = ancho or self.ancho
        if len(texto) >= ancho:
            return texto[:ancho]
        espacios = (ancho - len(texto)) // 2
        return " " * espacios + texto
    
    def justificar_texto(self, izquierda, derecha, ancho=None):
        """Justificar texto a izquierda y derecha"""
        ancho = ancho or self.ancho
        espacios_necesarios = ancho - len(izquierda) - len(derecha)
        if espacios_necesarios <= 0:
            return (izquierda + derecha)[:ancho]
        return izquierda + " " * espacios_necesarios + derecha
    
    def linea_separadora(self, caracter="-", ancho=None):
        """Crear línea separadora"""
        ancho = ancho or self.ancho
        return caracter * ancho
    
    def truncar_texto(self, texto, max_chars):
        """Truncar texto si es muy largo"""
        if len(texto) <= max_chars:
            return texto
        return texto[:max_chars-3] + "..."

    def formatear_factura_termica(self, factura):
        """Formatear factura para impresión térmica de 80mm - QR COMENTADO"""
        lineas = []
        
        print("🔍 DEBUG - Iniciando formateo de factura")
        print(f"   Factura número: {getattr(factura, 'numero', 'SIN NUMERO')}")
        print(f"   Cliente: {getattr(factura.cliente, 'nombre', 'SIN CLIENTE') if hasattr(factura, 'cliente') and factura.cliente else 'SIN CLIENTE'}")
        print(f"   Detalles: {len(factura.detalles) if hasattr(factura, 'detalles') else 0}")
        
        try:
            # ENCABEZADO
            lineas.append("")
            # Para máximo impacto:
            
            lineas.append("              \x1B\x45\x01\x1B\x21\x30CARNAVE\x1B\x21\x00\x1B\x45\x00")
            lineas.append("")
            lineas.append(self.centrar_texto("CUIT: 27-33342943-3"))
            lineas.append(self.centrar_texto("IVA: Responsable Inscrípto"))
            lineas.append(self.centrar_texto("Dir: Dorrego y Eva Perón"))
            lineas.append(self.centrar_texto("La Esquina de Siempre"))
            lineas.append("")
            
            # TIPO DE COMPROBANTE
            tipo_cbte = self._obtener_tipo_comprobante(factura.tipo_comprobante)
            lineas.append(self.centrar_texto(f"=== {tipo_cbte} ==="))
            lineas.append(self.centrar_texto(f"Nro: {factura.numero}"))
            lineas.append("")
            
            # FECHA Y HORA
            fecha_str = factura.fecha.strftime("%d/%m/%Y %H:%M")
            lineas.append(f"Fecha: {fecha_str}")
            
            # VENDEDOR
            vendedor = "Sistema"  # Default
            if hasattr(factura, 'usuario') and factura.usuario:
                vendedor = factura.usuario.nombre
            vendedor_corto = self.truncar_texto(vendedor, 20)
            lineas.append(f"Vendedor: {vendedor_corto}")
            
            lineas.append(self.linea_separadora())
            
            # CLIENTE
            if hasattr(factura, 'cliente') and factura.cliente:
                nombre_cliente = self.truncar_texto(factura.cliente.nombre, self.ancho)
                lineas.append(f"Cliente: {nombre_cliente}")
                if hasattr(factura.cliente, 'documento') and factura.cliente.documento:
                    tipo_doc = getattr(factura.cliente, 'tipo_documento', 'DNI') or "DNI"
                    lineas.append(f"{tipo_doc}: {factura.cliente.documento}")
            else:
                lineas.append("Cliente: Consumidor Final")
            
            lineas.append(self.linea_separadora())
            
            # ENCABEZADO DE PRODUCTOS
            lineas.append("PRODUCTO         CANT  P.U    TOTAL")
            lineas.append(self.linea_separadora())
            
            # PRODUCTOS (formato compacto)
            if hasattr(factura, 'detalles') and factura.detalles:
                print(f"🔍 DEBUG - Procesando {len(factura.detalles)} productos:")
                
                for i, detalle in enumerate(factura.detalles):
                    print(f"   Producto {i+1}: {getattr(detalle.producto, 'nombre', 'SIN NOMBRE') if hasattr(detalle, 'producto') and detalle.producto else 'SIN PRODUCTO'}")
                    
                    max_nombre = 17
                    cant_space = 5
                    precio_space = 7
                    total_space = 8
                    
                    # Obtener nombre del producto de forma segura
                    if hasattr(detalle, 'producto') and detalle.producto:
                        nombre_producto = getattr(detalle.producto, 'nombre', 'Producto')
                    else:
                        nombre_producto = 'Producto'
                    
                    nombre = self.truncar_texto(nombre_producto, max_nombre)
                    
                    # Formatear números de forma segura
                    try:
                        cant_str = f"{float(detalle.cantidad):.3f}"
                        precio_str = f"{float(detalle.precio_unitario):,.2f}"
                        total_str = f"{float(detalle.subtotal):,.2f}"
                    except (ValueError, AttributeError) as e:
                        print(f"⚠️ Error formateando números: {e}")
                        cant_str = "1"
                        precio_str = "0"
                        total_str = "0"
                    
                    # Crear línea compacta
                    linea = f"{nombre:<{max_nombre}} {cant_str:>{cant_space}} {precio_str:>{precio_space}} {total_str:>{total_space}}"
                    lineas.append(linea[:self.ancho])
            else:
                print("⚠️ DEBUG - No se encontraron detalles en la factura")
                lineas.append("Sin productos")
            
            lineas.append(self.linea_separadora())
            
            # TOTALES CON IVA DISCRIMINADO
            try:
                subtotal = float(getattr(factura, 'subtotal', 0))
                iva_total = float(getattr(factura, 'iva', 0))
                total = float(getattr(factura, 'total', 0))
                
                lineas.append(self.justificar_texto("SUBTOTAL:", f"${subtotal:,.2f}"))
                
                # *** DISCRIMINAR IVA POR ALÍCUOTA ***
                if hasattr(factura, 'detalles') and factura.detalles:
                    # Agrupar por porcentaje de IVA
                    iva_por_alicuota = {}
                    
                    for detalle in factura.detalles:
                        # Obtener porcentaje de IVA del detalle
                        if hasattr(detalle, 'porcentaje_iva') and detalle.porcentaje_iva is not None:
                            porcentaje = float(detalle.porcentaje_iva)
                        else:
                            # Fallback: obtener del producto
                            porcentaje = float(detalle.producto.iva) if hasattr(detalle, 'producto') and detalle.producto else 21.0
                        
                        # Calcular IVA del detalle
                        subtotal_detalle = float(detalle.subtotal)
                        iva_detalle = round((subtotal_detalle * porcentaje / 100), 2)
                        
                        # Agrupar por alícuota
                        if porcentaje not in iva_por_alicuota:
                            iva_por_alicuota[porcentaje] = 0
                        iva_por_alicuota[porcentaje] += iva_detalle
                    
                    # Mostrar cada alícuota de IVA
                    for porcentaje in sorted(iva_por_alicuota.keys()):
                        importe_iva = iva_por_alicuota[porcentaje]
                        if importe_iva > 0:
                            if porcentaje == 0:
                                etiqueta = "EXENTO:"
                            else:
                                etiqueta = f"IVA {porcentaje:g}%:"
                            lineas.append(self.justificar_texto(etiqueta, f"${importe_iva:,.2f}"))
                    
                    print(f"🧮 IVA discriminado: {iva_por_alicuota}")
                else:
                    # Fallback: mostrar IVA total si no hay detalles
                    if iva_total > 0:
                        lineas.append(self.justificar_texto("IVA 21%:", f"${iva_total:,.2f}"))
                
                
                # Obtener descuento desde los datos de la venta (si los tienes)
                # Por ahora, puedes calcularlo así:
                subtotal_mas_iva = subtotal + iva_total
                if total < subtotal_mas_iva:
                    descuento = subtotal_mas_iva - total
                    if descuento > 0:
                        lineas.append(self.justificar_texto("DESCUENTO:", f"-${descuento:.2f}"))
                        
                lineas.append(self.linea_separadora())
                lineas.append(self.justificar_texto("TOTAL:", f"${total:,.2f}"))

                
                
            except (ValueError, AttributeError) as e:
                print(f"⚠️ Error formateando totales: {e}")
                lineas.append(self.justificar_texto("TOTAL:", "$0.00"))
            
            lineas.append(self.linea_separadora())

            

            # INFORMACIÓN AFIP CON CAE (SIN QR)
            cae = getattr(factura, 'cae', None)
            if cae:
                lineas.append("")
                lineas.append("Transparencia Fiscal al Consumidor - Ley 27.743")
                lineas.append("")
                lineas.append(self.centrar_texto("*** AUTORIZADO AFIP ***"))
                lineas.append("")
                
                # CAE
                cae_texto = f"CAE: {cae}"
                if len(cae_texto) > self.ancho:
                    lineas.append("CAE:")
                    lineas.append(f"  {cae}")
                else:
                    lineas.append(cae_texto)
                    
                vto_cae = getattr(factura, 'vto_cae', None)
                if vto_cae:
                    try:
                        if hasattr(vto_cae, 'strftime'):
                            vto_str = vto_cae.strftime("%d/%m/%Y")
                        else:
                            vto_str = str(vto_cae)
                        lineas.append(f"Vto CAE: {vto_str}")
                    except Exception as e:
                        print(f"⚠️ Error formateando fecha CAE: {e}")
                        lineas.append(f"Vto CAE: {vto_cae}")
                
                # *** CÓDIGO QR AFIP - COMENTADO ***
                # try:
                #     # Intentar importar el módulo QR
                #     from qr_arca import crear_generador_qr
                #     generador_qr = crear_generador_qr()
                #     info_qr = generador_qr.obtener_info_qr(factura)
                #     
                #     if info_qr['valido']:
                #         lineas.append("")
                #         lineas.append(self.centrar_texto("--- CODIGO QR AFIP ---"))
                #         
                #         # Generar QR en ASCII
                #         qr_ascii = generador_qr.generar_qr_ascii(factura)
                #         if qr_ascii:
                #             # Dividir QR en líneas y centrar
                #             lineas_qr = qr_ascii.split('\n')
                #             for linea_qr in lineas_qr:
                #                 # Truncar si es muy ancho para la impresora
                #                 if len(linea_qr) > self.ancho:
                #                     linea_qr = linea_qr[:self.ancho]
                #                 lineas.append(linea_qr)
                #         else:
                #             # Fallback: mostrar URL
                #             lineas.append(self.centrar_texto("QR: Ver en factura web"))
                #         
                #         lineas.append("")
                #         lineas.append(self.centrar_texto("Escanear para verificar"))
                #         lineas.append(self.centrar_texto("en www.arca.gob.ar"))
                #     else:
                #         lineas.append("")
                #         lineas.append(self.centrar_texto("QR no disponible"))
                #         lineas.append(self.centrar_texto(info_qr['mensaje']))
                # except ImportError:
                #     # Si no está disponible el módulo QR, continuar sin QR
                #     lineas.append("")
                #     lineas.append(self.centrar_texto("QR: Modulo no disponible"))
                #     print("⚠️ Módulo QR no disponible")
                # except Exception as e:
                #     print(f"⚠️ Error generando QR: {e}")
                #     lineas.append("")
                #     lineas.append(self.centrar_texto("QR: Error al generar"))
                
                # *** MENSAJE OPCIONAL PARA VERIFICACIÓN WEB ***
                lineas.append("")
                lineas.append(self.centrar_texto("Verificar en:"))
                lineas.append(self.centrar_texto("www.arca.gob.ar"))
                
            else:
                lineas.append("")
                lineas.append("Transparencia Fiscal al Consumidor - Ley 27.743")
                lineas.append("")
                lineas.append(self.centrar_texto("*** NO AUTORIZADO ***"))
                lineas.append(self.centrar_texto("VERIFICAR AFIP"))
            
            # PIE DE PÁGINA
            lineas.append("")
            lineas.append(self.centrar_texto("Gracias por elegirnos"))
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("")
            lineas.append("")  # Más espacios antes del corte
            lineas.append("")
            
            # COMANDO DE CORTE DE PAPEL (ESC/POS)
            # ESC i = Corte completo (0x1B + 0x69)
            # GS V = Corte con alimentación (0x1D + 0x56 + 0x00)
            lineas.append("\x1B\x69")  # Comando ESC i - Corte completo
            
        except Exception as e:
            print(f"❌ Error en formatear_factura_termica: {e}")
            import traceback
            traceback.print_exc()
            
            # Crear factura mínima en caso de error
            lineas = [
                "",
                self.centrar_texto("*** ERROR EN FACTURA ***"),
                "",
                f"Error: {str(e)}",
                "",
                self.centrar_texto("Contactar soporte"),
                "",
                "",
                ""
            ]
        
        resultado = "\n".join(lineas)
        print(f"🔍 DEBUG - Factura formateada: {len(resultado)} caracteres, {len(lineas)} líneas")
        print(f"🔍 DEBUG - Primeras 5 líneas:")
        for i, linea in enumerate(lineas[:5]):
            print(f"   {i+1}: '{linea}'")
        
        return resultado


    def imprimir_factura_con_qr_web(self, factura):
        """Imprimir factura y mostrar QR en navegador para dispositivos móviles"""
        try:
            # Imprimir factura normal
            resultado_impresion = self.imprimir_factura(factura)
            
            # Generar info del QR para mostrar en web (COMENTADO)
            # try:
            #     from qr_arca import crear_generador_qr
            #     generador_qr = crear_generador_qr()
            #     info_qr = generador_qr.obtener_info_qr(factura)
            # except ImportError:
            #     info_qr = {'valido': False, 'mensaje': 'Módulo QR no disponible'}
            
            # Info QR deshabilitada
            info_qr = {'valido': False, 'mensaje': 'QR deshabilitado en impresión'}
            
            return {
                'impresion_exitosa': resultado_impresion,
                'qr_info': info_qr
            }
        except Exception as e:
            print(f"❌ Error en impresión con QR: {e}")
            return {
                'impresion_exitosa': False,
                'qr_info': {'valido': False, 'mensaje': str(e)}
            }

    def _obtener_tipo_comprobante(self, tipo):
        """Obtener descripción del tipo de comprobante"""
        tipos = {
            '01': 'FACTURA A', '1': 'FACTURA A',
            '06': 'FACTURA B', '6': 'FACTURA B',
            '11': 'FACTURA C', '11': 'FACTURA C',
            '03': 'NOTA CRED A', '3': 'NOTA CRED A',
            '08': 'NOTA CRED B', '8': 'NOTA CRED B',
            '13': 'NOTA CRED C', '13': 'NOTA CRED C'
        }
        
        # Convertir a string para buscar
        tipo_str = str(tipo)
        
        # Buscar primero el valor exacto, luego con cero adelante
        if tipo_str in tipos:
            return tipos[tipo_str]
        elif tipo_str.zfill(2) in tipos:  # Agregar cero adelante si es necesario
            return tipos[tipo_str.zfill(2)]
        else:
            return f'CBTE {tipo}'


    
    def imprimir_factura(self, factura):
        """Imprimir factura optimizada para EPSON TM-m30II"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")
            
            print(f"🖨️ INICIANDO IMPRESIÓN - Factura: {getattr(factura, 'numero', 'SIN_NUMERO')}")
            
            # Detectar si es EPSON TM-m30II
            es_epson_tm = 'epson tm-m30ii' in self.nombre_impresora.lower()
            
            if es_epson_tm:
                print("🎯 Usando configuración optimizada para EPSON TM-m30II")
            
            # Formatear contenido
            contenido = self.formatear_factura_termica(factura)
            print(f"📝 Contenido formateado: {len(contenido)} caracteres")
            
            # MÉTODO OPTIMIZADO PARA EPSON TM-m30II
            try:
                print("🔄 Método optimizado: win32print...")
                
                hPrinter = win32print.OpenPrinter(self.nombre_impresora)
                print("✅ Impresora abierta")
                
                try:
                    # Configuración específica para cada tipo de impresora
                    if es_epson_tm:
                        doc_type = "RAW"
                        job_name = f"Factura_EPSON_{getattr(factura, 'numero', 'XXX')}"
                    else:
                        doc_type = "TEXT"
                        job_name = f"Factura_{getattr(factura, 'numero', 'XXX')}"
                    
                    hJob = win32print.StartDocPrinter(hPrinter, 1, (job_name, None, doc_type))
                    print(f"✅ Documento iniciado (tipo: {doc_type})")
                    
                    try:
                        win32print.StartPagePrinter(hPrinter)
                        print("✅ Página iniciada")
                        
                        # Preparar datos según el tipo de impresora
                        if es_epson_tm:
                            # EPSON TM-m30II: Comandos ESC/POS
                            init_cmd = b'\x1B\x40'  # ESC @ - Inicializar
                            datos_bytes = init_cmd + contenido.encode('utf-8', errors='replace')
                            # Comando de corte automático
                            datos_bytes += b'\n\n\x1D\x56\x00'  # GS V 0 - Corte total
                        else:
                            # Otras impresoras: envío simple
                            datos_bytes = contenido.encode('utf-8', errors='replace')
                        
                        bytes_escritos = win32print.WritePrinter(hPrinter, datos_bytes)
                        print(f"✅ Datos enviados: {bytes_escritos} bytes")
                        
                        win32print.EndPagePrinter(hPrinter)
                        print("✅ Página completada")
                        
                        print("✅ *** IMPRESIÓN EXITOSA *** - Factura enviada a impresora")
                        return True
                        
                    finally:
                        win32print.EndDocPrinter(hPrinter)
                        print("✅ Documento finalizado")
                finally:
                    win32print.ClosePrinter(hPrinter)
                    print("✅ Impresora cerrada")
                    
            except Exception as e1:
                print(f"❌ MÉTODO OPTIMIZADO FALLÓ: {e1}")
                
                # MÉTODO FALLBACK: Archivo temporal
                try:
                    print("🔄 Método fallback: Archivo temporal...")
                    
                    import tempfile
                    import subprocess
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(contenido)
                        temp_path = temp_file.name
                    
                    cmd = f'print /D:"{self.nombre_impresora}" "{temp_path}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
                    
                    if result.returncode == 0:
                        print("✅ MÉTODO FALLBACK EXITOSO - Factura enviada")
                        
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                        
                        return True
                    else:
                        print(f"❌ MÉTODO FALLBACK FALLÓ: {result.stderr}")
                        
                except Exception as e2:
                    print(f"❌ MÉTODO FALLBACK FALLÓ: {e2}")
            
            print("❌ TODOS LOS MÉTODOS FALLARON")
            return False
            
        except Exception as e:
            print(f"❌ ERROR GENERAL en impresión: {e}")
            import traceback
            traceback.print_exc()
            return False


    def test_impresion(self):
        """Test de impresión optimizado para EPSON TM-m30II"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora")
                
            print(f"🧪 INICIANDO TEST - Impresora: {self.nombre_impresora}")
            
            # Detectar si es EPSON TM-m30II para usar configuración específica
            es_epson_tm = 'epson tm-m30ii' in self.nombre_impresora.lower()
            
            if es_epson_tm:
                print("🎯 Impresora EPSON TM-m30II detectada - usando configuración optimizada")
                
            contenido_test = """
    === PRUEBA DE IMPRESION ===

    Test de sistema POS
    Fecha: """ + datetime.now().strftime("%d/%m/%Y %H:%M") + """

    Impresora detectada:
    """ + self.nombre_impresora + """

    ------------------------------------------
    ESTADO: FUNCIONANDO CORRECTAMENTE
    ------------------------------------------

    *** EXITO ***




    """
            
            print(f"📝 Contenido creado: {len(contenido_test)} caracteres")
            
            # MÉTODO OPTIMIZADO PARA EPSON TM-m30II
            try:
                print("🔄 Método optimizado: win32print con RAW...")
                
                hPrinter = win32print.OpenPrinter(self.nombre_impresora)
                print("✅ Impresora abierta correctamente")
                
                try:
                    # Para EPSON TM-m30II usar RAW, para otras usar TEXT
                    doc_type = "RAW" if es_epson_tm else "TEXT"
                    job_name = "POS_Test_EPSON" if es_epson_tm else "POS_Test"
                    
                    hJob = win32print.StartDocPrinter(hPrinter, 1, (job_name, None, doc_type))
                    print(f"✅ Documento iniciado (tipo: {doc_type})")
                    
                    try:
                        win32print.StartPagePrinter(hPrinter)
                        print("✅ Página iniciada")
                        
                        # Para EPSON TM-m30II, agregar comandos ESC/POS básicos
                        if es_epson_tm:
                            # Comandos ESC/POS para EPSON
                            init_cmd = b'\x1B\x40'  # ESC @ - Inicializar
                            contenido_con_comandos = init_cmd + contenido_test.encode('utf-8', errors='replace')
                            # Agregar comando de corte de papel
                            contenido_con_comandos += b'\n\n\x1D\x56\x00'  # GS V 0 - Corte total
                            datos_bytes = contenido_con_comandos
                        else:
                            # Para otras impresoras, envío simple
                            datos_bytes = contenido_test.encode('utf-8', errors='replace')
                        
                        print(f"✅ Datos preparados: {len(datos_bytes)} bytes")
                        
                        bytes_escritos = win32print.WritePrinter(hPrinter, datos_bytes)
                        print(f"✅ Datos escritos: {bytes_escritos} bytes")
                        
                        win32print.EndPagePrinter(hPrinter)
                        print("✅ Página finalizada")
                        
                        print("✅ *** TEST EXITOSO *** - Impresión enviada correctamente")
                        return True
                        
                    except Exception as e3:
                        print(f"❌ Error en proceso de impresión: {e3}")
                        return False
                    finally:
                        try:
                            win32print.EndDocPrinter(hPrinter)
                            print("✅ Documento finalizado")
                        except Exception as e4:
                            print(f"⚠️ Error finalizando documento: {e4}")
                            
                finally:
                    try:
                        win32print.ClosePrinter(hPrinter)
                        print("✅ Impresora cerrada")
                    except Exception as e5:
                        print(f"⚠️ Error cerrando impresora: {e5}")
                        
            except Exception as e1:
                print(f"❌ MÉTODO OPTIMIZADO FALLÓ: {e1}")
                
                # FALLBACK: Método de archivo temporal
                try:
                    print("🔄 Método fallback: Archivo temporal...")
                    
                    import tempfile
                    import subprocess
                    
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(contenido_test)
                        temp_path = temp_file.name
                    
                    print(f"📁 Archivo temporal: {temp_path}")
                    
                    # Comando para enviar a impresora
                    cmd = f'print /D:"{self.nombre_impresora}" "{temp_path}"'
                    print(f"🔧 Comando: {cmd}")
                    
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0:
                        print("✅ MÉTODO FALLBACK EXITOSO")
                        
                        # Limpiar archivo
                        try:
                            os.unlink(temp_path)
                            print("🗑️ Archivo temporal eliminado")
                        except:
                            pass
                        
                        return True
                    else:
                        print(f"❌ MÉTODO FALLBACK FALLÓ: {result.stderr}")
                        
                except Exception as e2:
                    print(f"❌ MÉTODO FALLBACK FALLÓ: {e2}")
            
            # Si llegamos aquí, todos los métodos fallaron
            print("❌ TODOS LOS MÉTODOS FALLARON")
            return False
            
        except Exception as e:
            print(f"❌ ERROR GENERAL en test: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def verificar_estado(self):
        """Verificar el estado de la impresora"""
        try:
            if not self.nombre_impresora:
                return {
                    'disponible': False,
                    'error': 'Impresora no detectada',
                    'nombre': None,
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho
                }
            
            # Intentar obtener información de la impresora
            try:
                handle = win32print.OpenPrinter(self.nombre_impresora)
                info = win32print.GetPrinter(handle, 2)
                win32print.ClosePrinter(handle)
                
                estado = info['Status']
                estado_texto = "Lista" if estado == 0 else f"Estado: {estado}"
                
                return {
                    'disponible': True,
                    'nombre': self.nombre_impresora,
                    'estado': estado_texto,
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho
                }
            except Exception as e:
                # Si no puede obtener el estado pero la impresora existe, asumir que está disponible
                return {
                    'disponible': True,
                    'nombre': self.nombre_impresora,
                    'estado': 'Disponible (estado no verificable)',
                    'ancho_mm': self.ancho_mm,
                    'caracteres_linea': self.ancho,
                    'warning': str(e)
                }
                
        except Exception as e:
            logger.error(f"Error al verificar estado: {e}")
            return {
                'disponible': False,
                'error': str(e),
                'nombre': self.nombre_impresora,
                'ancho_mm': self.ancho_mm,
                'caracteres_linea': self.ancho
            }

    @staticmethod
    def listar_impresoras():
        """Listar todas las impresoras disponibles"""
        try:
            print("🖨️ Impresoras disponibles:")
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            for i, impresora in enumerate(impresoras, 1):
                print(f"   {i}. {impresora[2]}")
            
            # También listar impresoras de red
            try:
                impresoras_red = win32print.EnumPrinters(win32print.PRINTER_ENUM_NETWORK)
                if impresoras_red:
                    print("\n🌐 Impresoras de red:")
                    for i, impresora in enumerate(impresoras_red, 1):
                        print(f"   {i}. {impresora[2]}")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error listando impresoras: {e}")

# Instancia global de la impresora (80mm = 42 caracteres)
impresora_termica = ImpresoraTermica(ancho_mm=80)

# *** FUNCIONES PARA USAR EN FLASK ***
def obtener_estado_impresora():
    """Función para endpoint Flask"""
    return impresora_termica.verificar_estado()

def test_impresion():
    """Función para endpoint Flask"""
    resultado = impresora_termica.test_impresion()
    if resultado:
        return {
            'success': True,
            'mensaje': f'Test de impresión enviado correctamente a {impresora_termica.nombre_impresora}'
        }
    else:
        return {
            'success': False,
            'error': 'Error al enviar test de impresión'
        }

def imprimir_factura_termica(datos_factura):
    """Función para endpoint Flask - recibe datos en formato dict"""
    try:
        # Crear objeto factura simulado para compatibilidad
        class FacturaSimulada:
            def __init__(self, datos):
                self.numero = datos.get('numero', '0001-00000001')
                self.tipo_comprobante = datos.get('tipo_comprobante', '11')
                self.fecha = datetime.now()
                self.subtotal = datos.get('subtotal', 0)
                self.iva = datos.get('iva', 0)
                self.total = datos.get('total', 0)
                self.cae = datos.get('cae', None)
                self.vto_cae = datos.get('vto_cae', None)
                
                # Cliente simulado
                class ClienteSimulado:
                    def __init__(self, cliente_data):
                        if cliente_data:
                            self.nombre = cliente_data.get('nombre', 'Consumidor Final')
                            self.documento = cliente_data.get('documento', None)
                            self.tipo_documento = cliente_data.get('tipo_documento', 'DNI')
                        else:
                            self.nombre = 'Consumidor Final'
                            self.documento = None
                            self.tipo_documento = None
                
                self.cliente = ClienteSimulado(datos.get('cliente'))
                
                # Usuario simulado
                class UsuarioSimulado:
                    def __init__(self):
                        self.nombre = 'Sistema'
                
                self.usuario = UsuarioSimulado()
                
                # Detalles simulados
                class DetalleSimulado:
                    def __init__(self, item_data):
                        self.cantidad = item_data.get('cantidad', 1)
                        self.precio_unitario = item_data.get('precio_unitario', 0)
                        self.subtotal = item_data.get('subtotal', 0)
                        
                        # Producto simulado
                        class ProductoSimulado:
                            def __init__(self, item_data):
                                self.nombre = item_data.get('nombre', 'Producto')
                        
                        self.producto = ProductoSimulado(item_data)
                
                self.detalles = [DetalleSimulado(item) for item in datos.get('items', [])]
        
        # Crear factura simulada y imprimir
        factura_sim = FacturaSimulada(datos_factura)
        resultado = impresora_termica.imprimir_factura(factura_sim)
        
        if resultado:
            return {
                'success': True,
                'mensaje': f'Factura impresa correctamente en {impresora_termica.nombre_impresora}'
            }
        else:
            return {
                'success': False,
                'error': 'Error al imprimir factura'
            }
            
    except Exception as e:
        logger.error(f"Error en imprimir_factura_termica: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def imprimir_cartel_precio(self, producto, tiene_ofertas=False):
    """Imprimir cartel de precio individual para producto"""
    try:
        if not self.verificar_disponibilidad():
            print("Impresora no disponible para carteles")
            return False
        
        print(f"Imprimiendo cartel para: {producto.codigo}")
        
        # Preparar datos
        precio = float(producto.precio)
        nombre_corto = producto.nombre[:30] if len(producto.nombre) > 30 else producto.nombre
        descripcion_corta = ""
        if producto.descripcion:
            descripcion_corta = producto.descripcion[:35] if len(producto.descripcion) > 35 else producto.descripcion
        
        # Crear contenido del cartel
        contenido = []
        
        # Encabezado con nombre del negocio (opcional)
        contenido.append("=" * self.caracteres_linea)
        contenido.append("     PRECIO DE VENTA")
        contenido.append("=" * self.caracteres_linea)
        
        # Indicador de oferta
        if tiene_ofertas:
            contenido.append("")
            contenido.append("★" * self.caracteres_linea)
            contenido.append("        ¡OFERTA ESPECIAL!")
            contenido.append("★" * self.caracteres_linea)
        
        contenido.append("")
        
        # Nombre del producto (centrado y en negrita)
        nombre_centrado = nombre_corto.center(self.caracteres_linea)
        contenido.append(f"**{nombre_centrado}**")
        
        # Descripción si existe
        if descripcion_corta:
            contenido.append("")
            desc_centrada = descripcion_corta.center(self.caracteres_linea)
            contenido.append(desc_centrada)
        
        contenido.append("")
        contenido.append("-" * self.caracteres_linea)
        
        # Precio principal (grande y centrado)
        precio_texto = f"$ {precio:.2f}"
        precio_centrado = precio_texto.center(self.caracteres_linea)
        contenido.append("")
        contenido.append(f"**{precio_centrado}**")
        contenido.append("")
        
        contenido.append("-" * self.caracteres_linea)
        
        # Código del producto
        codigo_texto = f"Código: {producto.codigo}"
        codigo_centrado = codigo_texto.center(self.caracteres_linea)
        contenido.append(codigo_centrado)
        
        # Información adicional para ofertas
        if tiene_ofertas:
            if producto.es_combo and hasattr(producto, 'calcular_ahorro_combo'):
                ahorro = producto.calcular_ahorro_combo()
                if ahorro > 0:
                    contenido.append("")
                    ahorro_texto = f"Ahorro: $ {ahorro:.2f}"
                    ahorro_centrado = ahorro_texto.center(self.caracteres_linea)
                    contenido.append(ahorro_centrado)
        
        contenido.append("")
        contenido.append("=" * self.caracteres_linea)
        
        # Timestamp (opcional)
        from datetime import datetime
        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M")
        fecha_centrada = fecha_hora.center(self.caracteres_linea)
        contenido.append(fecha_centrada)
        
        contenido.append("=" * self.caracteres_linea)
        
        # Espacios finales para separar del siguiente cartel
        contenido.extend([""] * 3)
        
        # Unir todo el contenido
        texto_completo = "\n".join(contenido)
        
        # Enviar a impresora
        return self._enviar_texto_a_impresora(texto_completo)
        
    except Exception as e:
        print(f"Error imprimiendo cartel para {producto.codigo}: {e}")
        return False        