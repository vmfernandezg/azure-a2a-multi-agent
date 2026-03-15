#!/usr/bin/env python3
"""
Script para verificar el registro SOA y certificados SSL de ferrovial.com

Uso:
    pip install dnspython
    python check_ferrovial_dns.py

Verifica:
  1. Registro SOA (Start of Authority)
  2. Registros NS (Nameservers)
  3. Registros CAA (Certificate Authority Authorization)
  4. Certificado SSL/TLS actual (issuer/CA)
  5. Registros TXT
  6. Registros MX
"""

import subprocess
import sys
import ssl
import socket
import json
from datetime import datetime


def check_dns_with_module(domain: str):
    """Consulta registros DNS usando dnspython."""
    try:
        import dns.resolver
    except ImportError:
        print("[!] dnspython no instalado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "dnspython", "-q"])
        import dns.resolver

    print(f"\n{'='*70}")
    print(f"  VERIFICACION DNS COMPLETA: {domain}")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")

    # 1. SOA Record
    print(f"\n{'─'*70}")
    print("  1. REGISTRO SOA (Start of Authority)")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'SOA')
        for rdata in answers:
            print(f"  Primary NS (MNAME) : {rdata.mname}")
            print(f"  Admin Email (RNAME): {rdata.rname}")
            print(f"  Serial             : {rdata.serial}")
            print(f"  Refresh            : {rdata.refresh} segundos")
            print(f"  Retry              : {rdata.retry} segundos")
            print(f"  Expire             : {rdata.expire} segundos")
            print(f"  Minimum TTL        : {rdata.minimum} segundos")
    except dns.resolver.NoAnswer:
        print("  [!] No se encontró registro SOA")
    except dns.resolver.NXDOMAIN:
        print("  [!] El dominio no existe")
    except Exception as e:
        print(f"  [!] Error: {e}")

    # 2. NS Records
    print(f"\n{'─'*70}")
    print("  2. REGISTROS NS (Nameservers)")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        for i, rdata in enumerate(answers, 1):
            print(f"  NS {i}: {rdata}")
    except Exception as e:
        print(f"  [!] Error: {e}")

    # 3. CAA Records
    print(f"\n{'─'*70}")
    print("  3. REGISTROS CAA (Certificate Authority Authorization)")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'CAA')
        sectigo_found = False
        for rdata in answers:
            ca_info = str(rdata)
            print(f"  CAA: {ca_info}")
            if 'sectigo' in ca_info.lower() or 'comodo' in ca_info.lower():
                sectigo_found = True
        if sectigo_found:
            print("\n  [OK] Sectigo/Comodo esta autorizado en los registros CAA")
        else:
            print("\n  [!] ATENCION: Sectigo NO aparece en los registros CAA")
            print("      Si Sectigo es la CA publica, deberia estar autorizado.")
            print("      Registros CAA recomendados para Sectigo:")
            print('      0 issue "sectigo.com"')
            print('      0 issuewild "sectigo.com"')
    except dns.resolver.NoAnswer:
        print("  No hay registros CAA configurados")
        print("  [INFO] Sin CAA, cualquier CA puede emitir certificados")
    except Exception as e:
        print(f"  [!] Error: {e}")

    # 4. A Records
    print(f"\n{'─'*70}")
    print("  4. REGISTROS A (IPv4)")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'A')
        for rdata in answers:
            print(f"  A: {rdata}")
    except Exception as e:
        print(f"  [!] Error: {e}")

    # 5. TXT Records
    print(f"\n{'─'*70}")
    print("  5. REGISTROS TXT")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            print(f"  TXT: {rdata}")
    except dns.resolver.NoAnswer:
        print("  No hay registros TXT")
    except Exception as e:
        print(f"  [!] Error: {e}")

    # 6. MX Records
    print(f"\n{'─'*70}")
    print("  6. REGISTROS MX (Mail)")
    print(f"{'─'*70}")
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        for rdata in answers:
            print(f"  MX: {rdata}")
    except dns.resolver.NoAnswer:
        print("  No hay registros MX")
    except Exception as e:
        print(f"  [!] Error: {e}")


