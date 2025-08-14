
# REEMPLAZAR la clase ARCAClient en tu app.py por esta versión SSL-FIXED:

import ssl
import urllib3
from urllib3.util.ssl_ import create_urllib3_context

class ARCAClient:
    def __init__(self):
        self.config = ARCA_CONFIG
        self.token = None
        self.sign = None
        self.openssl_path = './openssl.exe'
        
        # Configurar SSL para AFIP
        self._configure_ssl()
        
        print(f"🔧 AFIP Client Simple inicializado")
        print(f"   CUIT: {self.config.CUIT}")
        print(f"   Ambiente: {'HOMOLOGACIÓN' if self.config.USE_HOMOLOGACION else 'PRODUCCIÓN'}")
    
    def _configure_ssl(self):
        """Configurar SSL para compatibilidad con AFIP"""
        import os
        import ssl
        import urllib3
        
        # Configurar OpenSSL
        os.environ['OPENSSL_CONF'] = ''
        
        # Desactivar advertencias SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configurar SSL global
        ssl._create_default_https_context = ssl._create_unverified_context
    
    def _create_zeep_transport(self):
        """Crear transporte ZEEP con SSL personalizado"""
        from zeep.transports import Transport
        import ssl
        
        # Contexto SSL personalizado
        ctx = ssl.create_default_context()
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        return Transport(timeout=60)
    
    def verificar_openssl(self):
        """Verificar que OpenSSL esté disponible - VERSIÓN CORREGIDA"""
        try:
            import subprocess
            
            # PRIMERO: Probar OpenSSL local (en el directorio del proyecto)
            if os.path.exists('./openssl.exe'):
                try:
                    result = subprocess.run(['./openssl.exe', 'version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"✅ OpenSSL local encontrado: {result.stdout.strip()}")
                        self.openssl_path = './openssl.exe'
                        return True
                except Exception as e:
                    print(f"⚠️ Error con OpenSSL local: {e}")
            
            # SEGUNDO: Probar ruta completa conocida
            ruta_conocida = r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"
            if os.path.exists(ruta_conocida):
                try:
                    result = subprocess.run([ruta_conocida, 'version'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        print(f"✅ OpenSSL encontrado en ruta completa: {result.stdout.strip()}")
                        self.openssl_path = ruta_conocida
                        return True
                except Exception as e:
                    print(f"⚠️ Error con ruta completa: {e}")
            
            # TERCERO: Probar comando directo
            try:
                result = subprocess.run(['openssl', 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"✅ OpenSSL encontrado en PATH: {result.stdout.strip()}")
                    self.openssl_path = 'openssl'
                    return True
            except Exception as e:
                print(f"⚠️ Error con comando directo: {e}")
            
            print("❌ OpenSSL no encontrado en ninguna ubicación")
            return False
            
        except Exception as e:
            print(f"❌ Error verificando OpenSSL: {e}")
            return False
    
    def crear_tra(self):
        """Crear Ticket Request Access"""
        now = datetime.utcnow()
        expire = now + timedelta(hours=12)
        unique_id = int(now.timestamp())
        
        tra_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
    <header>
        <uniqueId>{unique_id}</uniqueId>
        <generationTime>{now.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</generationTime>
        <expirationTime>{expire.strftime('%Y-%m-%dT%H:%M:%S.000-00:00')}</expirationTime>
    </header>
    <service>wsfe</service>
</loginTicketRequest>"""
        
        return tra_xml
    
    def firmar_tra_openssl(self, tra_xml):
        """Firmar TRA usando OpenSSL - VERSIÓN MEJORADA"""
        try:
            import tempfile
            import subprocess
            import base64
            
            print(f"🔐 Firmando TRA con OpenSSL: {self.openssl_path}")
            
            # Crear archivos temporales
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tra_file:
                tra_file.write(tra_xml)
                tra_temp = tra_file.name
            
            with tempfile.NamedTemporaryFile(suffix='.cms', delete=False) as cms_file:
                cms_temp = cms_file.name
            
            # Comando OpenSSL
            cmd = [
                self.openssl_path, 'smime', '-sign',
                '-in', tra_temp,
                '-out', cms_temp,
                '-signer', self.config.CERT_PATH,
                '-inkey', self.config.KEY_PATH,
                '-outform', 'DER',
                '-nodetach'
            ]
            
            print(f"📝 Ejecutando firma...")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"❌ Error OpenSSL: {result.stderr}")
                raise Exception(f"Error OpenSSL: {result.stderr}")
            
            # Leer archivo firmado
            with open(cms_temp, 'rb') as f:
                cms_data = f.read()
            
            # Limpiar archivos temporales
            os.unlink(tra_temp)
            os.unlink(cms_temp)
            
            # Codificar en base64
            cms_b64 = base64.b64encode(cms_data).decode('utf-8')
            
            print("✅ TRA firmado correctamente")
            return cms_b64
            
        except Exception as e:
            print(f"❌ Error firmando TRA: {e}")
            raise Exception(f"Error firmando TRA: {e}")
    
    def get_ticket_access(self):
        """Obtener ticket de acceso de WSAA"""
        try:
            print("🎫 Obteniendo ticket de acceso...")
            
            # Verificar certificados
            if not os.path.exists(self.config.CERT_PATH):
                raise Exception(f"Certificado no encontrado: {self.config.CERT_PATH}")
            
            if not os.path.exists(self.config.KEY_PATH):
                raise Exception(f"Clave privada no encontrada: {self.config.KEY_PATH}")
            
            # Verificar OpenSSL
            if not self.verificar_openssl():
                raise Exception("OpenSSL no disponible")
            
            # Crear y firmar TRA
            tra_xml = self.crear_tra()
            tra_firmado = self.firmar_tra_openssl(tra_xml)
            
            # Conectar con WSAA
            wsaa_url = 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl' if self.config.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
            
            print("🌐 Conectando con WSAA...")
            from zeep import Client
            
            # Usar transporte SSL personalizado
            transport = self._create_zeep_transport()
            client = Client(wsaa_url, transport=transport)
            
            # Enviar solicitud
            response = client.service.loginCms(tra_firmado)
            
            if response:
                # Procesar respuesta XML
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response)
                
                token_elem = root.find('.//token')
                sign_elem = root.find('.//sign')
                
                if token_elem is None or sign_elem is None:
                    raise Exception("Token o Sign no encontrados en respuesta")
                
                self.token = token_elem.text
                self.sign = sign_elem.text
                
                print("✅ Ticket de acceso obtenido")
                return True
            else:
                raise Exception("Respuesta vacía de WSAA")
                
        except Exception as e:
            print(f"❌ Error obteniendo ticket: {e}")
            return False
    
    def get_ultimo_comprobante(self, tipo_cbte):
        """Obtener último comprobante autorizado"""
        try:
            print(f"📋 Consultando último comprobante tipo {tipo_cbte}...")
            
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener acceso a AFIP")
            
            wsfe_url = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.config.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
            
            from zeep import Client
            
            # Usar transporte SSL personalizado
            transport = self._create_zeep_transport()
            client = Client(wsfe_url, transport=transport)
            
            response = client.service.FECompUltimoAutorizado(
                Auth={
                    'Token': self.token,
                    'Sign': self.sign,
                    'Cuit': self.config.CUIT
                },
                PtoVta=self.config.PUNTO_VENTA,
                CbteTipo=tipo_cbte
            )
            
            if hasattr(response, 'Errors') and response.Errors:
                error_msg = response.Errors.Err[0].Msg
                raise Exception(f"Error AFIP: {error_msg}")
            
            ultimo_num = response.CbteNro
            print(f"✅ Último comprobante: {ultimo_num}")
            return ultimo_num
            
        except Exception as e:
            print(f"❌ Error consultando comprobante: {e}")
            raise Exception(f"Error al obtener último comprobante: {e}")
    
    def autorizar_comprobante(self, factura_data):
        """Autorizar comprobante en AFIP"""
        try:
            print(f"📄 Autorizando comprobante {factura_data['numero']}...")
            
            if not self.get_ticket_access():
                raise Exception("No se pudo obtener acceso a AFIP")
            
            wsfe_url = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.config.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
            
            from zeep import Client
            
            # Usar transporte SSL personalizado
            transport = self._create_zeep_transport()
            client = Client(wsfe_url, transport=transport)
            
            # Preparar datos
            cliente_cuit = factura_data.get('cliente_cuit', '0')
            if cliente_cuit and cliente_cuit != '0' and len(cliente_cuit) == 11:
                tipo_doc = 80  # CUIT
                nro_doc = int(cliente_cuit)
            else:
                tipo_doc = 99  # Sin identificar
                nro_doc = 0
            
            cbte_data = {
                'CbteTipo': factura_data['tipo_comprobante'],
                'PtoVta': self.config.PUNTO_VENTA,
                'Concepto': 1,  # Productos
                'DocTipo': tipo_doc,
                'DocNro': nro_doc,
                'CbteDesde': factura_data['numero'],
                'CbteHasta': factura_data['numero'],
                'CbteFch': factura_data['fecha'].strftime('%Y%m%d'),
                'ImpTotal': float(factura_data['total']),
                'ImpTotConc': 0,
                'ImpNeto': float(factura_data['subtotal']),
                'ImpOpEx': 0,
                'ImpIVA': float(factura_data['iva']),
                'ImpTrib': 0,
                'MonId': 'PES',
                'MonCotiz': 1
            }
            
            # Enviar solicitud
            response = client.service.FECAESolicitar(
                Auth={
                    'Token': self.token,
                    'Sign': self.sign,
                    'Cuit': self.config.CUIT
                },
                FeCAEReq={
                    'FeCabReq': {
                        'CantReg': 1,
                        'PtoVta': self.config.PUNTO_VENTA,
                        'CbteTipo': factura_data['tipo_comprobante']
                    },
                    'FeDetReq': {
                        'FECAEDetRequest': [cbte_data]
                    }
                }
            )
            
            # Verificar errores
            if hasattr(response, 'Errors') and response.Errors:
                error_msg = response.Errors.Err[0].Msg
                raise Exception(f"Error AFIP: {error_msg}")
            
            result = response.FeDetResp.FECAEDetResponse[0]
            
            if result.Resultado == 'A':
                print(f"✅ Comprobante autorizado - CAE: {result.CAE}")
                return {
                    'cae': result.CAE,
                    'vto_cae': datetime.strptime(result.CAEFchVto, '%Y%m%d').date(),
                    'estado': 'autorizada'
                }
            else:
                print(f"❌ Comprobante rechazado")
                return {
                    'cae': None,
                    'vto_cae': None,
                    'estado': 'rechazada'
                }
                
        except Exception as e:
            print(f"❌ Error autorizando comprobante: {e}")
            raise Exception(f"Error al autorizar comprobante: {e}")
