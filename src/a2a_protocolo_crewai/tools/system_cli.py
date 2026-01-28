"""
Herramienta de System CLI para ejecutar comandos del sistema.
"""

import subprocess
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


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
        """Ejecuta un comando del sistema y retorna el resultado."""
        print(f"\n[SYSTEM CLI] Ejecutando: {command}")

        # Lista de comandos peligrosos que requieren confirmacion
        dangerous_patterns = ['rm ', 'del ', 'format', 'rmdir', 'rd ', 'deltree']

        if any(pattern in command.lower() for pattern in dangerous_patterns):
            return f"BLOQUEADO: Comando potencialmente destructivo detectado: {command}. Use con precaucion."

        try:
            # Detectar si es comando PowerShell o cmd
            # Si empieza con 'powershell ' lo ejecutamos en PowerShell
            if command.lower().startswith('powershell '):
                ps_cmd = command[11:]  # Quitar 'powershell '
                full_cmd = ['powershell.exe', '-NoProfile', '-Command', ps_cmd]
                result = subprocess.run(
                    full_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                # Ejecutar comando en cmd
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='cp850',
                    errors='replace'
                )

            output = result.stdout if result.stdout else ""
            error = result.stderr if result.stderr else ""

            if result.returncode == 0:
                response = f"[OK] Comando ejecutado exitosamente.\n\nSalida:\n{output}"
            else:
                response = f"[ERROR] Codigo de salida: {result.returncode}\n\nSalida:\n{output}\n\nError:\n{error}"

            # Limitar longitud de respuesta
            if len(response) > 3000:
                response = response[:3000] + "\n...[TRUNCADO]"

            print(f"[SYSTEM CLI] Completado (codigo: {result.returncode})")
            return response

        except subprocess.TimeoutExpired:
            return "[TIMEOUT] El comando excedio el tiempo limite de 60 segundos."
        except Exception as e:
            return f"[ERROR] Error ejecutando comando: {str(e)}"
