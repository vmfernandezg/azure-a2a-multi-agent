from fastmcp import FastMCP
import subprocess
import os
from dotenv import load_dotenv

load_dotenv()

# Crear el servidor para el Agente de Sistema
mcp = FastMCP("system-agent")

@mcp.tool()
def system_execute(command: str) -> str:
    """
    Ejecuta comandos del sistema operativo (cmd o powershell).
    
    Args:
        command: El comando a ejecutar. Si empieza con 'powershell ', usa PowerShell.
    """
    print(f"\n[SYSTEM SERVER] Ejecutando: {command}")
    
    # Lista de comandos peligrosos que requieren confirmacion
    dangerous_patterns = ['rm ', 'del ', 'format', 'rmdir', 'rd ', 'deltree']

    if any(pattern in command.lower() for pattern in dangerous_patterns):
        return f"BLOQUEADO: Comando potencialmente destructivo detectado: {command}. Use con precaucion."

    try:
        # Detectar si es comando PowerShell o cmd
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

        output = result.stdout.strip() if result.stdout else ""
        error = result.stderr.strip() if result.stderr else ""

        if result.returncode == 0:
            response = f"[OK] Salida:\n{output}"
        else:
            response = f"[ERROR Code {result.returncode}] Salida:\n{output}\nError:\n{error}"

        # Limitar longitud de respuesta
        if len(response) > 3000:
            response = response[:3000] + "\n...[TRUNCADO]"

        return response

    except subprocess.TimeoutExpired:
        return "[TIMEOUT] El comando excedio el tiempo limite de 60 segundos."
    except Exception as e:
        return f"[ERROR] Error ejecutando comando: {str(e)}"

if __name__ == "__main__":
    # Ejecuta el servidor en el puerto 9002
    print("🟢 Iniciando System Agent Server en puerto 9002...")
    mcp.run(transport="sse", port=9002)
