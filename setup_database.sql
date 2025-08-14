-- setup_database.sql
-- Script para crear la base de datos y usuario para el POS Argentina

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS pos_argentina CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario para la aplicación
CREATE USER IF NOT EXISTS 'pos_user'@'localhost' IDENTIFIED BY 'pos_password';

-- Otorgar permisos
GRANT ALL PRIVILEGES ON pos_argentina.* TO 'pos_user'@'localhost';
FLUSH PRIVILEGES;

-- Usar la base de datos
USE pos_argentina;

-- Crear tabla de usuarios
CREATE TABLE IF NOT EXISTS usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    rol VARCHAR(50) DEFAULT 'vendedor',
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla de clientes
CREATE TABLE IF NOT EXISTS cliente (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    documento VARCHAR(20),
    tipo_documento VARCHAR(10) DEFAULT 'DNI',
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    condicion_iva VARCHAR(50) DEFAULT 'CONSUMIDOR_FINAL',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_documento (documento)
);

-- Crear tabla de productos
CREATE TABLE IF NOT EXISTS producto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    stock INT DEFAULT 0,
    categoria VARCHAR(100),
    iva DECIMAL(5, 2) DEFAULT 21.00,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_codigo (codigo),
    INDEX idx_nombre (nombre),
    INDEX idx_categoria (categoria)
);

-- Crear tabla de facturas
CREATE TABLE IF NOT EXISTS factura (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero VARCHAR(50) UNIQUE NOT NULL,
    tipo_comprobante VARCHAR(10) DEFAULT '01',