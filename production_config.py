# production_config.py - Configuración para Producción

import os
from datetime import timedelta

class ProductionConfig:
    """Configuración optimizada para producción"""
    
    # Seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CAMBIAR_EN_PRODUCCION_POR_CLAVE_SEGURA_LARGA'
    
    # Base de datos MySQL para producción
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'pos_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'TU_PASSWORD_SEGURA_AQUI'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'pos_argentina'
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Configuración de Flask para producción
    DEBUG = False
    TESTING = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/pos_produccion.log'

class ARCAProductionConfig:
    """Configuración ARCA/AFIP para PRODUCCIÓN"""
    
    # ⚠️ DATOS REALES DE TU EMPRESA - COMPLETAR
    CUIT = '20123456789'  # ⚠️ REEMPLAZAR CON TU CUIT REAL
    PUNTO_VENTA = 1       # ⚠️ TU PUNTO DE VENTA REAL
    RAZON_SOCIAL = 'TU RAZON SOCIAL SA'  # ⚠️ TU RAZÓN SOCIAL REAL
    
    # Certificados AFIP (ya los tienes)
    CERT_PATH = 'certificados/certificado.crt'
    KEY_PATH = 'certificados/private.key'
    
    # 🚨 PRODUCCIÓN - URLs REALES DE AFIP
    USE_HOMOLOGACION = False  # ¡IMPORTANTE! False para producción
    
    # URLs de AFIP PRODUCCIÓN
    WSAA_URL = 'https://wsaa.afip.gov.ar/ws/services/LoginCms'
    WSFEv1_URL = 'https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL'
    
    # Cache y seguridad
    TOKEN_CACHE_FILE = 'cache/token_arca_prod.json'
    TOKEN_BACKUP_FILE = 'cache/token_backup_prod.json'
    
    # Configuración de timeouts y reintentos
    REQUEST_TIMEOUT = 30  # segundos
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # segundos entre reintentos
    
    # Validaciones adicionales para producción
    VALIDATE_CERTIFICATES = True
    LOG_ALL_REQUESTS = True
    
    # Tipos de comprobante para producción
    TIPOS_COMPROBANTE_PROD = {
        '01': 'Factura A',
        '02': 'Nota de Débito A', 
        '03': 'Nota de Crédito A',
        '06': 'Factura B',
        '07': 'Nota de Débito B',
        '08': 'Nota de Crédito B', 
        '11': 'Factura C',
        '12': 'Nota de Débito C',
        '13': 'Nota de Crédito C'
    }

# Configuración de logging para producción
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/pos_produccion.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'afip_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/afip_produccion.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'detailed'
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        'app': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False
        },
        'afip': {
            'handlers': ['afip_file', 'console'],
            'level': 'DEBUG',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}