def check_ssl_certificate(domain: str, port: int = 443):
    """Verifica el certificado SSL/TLS del dominio."""
    print(f"\n{'─'*70}")
    print("  7. CERTIFICADO SSL/TLS")
    print(f"{'─'*70}")
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()

                # Issuer
                issuer = dict(x[0] for x in cert.get('issuer', []))
                subject = dict(x[0] for x in cert.get('subject', []))

                print(f"  Dominio (CN)       : {subject.get('commonName', 'N/A')}")
                print(f"  Emisor (Issuer)    : {issuer.get('commonName', 'N/A')}")
                print(f"  Organizacion (O)   : {issuer.get('organizationName', 'N/A')}")
                print(f"  Valido desde       : {cert.get('notBefore', 'N/A')}")
                print(f"  Valido hasta       : {cert.get('notAfter', 'N/A')}")
                print(f"  Numero de serie    : {cert.get('serialNumber', 'N/A')}")
                print(f"  Version            : {cert.get('version', 'N/A')}")

                # SANs
                san = cert.get('subjectAltName', [])
                if san:
                    print(f"  SANs               :")
                    for type_, value in san:
                        print(f"    - {type_}: {value}")

                # Check if Sectigo
                issuer_org = issuer.get('organizationName', '').lower()
                issuer_cn = issuer.get('commonName', '').lower()
                if 'sectigo' in issuer_org or 'sectigo' in issuer_cn or 'comodo' in issuer_org:
                    print(f"\n  [OK] El certificado fue emitido por Sectigo")
                else:
                    print(f"\n  [INFO] El certificado NO fue emitido por Sectigo")
                    print(f"         CA actual: {issuer.get('organizationName', 'N/A')}")

    except socket.timeout:
        print("  [!] Timeout conectando al servidor")
    except ssl.SSLError as e:
        print(f"  [!] Error SSL: {e}")
    except ConnectionRefusedError:
        print(f"  [!] Conexion rechazada en puerto {port}")
    except Exception as e:
        print(f"  [!] Error: {e}")


def check_with_cli(domain: str):
    """Verificación alternativa usando herramientas CLI del sistema."""
    print(f"\n{'─'*70}")
    print("  8. VERIFICACION CON HERRAMIENTAS CLI")
    print(f"{'─'*70}")

    # dig
    for cmd, label in [
        (["dig", "SOA", domain, "+short"], "dig SOA"),
        (["dig", "CAA", domain, "+short"], "dig CAA"),
        (["dig", "NS", domain, "+short"], "dig NS"),
    ]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                print(f"\n  {label}:")
                for line in result.stdout.strip().split('\n'):
                    print(f"    {line}")
        except FileNotFoundError:
            print(f"\n  [!] {cmd[0]} no disponible")
            break
        except Exception as e:
            print(f"\n  [!] Error ejecutando {label}: {e}")


def print_recommendations(domain: str):
    """Imprime recomendaciones basadas en buenas prácticas."""
    print(f"\n{'='*70}")
    print("  RECOMENDACIONES")
    print(f"{'='*70}")
    print("""
  Si Sectigo es la CA publica para ferrovial.com, asegurate de:

  1. REGISTRO CAA: Configurar registros CAA para autorizar a Sectigo:
     ferrovial.com.  3600  IN  CAA  0 issue "sectigo.com"
     ferrovial.com.  3600  IN  CAA  0 issuewild "sectigo.com"

  2. REGISTRO SOA: Verificar que:
     - El serial se incrementa con cada cambio
     - El primary NS apunta al nameserver correcto
     - Los valores de refresh/retry/expire son razonables:
       * Refresh: 3600-86400 (1h-24h)
       * Retry: 600-3600 (10min-1h)
       * Expire: 604800-2419200 (1sem-4sem)
       * Minimum TTL: 300-86400 (5min-24h)

  3. CERTIFICADO SSL: Verificar que:
     - El certificado esta vigente
     - Fue emitido por Sectigo (si es la CA elegida)
     - Cubre todos los subdominios necesarios (wildcard o SANs)

  4. Si usas Azure DNS, el SOA se gestiona automaticamente pero
     puedes verificarlo con:
     az network dns record-set soa show -g <resource-group> -z ferrovial.com
""")


if __name__ == "__main__":
    domain = "ferrovial.com"

    print(f"\n  Verificando registros DNS y certificado SSL para: {domain}")
    print(f"  Ejecutando desde: {socket.gethostname()}")

    check_dns_with_module(domain)
    check_ssl_certificate(domain)
    check_with_cli(domain)
    print_recommendations(domain)

    print(f"\n{'='*70}")
    print("  VERIFICACION COMPLETADA")
    print(f"{'='*70}\n")
