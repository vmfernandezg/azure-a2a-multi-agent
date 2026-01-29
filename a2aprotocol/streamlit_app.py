"""
Streamlit Interface for Azure Orchestrator A2A
Este script crea una interfaz web interactiva para el sistema multi-agente.
NO MODIFICA la lógica existente, solo importa el Crew y lo ejecuta.

Ejecución:
streamlit run streamlit_app.py
"""

import os
import sys

# --- FIX TELEMETRY BEFORE ANY IMPORTS ---
# Desactivar telemetria de CrewAI para evitar error de hilos en Streamlit
# ValueError: signal only works in main thread
# Se deben configurar ANTES de importar crewai
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true" # Por si acaso usa esta otra variable
# ----------------------------------------

import streamlit as st
import subprocess
import json

# Asegurar que el path incluye 'src' para encontrar los módulos
current_dir = os.getcwd()
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importar la lógica del Crew existente
try:
    from a2a_protocolo_crewai.crew import AzureOrchestratorCrew
except ImportError:
    st.error("Error importando AzureOrchestratorCrew. Asegúrate de ejecutar esto desde la raíz del proyecto (mcpddgs).")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="Azure A2A Orchestrator",
    page_icon="🤖",
    layout="wide"
)

# --- FUNCIONES AUXILIARES ---
def get_azure_subscriptions():
    """Obtiene la lista de subscripciones de Azure CLI"""
    try:
        # Usamos --output json para parsear fácil
        result = subprocess.run(
            "az account list --output json",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10 # Timeout rápido para no bloquear la UI mucho tiempo
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except Exception as e:
        st.sidebar.error(f"Error listando subscripciones: {str(e)}")
        return []

def set_subscription(sub_id, sub_name):
    """Cambia la subscripción activa"""
    try:
        subprocess.run(f'az account set --subscription "{sub_id}"', shell=True, check=True)
        os.environ["AZURE_SUBSCRIPTION_ID"] = sub_id
        return True
    except Exception:
        return False

# --- UI PRINCIPAL ---

# Título y Descripción
st.title("🤖 Azure A2A Orchestrator")
st.markdown("""
Interactúa con tus recursos de Azure usando lenguaje natural.
Este asistente utiliza **CrewAI** y un servidor **MCP** local para buscar documentación.
""")

# Sidebar con Configuración
with st.sidebar:
    st.header("Configuración")
    
    # 1. Selector de Subscripción
    st.subheader("Subscripción Azure")
    
    # Cargar subscripciones (cachear esto sería ideal, pero por ahora directo)
    if "subscriptions" not in st.session_state:
        with st.spinner("Cargando subscripciones..."):
            st.session_state.subscriptions = get_azure_subscriptions()

    subs = st.session_state.subscriptions
    
    if subs:
        # Crear lista de nombres para el selectbox
        # Buscamos la default actual
        default_index = 0
        formatted_names = []
        for i, s in enumerate(subs):
            name = s['name']
            is_default = s.get('isDefault', False)
            formatted_names.append(f"{name} ({s['id']})")
            if is_default:
                default_index = i
        
        selected_option = st.selectbox(
            "Selecciona la cuenta activa:",
            options=formatted_names,
            index=default_index
        )
        
        # Al cambiar, actualizar entorno
        if selected_option:
            # Extraer ID del string seleccionado
            # Formato: "Nombre (ID)"
            selected_id = selected_option.split("(")[-1].replace(")", "")
            
            # Solo actualizar si cambió
            current_env_sub = os.getenv("AZURE_SUBSCRIPTION_ID")
            # O si es la primera vez (puede que env sea None)
            
            # Buscamos el nombre limpio
            selected_sub_obj = next((s for s in subs if s['id'] == selected_id), None)
            
            if selected_id != current_env_sub:
                if set_subscription(selected_id, selected_sub_obj['name']):
                    st.success(f"Activa: {selected_sub_obj['name']}")
                else:
                    st.error("Error cambiando subscripción")
            else:
                 # Asegurar que la variable de entorno está setea aunque no haya cambiado en UI (inicio app)
                 os.environ["AZURE_SUBSCRIPTION_ID"] = selected_id

    else:
        st.warning("No se encontraron subscripciones. ¿Estás logueado en 'az login'?")
        if st.button("Reintentar Carga"):
            del st.session_state.subscriptions
            st.rerun()

    st.divider()
    st.info(f"Python: {sys.version.split()[0]}")
    st.info("MCP Servers: Ports 9000-9002")
    
    if st.button("Borrar Historial"):
        st.session_state.messages = []
        st.rerun()

# Verificar entorno (copiado de main.py pero simplificado)
required_vars = ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT"]
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    st.error(f"Faltan variables de entorno: {', '.join(missing_vars)}. Revisa tu archivo .env")
    st.stop()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar Crew (lazy loading)
if "crew_instance" not in st.session_state:
    try:
        # Probamos instanciar para ver si hay credenciales
        test_crew = AzureOrchestratorCrew()
        st.session_state.crew_ready = True
    except Exception as e:
        st.error(f"Error inicializando Agentes: {str(e)}")
        st.session_state.crew_ready = False

# Mostrar mensajes del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input de usuario
if prompt := st.chat_input("Escribe tu solicitud (ej: 'listar vms', 'novedades azure functions')..."):
    if not st.session_state.get("crew_ready", False):
        st.error("El sistema no está listo. Revisa los errores superiores.")
    else:
        # Guardar y mostrar mensaje de usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Ejecutar Agente
        with st.chat_message("assistant"):
            with st.spinner("Los agentes están trabajando... (Consultando Azure / MCP / Docs)"):
                try:
                    # Preparar contexto (historial reciente para el prompt)
                    context_prompt = ""
                    history = st.session_state.messages[-10:-1] # Últimos 10 sin contar el actual
                    if history:
                        context_prompt = "\n\nHISTORIAL DE CONVERSACION RECIENTE:\n"
                        for msg in history:
                            role = "Usuario" if msg["role"] == "user" else "Agente"
                            context_prompt += f"{role}: {msg['content']}\n"
                    
                    full_request = f"{prompt}{context_prompt}"
                    
                    # Instanciar y ejecutar (Fresh instance per run is safer for CrewAI state)
                    crew = AzureOrchestratorCrew()
                    result = crew.crew().kickoff(inputs={"user_request": full_request})
                    
                    response_text = str(result)
                    st.markdown(response_text)
                    
                    # Guardar respuesta
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    
                except Exception as e:
                    error_msg = f"Ocurrió un error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
