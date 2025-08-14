# config.py - Configuración de la base de datos MySQL

import os
from datetime import timedelta

class Config:
    # Clave secreta para sesiones
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta_muy_segura_aqui'
    
    # Configuración MySQL
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'pos_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'pos_password'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'pos_argentina'
    
    # URI de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

class ARCAConfig:
    """Configuración para AFIP/ARCA"""
    
    # DATOS DE TU EMPRESA - CAMBIAR POR TUS DATOS REALES
    CUIT = '20203852100'  # TU CUIT AQUÍ
    PUNTO_VENTA = 3       # TU PUNTO DE VENTA
    RAZON_SOCIAL = 'PABLO GUSTAVO RE'
    
    # RUTAS DE CERTIFICADOS
    CERT_PATH = os.path.join('certificados', 'certificado.crt')
    KEY_PATH = os.path.join('certificados', 'private.key')
    
    # URLs DE AFIP
    # HOMOLOGACIÓN (para pruebas)
    WSAA_URL_HOMO = 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms'
    WSFEv1_URL_HOMO = 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # PRODUCCIÓN (para uso real)
    WSAA_URL_PROD = 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    WSFEv1_URL_PROD = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # USAR HOMOLOGACIÓN POR DEFECTO (cambiar a False para producción)
    USE_HOMOLOGACION = False
    
    @property
    def WSAA_URL(self):
        return self.WSAA_URL_HOMO if self.USE_HOMOLOGACION else self.WSAA_URL_PROD
    
    @property
    def WSFEv1_URL(self):
        return self.WSFEv1_URL_HOMO if self.USE_HOMOLOGACION else self.WSFEv1_URL_PROD
    
    # ARCHIVO DE CACHE PARA TOKENS
    TOKEN_CACHE_FILE = 'cache/token_arca.json'
    
    # TIPOS DE COMPROBANTE
    TIPOS_COMPROBANTE = {
        '01': 'Factura A',
        '02': 'Nota de Débito A',
        '03': 'Nota de Crédito A',
        '06': 'Factura B',
        '07': 'Nota de Débito B',
        '08': 'Nota de Crédito B',
        '11': 'Factura C',
        '12': 'Nota de Débito C',
        '13': 'Nota de Crédito C',
    }
    
    # TIPOS DE DOCUMENTO
    TIPOS_DOCUMENTO = {
        '80': 'CUIT',
        '86': 'CUIL',
        '96': 'DNI',
        '99': 'Sin identificar/venta global diaria'
    }
    
    # CONDICIONES IVA
    CONDICIONES_IVA = {
        'IVA_RESPONSABLE_INSCRIPTO': 1,
        'IVA_RESPONSABLE_NO_INSCRIPTO': 2,
        'IVA_NO_RESPONSABLE': 3,
        'IVA_SUJETO_EXENTO': 4,
        'CONSUMIDOR_FINAL': 5,
        'RESPONSABLE_MONOTRIBUTO': 6,
        'SUJETO_NO_CATEGORIZADO': 7,
        'PROVEEDOR_DEL_EXTERIOR': 8,
        'CLIENTE_DEL_EXTERIOR': 9,
        'IVA_LIBERADO_LEY_19640': 10,
        'IVA_RESPONSABLE_INSCRIPTO_AGENTE_PERCEPCION': 11,
        'PEQUENO_CONTRIBUYENTE_EVENTUAL': 12,
        'MONOTRIBUTISTA_SOCIAL': 13,
        'PEQUENO_CONTRIBUYENTE_EVENTUAL_SOCIAL': 14
    }