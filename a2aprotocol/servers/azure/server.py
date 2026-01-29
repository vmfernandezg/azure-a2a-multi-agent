from fastmcp import FastMCP
import subprocess
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Crear el servidor para el Agente de Azure
mcp = FastMCP("azure-agent")

@mcp.tool()
def azure_cli(command: str) -> str:
    """
    Ejecuta comandos de Azure CLI (az).
    
    Args:
        command: El comando a ejecutar SIN el prefijo 'az'. Ejemplo: 'vm list'
    """
    # Limpieza de comando
    command = command.strip()
    if command.lower().startswith('az '):
        command = command[3:].strip()
    
    full_command = f"az {command}"
    print(f"\n[AZURE SERVER] Ejecutando CLI: {full_command}")
    
    try:
        # Ejecutar con subprocess
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        if result.returncode == 0:
            return output
        else:
            return f"ERROR (Code {result.returncode}): {error}\nOutput: {output}"
            
    except subprocess.TimeoutExpired:
        return "TIMEOUT: El comando excedió los 120 segundos."
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

@mcp.tool()
def azure_powershell(script: str) -> str:
    """
    Ejecuta scripts de Azure PowerShell (Cmdlets Az).
    
    Args:
        script: El script de PowerShell a ejecutar.
    """
    print(f"\n[AZURE SERVER] Ejecutando PowerShell: {script[:50]}...")
    
    # Envolver para capturar errores y asegurar encoding
    wrapped_script = f"""
    $ErrorActionPreference = 'Stop'
    try {{
        {script}
    }} catch {{
        Write-Error $_
        exit 1
    }}
    """
    
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", wrapped_script],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""
        
        if result.returncode == 0:
            return output
        else:
            return f"POWERSHELL ERROR: {error}\nOutput: {output}"
            
    except subprocess.TimeoutExpired:
        return "TIMEOUT: El script excedió los 120 segundos."
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

@mcp.tool()
def login_service_principal(client_id: str, client_secret: str, tenant_id: str, subscription_id: str = None) -> str:
    """
    Realiza login en Azure usando Service Principal.
    Útil para inicializar la sesión del servidor.
    """
    try:
        cmd = f"az login --service-principal -u {client_id} -p {client_secret} --tenant {tenant_id}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return f"LOGIN FAILED: {result.stderr}"
            
        if subscription_id:
            subprocess.run(f"az account set --subscription {subscription_id}", shell=True)
            return f"Login exitoso. Subscripción activa: {subscription_id}"
            
        return "Login exitoso (Subscripción por defecto)."
    except Exception as e:
        return f"LOGIN ERROR: {str(e)}"

if __name__ == "__main__":
    # Ejecuta el servidor en el puerto 9001
    print("🔵 Iniciando Azure Agent Server en puerto 9001...")
    mcp.run(transport="sse", port=9001)
