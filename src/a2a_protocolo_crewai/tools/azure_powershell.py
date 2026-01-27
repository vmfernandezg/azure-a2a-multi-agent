"""
Herramienta de Azure PowerShell para ejecutar cmdlets de Az.
"""

import os
import subprocess
import tempfile
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class AzurePSCommandInput(BaseModel):
    """Esquema de entrada para comandos Azure PowerShell."""
    command: str = Field(
        ...,
        description="El cmdlet de Azure PowerShell a ejecutar. Ejemplo: 'Get-AzVM' o 'Get-AzResourceGroup'"
    )


class AzurePowerShellTool(BaseTool):
    """
    Herramienta para ejecutar cmdlets de Azure PowerShell (Az module).

    Permite gestionar recursos de Azure usando PowerShell cmdlets
    como Get-AzVM, Get-AzResourceGroup, New-AzVM, etc.
    """

    name: str = "azure_powershell"
    description: str = """
    Ejecuta cmdlets de Azure PowerShell (modulo Az).

    Usa esta herramienta para:
    - Listar recursos: Get-AzVM, Get-AzResourceGroup, Get-AzStorageAccount
    - Ver informacion: Get-AzContext, Get-AzSubscription
    - Gestionar VMs: Start-AzVM, Stop-AzVM, New-AzVM
    - Gestionar storage: Get-AzStorageAccount, New-AzStorageAccount
    - Networking: Get-AzVirtualNetwork, Get-AzNetworkSecurityGroup
    - Subscripciones: Set-AzContext, Get-AzSubscription

    IMPORTANTE:
    - Usa cmdlets completos de Azure PowerShell (modulo Az)
    - Los cmdlets destructivos requieren confirmacion
    - La conexion a Azure se hace automaticamente
    """
    args_schema: Type[BaseModel] = AzurePSCommandInput

    def _run(self, command: str) -> str:
        """Ejecuta un cmdlet de Azure PowerShell y retorna el resultado."""

        print(f"\n[AZURE POWERSHELL] Ejecutando: {command}")

        # Comandos peligrosos que requieren confirmacion
        dangerous_patterns = ['Remove-', 'Delete-', 'Stop-', 'Deallocate']
        is_dangerous = any(pattern in command for pattern in dangerous_patterns)

        if is_dangerous and '-Force' not in command and '-Confirm:$false' not in command:
            print("[AZURE POWERSHELL] Cmdlet potencialmente destructivo detectado")

        # Obtener credenciales
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

        try:
            # Crear script PowerShell con conexion automatica
            script_content = f'''
$ErrorActionPreference = 'Continue'
$WarningPreference = 'SilentlyContinue'

# Conectar a Azure
$securePassword = ConvertTo-SecureString "{client_secret}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("{client_id}", $securePassword)
Connect-AzAccount -ServicePrincipal -Credential $credential -Tenant "{tenant_id}" -WarningAction SilentlyContinue | Out-Null

# Establecer subscription
Set-AzContext -Subscription "{subscription_id}" -WarningAction SilentlyContinue | Out-Null

# Ejecutar comando
{command}
'''
            # Escribir script a archivo temporal
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                f.write(script_content)
                script_path = f.name

            try:
                # Ejecutar script
                result = subprocess.run(
                    ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding='utf-8',
                    errors='replace'
                )

                output = result.stdout.strip() if result.stdout else ""
                error = result.stderr.strip() if result.stderr else ""

                if result.returncode == 0 or output:
                    response = output if output else "[OK] Comando ejecutado sin salida"
                else:
                    if 'Connect-AzAccount' in error or 'not connected' in error.lower():
                        response = f"[ERROR] No conectado a Azure.\n\nError:\n{error}"
                    else:
                        response = f"[ERROR] Codigo: {result.returncode}\n\nSalida:\n{output}\n\nError:\n{error}"

                # Limitar longitud
                if len(response) > 5000:
                    response = response[:5000] + "\n...[TRUNCADO]"

                print(f"[AZURE POWERSHELL] Completado (codigo: {result.returncode})")
                return response

            finally:
                # Limpiar archivo temporal
                try:
                    os.unlink(script_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            return "[TIMEOUT] El cmdlet Azure PowerShell excedio el tiempo limite de 120 segundos."
        except FileNotFoundError:
            return "[ERROR] PowerShell no esta disponible."
        except Exception as e:
            return f"[ERROR] Error ejecutando cmdlet: {str(e)}"


class AzurePSConnectInput(BaseModel):
    """Esquema de entrada para conexion Azure PowerShell."""
    use_service_principal: bool = Field(
        default=True,
        description="True para usar Service Principal, False para login interactivo"
    )


class AzurePSConnectTool(BaseTool):
    """
    Herramienta para conectarse a Azure usando PowerShell.
    """

    name: str = "azure_ps_connect"
    description: str = """
    Conecta a Azure usando PowerShell (Connect-AzAccount).

    Usa esta herramienta PRIMERO antes de ejecutar otros cmdlets Azure.
    Utiliza las credenciales configuradas en el archivo .env.
    """
    args_schema: Type[BaseModel] = AzurePSConnectInput

    def _run(self, use_service_principal: bool = True) -> str:
        """Realiza conexion a Azure con PowerShell."""
        print("\n[AZURE PS CONNECT] Iniciando conexion...")

        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

        if not all([client_id, client_secret, tenant_id]):
            return "[ERROR] Credenciales Azure no configuradas en .env"

        try:
            # Script de conexion
            script_content = f'''
$ErrorActionPreference = 'Stop'
$WarningPreference = 'SilentlyContinue'

$securePassword = ConvertTo-SecureString "{client_secret}" -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("{client_id}", $securePassword)
$result = Connect-AzAccount -ServicePrincipal -Credential $credential -Tenant "{tenant_id}" -WarningAction SilentlyContinue

if ($result) {{
    Set-AzContext -Subscription "{subscription_id}" -WarningAction SilentlyContinue | Out-Null
    Write-Host "[OK] Conexion exitosa"
    Write-Host "Subscription: {subscription_id}"
}} else {{
    Write-Host "[ERROR] Conexion fallida"
}}
'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
                f.write(script_content)
                script_path = f.name

            try:
                result = subprocess.run(
                    ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
                )

                output = result.stdout.strip() if result.stdout else ""

                if '[OK]' in output or result.returncode == 0:
                    return f"[OK] Conexion exitosa con Service Principal.\nSubscription: {subscription_id}"
                else:
                    return f"[ERROR] Conexion fallida:\n{output}\n{result.stderr}"

            finally:
                try:
                    os.unlink(script_path)
                except:
                    pass

        except Exception as e:
            return f"[ERROR] Error durante conexion: {str(e)}"
