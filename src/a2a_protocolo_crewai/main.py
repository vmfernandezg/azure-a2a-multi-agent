"""
Orquestador Azure A2A - Sistema Multi-Agente con CrewAI + Azure OpenAI.

Flujo:
1. Login en Azure CLI
2. Seleccionar subscripcion
3. Loop interactivo:
   - Usuario escribe en lenguaje natural
   - Azure OpenAI traduce a comandos
   - Agente ejecuta con las herramientas apropiadas
   - Muestra resultado
   - Repite hasta "exit" o "salir"
"""

import os
import sys
import subprocess
import json
from dotenv import load_dotenv

from .crew import AzureOrchestratorCrew


def print_header(text: str, char: str = "="):
    """Imprime un encabezado formateado."""
    print(f"\n{char * 60}")
    print(text)
    print(f"{char * 60}")


def check_environment() -> bool:
    """Verifica que el entorno este correctamente configurado."""
    load_dotenv()

    errors = []

    # Verificar Azure OpenAI
    # Verificar Azure OpenAI
    # Se requiere API KEY, Managed Identity (UMI) o Service Principal (SPN)
    if not os.getenv("AZURE_OPENAI_API_KEY") and not os.getenv("AZURE_AQUIDENTIY_CLIENT_ID") and not os.getenv("AZURE_CLIENT_ID"):
        errors.append("Falta autenticacion: Configura API_KEY, UMI_CLIENT_ID o SPN (AZURE_CLIENT_ID)")

    if not os.getenv("AZURE_OPENAI_ENDPOINT"):
        errors.append("AZURE_OPENAI_ENDPOINT no configurada")

    if not os.getenv("AZURE_OPENAI_DEPLOYMENT"):
        errors.append("AZURE_OPENAI_DEPLOYMENT no configurada")

    # Verificar Azure Service Principal
    if not os.getenv("AZURE_CLIENT_ID"):
        errors.append("AZURE_CLIENT_ID no configurada")

    if not os.getenv("AZURE_CLIENT_SECRET"):
        errors.append("AZURE_CLIENT_SECRET no configurada")

    if not os.getenv("AZURE_TENANT_ID"):
        errors.append("AZURE_TENANT_ID no configurada")

    if errors:
        print_header("ERRORES DE CONFIGURACION", "!")
        for error in errors:
            print(f"  [X] {error}")
        print("\nConfigura las variables en el archivo .env")
        return False

    print("[OK] Configuracion verificada")
    return True


def azure_cli_login() -> bool:
    """Realiza login con Azure CLI usando Service Principal."""
    print_header("LOGIN AZURE CLI")

    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")

    try:
        login_cmd = f'az login --service-principal -u "{client_id}" -p "{client_secret}" --tenant "{tenant_id}" --output none'

        result = subprocess.run(
            login_cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("[OK] Login Azure CLI exitoso")
            return True
        else:
            print(f"[ERROR] Login fallido: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Error durante login: {str(e)}")
        return False


def list_and_select_subscription() -> bool:
    """Lista y permite seleccionar una subscripcion."""
    print_header("SUBSCRIPCIONES DISPONIBLES")

    try:
        result = subprocess.run(
            "az account list --output json",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0 or not result.stdout.strip():
            print("[ERROR] No se pudieron obtener las subscripciones")
            return False

        subscriptions = json.loads(result.stdout)

        if not subscriptions:
            print("[ERROR] No hay subscripciones disponibles")
            return False

        print(f"\nSe encontraron {len(subscriptions)} subscripcion(es):\n")

        for i, sub in enumerate(subscriptions, 1):
            estado = "[ACTIVA]" if sub.get("isDefault") else ""
            print(f"  [{i}] {sub.get('name', 'N/A')} {estado}")
            print(f"      ID: {sub.get('id', 'N/A')}")

        print("\n" + "-" * 60)
        selected = input("\nSelecciona subscripcion (numero) o Enter para usar la activa: ").strip()

        if selected:
            try:
                idx = int(selected) - 1
                if 0 <= idx < len(subscriptions):
                    sub_id = subscriptions[idx]["id"]
                    subprocess.run(
                        f'az account set --subscription "{sub_id}"',
                        shell=True,
                        capture_output=True
                    )
                    # ACTUALIZACION: Guardar la subscripcion seleccionada en el entorno
                    # para que la herramienta de PowerShell la use correctamente.
                    os.environ["AZURE_SUBSCRIPTION_ID"] = sub_id
                    print(f"\n[OK] Subscripcion activa: {subscriptions[idx]['name']}")
            except (ValueError, IndexError):
                print("[!] Seleccion invalida, usando subscripcion por defecto")

        return True

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        return False


def run_interactive_loop():
    """Ejecuta el loop interactivo principal."""
    print_header("ORQUESTADOR AZURE A2A - LISTO")
    print("""
Escribe tu solicitud en lenguaje natural.

EJEMPLOS:
  Sistema: "que hora es", "lista los ficheros"
  Azure:   "listar vms", "que grupos de recursos hay", "listar aks"

Escribe 'exit' o 'salir' para terminar.
""")

    # Historial de conversacion manual (ya que no usamos embeddings)
    chat_history = []
    
    while True:
        print("-" * 60)
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n[!] Saliendo...")
            break

        # Verificar salida
        if user_input.lower() in ['exit', 'salir', 'quit', 'q']:
            print("\n[+] Hasta luego!")
            break

        # Ignorar entradas vacias
        if not user_input:
            continue

        # Ejecutar solicitud
        print(f"\n[*] Procesando: {user_input}")
        print("-" * 60)

        try:
            # Preparar contexto con historial
            context_prompt = ""
            if chat_history:
                context_prompt = "\n\nHISTORIAL DE CONVERSACION RECIENTE:\n"
                for i, (q, a) in enumerate(chat_history[-10:], 1):  # Ultimos 10 mensajes
                    context_prompt += f"Usuario: {q}\nAgente: {a}\n---\n"
                
            full_request = f"{user_input}{context_prompt}"

            # IMPORTANTE: Re-instanciar el crew para evitar errores de estado en modo jerarquico
            crew_instance = AzureOrchestratorCrew()
            result = crew_instance.crew().kickoff(
                inputs={"user_request": full_request}
            )

            print("\n" + "=" * 60)
            print("RESULTADO:")
            print("=" * 60)

            result_str = str(result)
            if result_str:
                 # Guardar en historial
                 chat_history.append((user_input, result_str))
                 print(result_str)
            else:
                 print("[!] Comando ejecutado sin salida")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")


def main():
    """Funcion principal."""
    print_header("ORQUESTADOR AZURE A2A")
    print("Version: 6.0.0")
    print("Sistema: CrewAI + Azure OpenAI (GPT-4)")
    print("Herramientas: Sistema, Azure CLI, PowerShell")

    # 1. Verificar entorno
    if not check_environment():
        sys.exit(1)

    # 2. Login Azure
    if not azure_cli_login():
        sys.exit(1)

    # 3. Seleccionar subscripcion
    if not list_and_select_subscription():
        sys.exit(1)

    # 4. Inicializar y ejecutar
    print_header("INICIALIZANDO")

    try:
        # Verificar que se puede crear una instancia
        test_crew = AzureOrchestratorCrew()
        print("[OK] Azure OpenAI configurado correctamente")
        del test_crew
    except Exception as e:
        print(f"[ERROR] Error inicializando: {str(e)}")
        sys.exit(1)

    # 5. Loop interactivo
    run_interactive_loop()


if __name__ == "__main__":
    main()
