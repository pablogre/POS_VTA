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
        
    def _buscar_impresora_termica(self):
        """Buscar impresora térmica automáticamente"""
        try:
            impresoras = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL)
            
            # Nombres comunes de impresoras térmicas - EPSON TM-M30II específicamente
            nombres_termicas = [
                'tm-m30ii', 'tm-m30', 'epson tm-m30ii', 'epson tm-m30',
                'thermal', 'receipt', 'pos', 'tm-', 'rp-', 'sp-',
                'termica', 'ticket', 'epson', 'star', 'citizen',
                'xprinter', 'godex', 'zebra', 'bixolon'
            ]
            
            for impresora in impresoras:
                nombre = impresora[2].lower()
                for termico in nombres_termicas:
                    if termico in nombre:
                        print(f"🖨️ Impresora térmica detectada: {impresora[2]}")
                        return impresora[2]
            
            # Si no encuentra térmica, usar impresora por defecto
            try:
                impresora_default = win32print.GetDefaultPrinter()
                print(f"🖨️ Usando impresora por defecto: {impresora_default}")
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
        """Formatear factura para impresión térmica de 80mm con QR AFIP"""
        lineas = []
        
        print("🔍 DEBUG - Iniciando formateo de factura")
        print(f"   Factura número: {getattr(factura, 'numero', 'SIN NUMERO')}")
        print(f"   Cliente: {getattr(factura.cliente, 'nombre', 'SIN CLIENTE') if hasattr(factura, 'cliente') and factura.cliente else 'SIN CLIENTE'}")
        print(f"   Detalles: {len(factura.detalles) if hasattr(factura, 'detalles') else 0}")
        
        try:
            # ENCABEZADO
            lineas.append("")
            lineas.append(self.centrar_texto("TU EMPRESA S.A."))
            lineas.append(self.centrar_texto("CUIT: 20-20385210-0"))
            lineas.append(self.centrar_texto("Dir: Tu Direccion 123"))
            lineas.append(self.centrar_texto("Tel: (011) 1234-5678"))
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
                        cant_str = f"{int(detalle.cantidad)}"
                        precio_str = f"{float(detalle.precio_unitario):,.0f}"
                        total_str = f"{float(detalle.subtotal):,.0f}"
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
            
            # TOTALES
            try:
                subtotal = float(getattr(factura, 'subtotal', 0))
                iva = float(getattr(factura, 'iva', 0))
                total = float(getattr(factura, 'total', 0))
                
                lineas.append(self.justificar_texto("SUBTOTAL:", f"${subtotal:,.2f}"))
                if iva > 0:
                    lineas.append(self.justificar_texto("IVA 21%:", f"${iva:,.2f}"))
                lineas.append(self.linea_separadora())
                lineas.append(self.justificar_texto("TOTAL:", f"${total:,.2f}"))
            except (ValueError, AttributeError) as e:
                print(f"⚠️ Error formateando totales: {e}")
                lineas.append(self.justificar_texto("TOTAL:", "$0.00"))
            
            lineas.append(self.linea_separadora())
            
            # INFORMACIÓN AFIP CON QR
            cae = getattr(factura, 'cae', None)
            if cae:
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
                
                # *** CÓDIGO QR AFIP ***
                try:
                    # Intentar importar el módulo QR
                    from qr_afip import crear_generador_qr
                    generador_qr = crear_generador_qr()
                    info_qr = generador_qr.obtener_info_qr(factura)
                    
                    if info_qr['valido']:
                        lineas.append("")
                        lineas.append(self.centrar_texto("--- CODIGO QR AFIP ---"))
                        
                        # Generar QR en ASCII
                        qr_ascii = generador_qr.generar_qr_ascii(factura)
                        if qr_ascii:
                            # Dividir QR en líneas y centrar
                            lineas_qr = qr_ascii.split('\n')
                            for linea_qr in lineas_qr:
                                # Truncar si es muy ancho para la impresora
                                if len(linea_qr) > self.ancho:
                                    linea_qr = linea_qr[:self.ancho]
                                lineas.append(linea_qr)
                        else:
                            # Fallback: mostrar URL
                            lineas.append(self.centrar_texto("QR: Ver en factura web"))
                        
                        lineas.append("")
                        lineas.append(self.centrar_texto("Escanear para verificar"))
                        lineas.append(self.centrar_texto("en www.afip.gob.ar"))
                    else:
                        lineas.append("")
                        lineas.append(self.centrar_texto("QR no disponible"))
                        lineas.append(self.centrar_texto(info_qr['mensaje']))
                except ImportError:
                    # Si no está disponible el módulo QR, continuar sin QR
                    lineas.append("")
                    lineas.append(self.centrar_texto("QR: Modulo no disponible"))
                    print("⚠️ Módulo QR no disponible")
                except Exception as e:
                    print(f"⚠️ Error generando QR: {e}")
                    lineas.append("")
                    lineas.append(self.centrar_texto("QR: Error al generar"))
                
            else:
                lineas.append("")
                lineas.append(self.centrar_texto("*** NO AUTORIZADO ***"))
                lineas.append(self.centrar_texto("VERIFICAR AFIP"))
            
            # PIE DE PÁGINA
            lineas.append("")
            lineas.append(self.centrar_texto("Gracias por su compra"))
            lineas.append("")
            lineas.append("")
            lineas.append("")  # Espacio para cortar
            
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
            
            # Generar info del QR para mostrar en web
            try:
                from qr_afip import crear_generador_qr
                generador_qr = crear_generador_qr()
                info_qr = generador_qr.obtener_info_qr(factura)
            except ImportError:
                info_qr = {'valido': False, 'mensaje': 'Módulo QR no disponible'}
            
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
            '01': 'FACTURA A',
            '06': 'FACTURA B', 
            '11': 'FACTURA C',
            '03': 'NOTA CRED A',
            '08': 'NOTA CRED B',
            '13': 'NOTA CRED C'
        }
        return tipos.get(str(tipo), f'CBTE {tipo}')

        
    
    def imprimir_factura(self, factura):
        """Imprimir factura - MÉTODO SÚPER SIMPLE"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora térmica")
            
            print(f"🖨️ INICIANDO IMPRESIÓN - Factura: {getattr(factura, 'numero', 'SIN_NUMERO')}")
            
            # Formatear contenido
            contenido = self.formatear_factura_termica(factura)
            print(f"📝 Contenido formateado: {len(contenido)} caracteres")
            
            # MÉTODO 1: win32print directo
            try:
                print("🔄 Método 1: win32print directo...")
                
                hPrinter = win32print.OpenPrinter(self.nombre_impresora)
                
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, (f"Factura_{getattr(factura, 'numero', 'XXX')}", None, "RAW"))
                    
                    try:
                        win32print.StartPagePrinter(hPrinter)
                        
                        # Enviar datos como UTF-8
                        datos_bytes = contenido.encode('utf-8', errors='replace')
                        bytes_escritos = win32print.WritePrinter(hPrinter, datos_bytes)
                        
                        win32print.EndPagePrinter(hPrinter)
                        
                        print(f"✅ MÉTODO 1 EXITOSO - Factura enviada: {bytes_escritos} bytes")
                        return True
                        
                    finally:
                        win32print.EndDocPrinter(hPrinter)
                finally:
                    win32print.ClosePrinter(hPrinter)
                    
            except Exception as e1:
                print(f"❌ MÉTODO 1 FALLÓ: {e1}")
                
                # MÉTODO 2: Archivo temporal
                try:
                    print("🔄 Método 2: Archivo temporal...")
                    
                    import tempfile
                    import subprocess
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(contenido)
                        temp_path = temp_file.name
                    
                    cmd = f'type "{temp_path}" > "{self.nombre_impresora}"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0:
                        print("✅ MÉTODO 2 EXITOSO - Factura enviada")
                        
                        try:
                            os.unlink(temp_path)
                        except:
                            pass
                        
                        return True
                    else:
                        print(f"❌ MÉTODO 2 FALLÓ: {result.stderr}")
                        
                except Exception as e2:
                    print(f"❌ MÉTODO 2 FALLÓ: {e2}")
            
            print("❌ TODOS LOS MÉTODOS FALLARON")
            return False
            
        except Exception as e:
            print(f"❌ ERROR GENERAL en impresión: {e}")
            import traceback
            traceback.print_exc()
            return False        

    def test_impresion(self):
        """Test de impresión - MÉTODO SÚPER SIMPLE"""
        try:
            if not self.nombre_impresora:
                raise Exception("No se encontró impresora")
                
            print(f"🧪 INICIANDO TEST - Impresora: {self.nombre_impresora}")
            
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
            
            # MÉTODO 1: Intentar win32print directo
            try:
                print("🔄 Método 1: win32print directo...")
                
                hPrinter = win32print.OpenPrinter(self.nombre_impresora)
                print("✅ Impresora abierta correctamente")
                
                try:
                    hJob = win32print.StartDocPrinter(hPrinter, 1, ("POS_Test", None, "RAW"))
                    print("✅ Documento iniciado")
                    
                    try:
                        win32print.StartPagePrinter(hPrinter)
                        print("✅ Página iniciada")
                        
                        # Enviar datos como bytes
                        datos_bytes = contenido_test.encode('utf-8', errors='replace')
                        print(f"✅ Datos convertidos: {len(datos_bytes)} bytes")
                        
                        bytes_escritos = win32print.WritePrinter(hPrinter, datos_bytes)
                        print(f"✅ Datos escritos: {bytes_escritos} bytes")
                        
                        win32print.EndPagePrinter(hPrinter)
                        print("✅ Página finalizada")
                        
                        print("✅ MÉTODO 1 EXITOSO - Test enviado correctamente")
                        return True
                        
                    except Exception as e3:
                        print(f"❌ Error en escritura: {e3}")
                        raise e3
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
                print(f"❌ MÉTODO 1 FALLÓ: {e1}")
                
                # MÉTODO 2: Fallback con archivo temporal
                try:
                    print("🔄 Método 2: Archivo temporal...")
                    
                    import tempfile
                    import subprocess
                    
                    # Crear archivo temporal
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                        temp_file.write(contenido_test)
                        temp_path = temp_file.name
                    
                    print(f"📁 Archivo temporal: {temp_path}")
                    
                    # Comando para enviar a impresora
                    cmd = f'type "{temp_path}" > "{self.nombre_impresora}"'
                    print(f"🔧 Comando: {cmd}")
                    
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        print("✅ MÉTODO 2 EXITOSO - Comando ejecutado")
                        
                        # Limpiar archivo
                        try:
                            os.unlink(temp_path)
                            print("🗑️ Archivo temporal eliminado")
                        except:
                            pass
                        
                        return True
                    else:
                        print(f"❌ MÉTODO 2 FALLÓ: {result.stderr}")
                        
                except Exception as e2:
                    print(f"❌ MÉTODO 2 FALLÓ: {e2}")
            
            # Si llegamos aquí, ambos métodos fallaron
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