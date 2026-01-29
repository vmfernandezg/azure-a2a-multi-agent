"""
Herramienta de Azure CLI para ejecutar comandos az.
"""

import os
import subprocess
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .mcp_client import run_mcp_tool_sync


class AzureCommandInput(BaseModel):
    """Esquema de entrada para comandos Azure CLI."""
    command: str = Field(
        ...,
        description="El comando Azure CLI a ejecutar (sin el prefijo 'az'). Ejemplo: 'vm list' o 'group list'"
    )


class AzureCLITool(BaseTool):
    """
    Herramienta para ejecutar comandos de Azure CLI (az).

    Permite gestionar recursos de Azure como VMs, storage,
    networking, resource groups, etc.
    """

    name: str = "azure_cli"
    description: str = """
    Ejecuta comandos de Azure CLI (az) y devuelve la salida exacta.

    Usa esta herramienta para:
    - Listar recursos: az vm list, az group list, az storage account list
    - Ver informacion: az account show, az vm show
    - Gestionar VMs: az vm start, az vm stop, az vm deallocate
    - Gestionar storage: az storage account list, az storage container list
    - Networking: az network vnet list, az network nsg list
    - Subscripciones: az account list, az account set

    IMPORTANTE:
    - Proporciona el comando SIN el prefijo 'az'
    - Ejemplo: usa 'vm list' en lugar de 'az vm list'
    - Los comandos destructivos requieren confirmacion
    - Para listados, usa SIEMPRE --output table para formato legible
    - Esta herramienta devuelve la salida EXACTA del comando, no inventes datos
    """
    args_schema: Type[BaseModel] = AzureCommandInput

    def _run(self, command: str) -> str:
        """Ejecuta el comando a traves del Agente Azure (Puerto 9001)."""
        return run_mcp_tool_sync(9001, "azure_cli", {"command": command})


class AzureLoginInput(BaseModel):
    """Esquema de entrada para login de Azure."""
    use_service_principal: bool = Field(
        default=True,
        description="True para usar Service Principal, False para login interactivo"
    )


class AzureLoginTool(BaseTool):
    """
    Herramienta para autenticarse en Azure.

    Usa las credenciales del Service Principal configuradas
    en las variables de entorno.
    """

    name: str = "azure_login"
    description: str = """
    Autentica en Azure usando Service Principal.

    Usa esta herramienta PRIMERO antes de ejecutar otros comandos Azure.
    Utiliza las credenciales configuradas en el archivo .env:
    - AZURE_CLIENT_ID
    - AZURE_CLIENT_SECRET
    - AZURE_TENANT_ID
    - AZURE_SUBSCRIPTION_ID
    """
    args_schema: Type[BaseModel] = AzureLoginInput

    def _run(self, use_service_principal: bool = True) -> str:
        """Realiza login a traves del Agente Azure (Puerto 8001)."""
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
