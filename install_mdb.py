# config_local.py - Configuración manual para tu BD existente

import os

class Config:
    SECRET_KEY = 'tu_clave_secreta_cambiar_en_produccion'
    
    # Configuración MySQL - CAMBIAR POR TUS DATOS
    MYSQL_HOST = 'localhost'
    MYSQL_PORT = 3306
    MYSQL_USER = 'pos_user'
    MYSQL_PASSWORD = 'cl1v2'  # Tu contraseña
    MYSQL_DATABASE = 'pos_argentina'
    
    # URI de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ARCAConfig:
    # CAMBIAR POR TUS DATOS REALES PARA PRODUCCIÓN
    CUIT = '20123456789'  # ⚠️ TU CUIT AQUÍ
    PUNTO_VENTA = 1       # ⚠️ TU PUNTO DE VENTA
    RAZON_SOCIAL = 'MI EMPRESA SRL'  # ⚠️ TU RAZÓN SOCIAL
    
    # Certificados AFIP
    CERT_PATH = 'certificados/certificado.crt'
    KEY_PATH = 'certificados/private.key'
    
    # HOMOLOGACIÓN vs PRODUCCIÓN
    USE_HOMOLOGACION = True  # True = pruebas, False = producción real
    
    # URLs automáticas según ambiente
    @property
    def WSAA_URL(self):
        return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms' if self.USE_HOMOLOGACION else 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    
    @property
    def WSFEv1_URL(self):
        return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL' if self.USE_HOMOLOGACION else 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    TOKEN_CACHE_FILE = 'cache/token_arca.json'