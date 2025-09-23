# generar_csr_manual.py
import subprocess
import os

def generar_certificados():
    print("Generando certificados de homologación...")
    print("Titular: Pablo Gustavo Ré")
    print("CUIT: 20203852100")
    print("Ubicación: San Nicolás de los Arroyos, Buenos Aires")
    
    # Crear directorio
    os.makedirs('certificados', exist_ok=True)
    
    # Verificar OpenSSL
    openssl_path = './openssl.exe'
    if not os.path.exists(openssl_path):
        openssl_path = 'openssl'
    
    try:
        # 1. Generar clave privada
        print("1. Generando clave privada...")
        subprocess.run([
            openssl_path, 'genrsa', 
            '-out', 'certificados/homo_private.key', 
            '2048'
        ], check=True)
        
        # 2. Generar CSR con datos correctos
        print("2. Generando CSR...")
        subprocess.run([
            openssl_path, 'req', '-new',
            '-key', 'certificados/homo_private.key',
            '-out', 'certificados/homo_certificado.csr',
            '-subj', '/C=AR/ST=Buenos Aires/L=San Nicolas de los Arroyos/O=Pablo Gustavo Re/OU=IT/CN=CUIT20203852100'
        ], check=True)
        
        print("\nArchivos generados:")
        print("- certificados/homo_private.key")
        print("- certificados/homo_certificado.csr")
        print("\nDatos del certificado:")
        print("- Titular: Pablo Gustavo Ré")
        print("- CUIT: 20203852100")
        print("- Ubicación: San Nicolás de los Arroyos, Buenos Aires")
        print("\nSube el archivo .csr al portal de AFIP")
        
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print("OpenSSL no encontrado. Usa los comandos manuales.")

if __name__ == "__main__":
    generar_certificados()