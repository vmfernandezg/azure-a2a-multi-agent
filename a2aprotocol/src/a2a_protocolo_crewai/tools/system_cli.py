"""
Herramienta de System CLI para ejecutar comandos del sistema.
"""

import subprocess
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .mcp_client import run_mcp_tool_sync


class SystemCommandInput(BaseModel):
    """Esquema de entrada para comandos del sistema."""
    command: str = Field(
        ...,
        description="El comando del sistema a ejecutar (cmd, bash, etc.)"
    )


class SystemCLITool(BaseTool):
    """
    Herramienta para ejecutar comandos del sistema operativo.

    Permite ejecutar comandos de Windows (cmd) o comandos generales
    del sistema para tareas como listar archivos, verificar conectividad, etc.
    """

    name: str = "system_cli"
    description: str = """
    Ejecuta comandos del sistema operativo.

    Usa esta herramienta para:
    - Verificar conectividad de red (ping, nslookup)
    - Listar archivos y directorios (dir, ls)
    - Verificar variables de entorno
    - Ejecutar scripts locales
    - Operaciones generales del sistema

    IMPORTANTE: No ejecutar comandos destructivos sin confirmacion.
    Los comandos se ejecutan en Windows (cmd).
    """
    args_schema: Type[BaseModel] = SystemCommandInput

    def _run(self, command: str) -> str:
        """Ejecuta el comando a traves del Agente Sistema (Puerto 9002)."""
        return run_mcp_tool_sync(9002, "system_execute", {"command": command})
