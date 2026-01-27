"""
Herramienta de Azure CLI para ejecutar comandos az.
"""

import os
import subprocess
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


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
        """Ejecuta un comando de Azure CLI y retorna el resultado."""

        # Limpiar el comando
        command = command.strip()
        
        # Asegurar que el comando no empiece con 'az '
        if command.lower().startswith('az '):
            command = command[3:].strip()

        # Asegurar que no haya errores tipográficos comunes
        command = command.replace('agr ', 'az ')

        full_command = f"az {command}"
        print(f"\n[AZURE CLI] Ejecutando: {full_command}")

        # Comandos peligrosos que requieren confirmacion
        dangerous_patterns = ['delete', 'remove', 'purge', 'deallocate', 'stop']
        is_dangerous = any(pattern in command.lower() for pattern in dangerous_patterns)

        if is_dangerous and '--yes' not in command and '-y' not in command:
            print("[AZURE CLI] Comando potencialmente destructivo detectado")

        try:
            # Ejecutar comando Azure CLI
            result = subprocess.run(
                full_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                encoding='utf-8',
                errors='replace'
            )

            output = result.stdout if result.stdout else ""
            error = result.stderr if result.stderr else ""
 
            if result.returncode == 0:
                response = output.strip()
            else:
                # Verificar si es error de login
                if 'az login' in error.lower() or 'not logged in' in error.lower():
                    response = f"[ERROR] No autenticado en Azure. Ejecuta primero el login.\n\nError:\n{error}"
                else:
                    response = f"[ERROR] Codigo de salida: {result.returncode}\n\nSalida:\n{output}\n\nError:\n{error}"
 
            # Limitar longitud de respuesta
            if len(response) > 10000:
                response = response[:10000] + "\n...[TRUNCADO]"
 
            print(f"[AZURE CLI] Completado (codigo: {result.returncode})")
            return response

        except subprocess.TimeoutExpired:
            return "[TIMEOUT] El comando Azure CLI excedio el tiempo limite de 120 segundos."
        except FileNotFoundError:
            return "[ERROR] Azure CLI no esta instalado o no esta en el PATH. Instala Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli"
        except Exception as e:
            return f"[ERROR] Error ejecutando comando Azure CLI: {str(e)}"


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
        """Realiza login en Azure."""
        print("\n[AZURE LOGIN] Iniciando autenticacion...")

        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')

        if not all([client_id, client_secret]):
            return "[ERROR] Credenciales Azure no configuradas en .env (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)"

        if not tenant_id:
            # Intentar obtener tenant_id
            return "[ERROR] AZURE_TENANT_ID no configurado en .env. Es necesario para el login con Service Principal."

        try:
            # Login con Service Principal
            login_cmd = f'az login --service-principal -u {client_id} -p {client_secret} --tenant {tenant_id}'

            result = subprocess.run(
                login_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                # Establecer subscription si esta configurada
                if subscription_id:
                    sub_cmd = f'az account set --subscription {subscription_id}'
                    subprocess.run(sub_cmd, shell=True, capture_output=True)

                return f"[OK] Login exitoso con Service Principal.\nSubscription activa: {subscription_id or 'default'}"
            else:
                return f"[ERROR] Login fallido:\n{result.stderr}"

        except Exception as e:
            return f"[ERROR] Error durante login: {str(e)}"
