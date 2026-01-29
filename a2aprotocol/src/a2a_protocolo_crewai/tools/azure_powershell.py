"""
Herramienta de Azure PowerShell para ejecutar cmdlets de Az.
"""

import os
import subprocess
from .mcp_client import run_mcp_tool_sync
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .mcp_client import run_mcp_tool_sync


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
        """Ejecuta el cmdlet a traves del Agente Azure (Puerto 9001)."""
        return run_mcp_tool_sync(9001, "azure_powershell", {"script": command})


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
        """Realiza conexion via Agente Azure (Puerto 8001)."""
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

        return run_mcp_tool_sync(9001, "login_service_principal", {
            "client_id": client_id,
            "client_secret": client_secret,
            "tenant_id": tenant_id,
            "subscription_id": subscription_id
        })
