#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración local del sistema POS AFIP
Archivo generado automáticamente el 2025-09-04 13:02:41
"""

class Config:
    """Configuración de Flask"""
    SECRET_KEY = 'tu_clave_secreta_20250904'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://pos_user:pos_password@localhost/factufacil'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración adicional
    DEBUG = True
    TESTING = False

class ARCAConfig:
    """Configuración de AFIP/ARCA"""
    
    # Datos de la empresa
    CUIT = '20203852100'
    PUNTO_VENTA = 3
    
    # Ambiente (True = Homologación, False = Producción)
    USE_HOMOLOGACION = True
    
    # Certificados digitales - DINÁMICOS según ambiente
    @property
    def CERT_PATH(self):
        if self.USE_HOMOLOGACION:
            return 'certificados/homo_certificado.crt'
        else:
            return 'certificados/certificado.crt'
    
    @property
    def KEY_PATH(self):
        if self.USE_HOMOLOGACION:
            return 'certificados/homo_private.key'
        else:
            return 'certificados/private.key'
    
    # URLs de servicios AFIP
    @property
    def WSAA_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
        else:
            return 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
    
    @property
    def WSFEv1_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
        else:
            return 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # Cache de tokens
    TOKEN_CACHE_FILE = 'cache/token_afip.json'
    
    # Logging
    LOG_FILE = 'logs/afip.log'
    #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración local del sistema POS AFIP
Archivo generado automáticamente el 2025-09-04 13:02:41
"""

class Config:
    """Configuración de Flask"""
    SECRET_KEY = 'tu_clave_secreta_20250904'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://pos_user:pos_password@localhost/pos_argentina'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración adicional
    DEBUG = True
    TESTING = False

class ARCAConfig:
    """Configuración de AFIP/ARCA"""
    
    # Datos de la empresa
    CUIT = '20203852100'
    PUNTO_VENTA = 3  
    
    # Ambiente (True = Homologación, False = Producción)
    USE_HOMOLOGACION = True
    
    # Certificados digitales - DINÁMICOS según ambiente
    @property
    def CERT_PATH(self):
        if self.USE_HOMOLOGACION:
            return 'certificados/homo_certificado.crt'
        else:
            return 'certificados/certificado.crt'
    
    @property
    def KEY_PATH(self):
        if self.USE_HOMOLOGACION:
            return 'certificados/homo_private.key'
        else:
            return 'certificados/private.key'
    
    # URLs de servicios AFIP
    @property
    def WSAA_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl'
        else:
            return 'https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl'
    
    @property
    def WSFEv1_URL(self):
        if self.USE_HOMOLOGACION:
            return 'https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL'
        else:
            return 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # Cache de tokens
    TOKEN_CACHE_FILE = 'cache/token_afip.json'
    
    # Logging
    LOG_FILE = 'logs/afip.log'
    LOG_LEVEL = 'DEBUG' if USE_HOMOLOGACION else 'INFO'