# Análisis Completo del Proyecto: Orquestador Azure A2A con MCP

## 📋 ¿QUÉ HACE EL PROYECTO?

El proyecto es un **Orquestador Azure A2A (Agent-to-Agent)** multi-agente que permite a los usuarios interactuar con Azure usando **lenguaje natural** en español.

La principal innovación de esta versión es la integración del **Model Context Protocol (MCP)**, separando la lógica de búsqueda en un servidor independiente que se comunica vía HTTP (SSE).

### Propósito Principal

- **Interactuar con Azure sin conocer comandos técnicos**
- **Arquitectura Cliente-Servidor MCP**: Integración escalable y modular.
- **Servidor MCP Local**: Gestiona herramientas externas (como búsqueda web) en un proceso separado.
- **Interpretar solicitudes en español** y traducirlas a comandos
- **Buscar en documentación oficial** cuando se desconoce un comando
- **Coordinar múltiples agentes especializados** para tareas complejas

---

## 🏗️ ARQUITECTURA DEL SISTEMA (MCP ENABLED)

```
┌─────────────────────────────────────────────────────────────┐
│                  USUARIO (Español)                       │
│              "listar vms", "que hora es"                │
23: └────────────────────┬──────────────────────────────────────┘
24:                      │
25:                      v
26: ┌─────────────────────────────────────────────────────────────┐
27: │       AGENT CLIENT (Python 3.10)                           │
28: │          Manager + Azure Specialist + System Specialist    │
29: │          (Puerto Principal)                                │
30: └──────┬─────────────┬─────────────────────┬──────────────┘
31:        │             │                     │ HTTP / SSE
32:        v             v                     v
33: ┌────────────┐  ┌────────────┐   ┌───────────────────────────┐
34: │Azure CLI   │  │PowerShell  │   │  MCP SERVER (FastMCP)     │
35: │(Subproceso)│  │(Subproceso)│   │  "azure-docs-search"      │
36: └────────────┘  └────────────┘   │  Puerto: 8000             │
37:                                  └─────────────┬─────────────┘
                                                   │
                                                   v
                                          DuckDuckGo Search 
                                       (learn.microsoft.com)
```

### Componentes Clave

1. **Agente Cliente (`src/`)**: Ejecuta la lógica de negocio, orquestación y herramientas locales (CLI/PowerShell).
2. **Servidor MCP (`mcp_server.py`)**: Un proceso independiente que expone herramientas vía protocolo MCP (HTTP/SSE). Actualmente aloja la herramienta de búsqueda de documentación.

---

## 🚀 CÓMO EJECUTAR EL PROYECTO

Debido a la arquitectura Cliente-Servidor, necesitas ejecutar dos procesos en terminales separadas.

### Prerrequisitos

- **Python 3.10** (Requerido para compatibilidad con `crewai` y `fastmcp`).
- Credenciales de Azure configuradas en `.env`.
- **Streamlit**: Instalado en el entorno (`pip install streamlit`).

## 🖥️ OPCIÓN A: Interfaz Web (Streamlit) - ¡NUEVO

Una interfaz visual moderna con historial de chat y **selector de subscripción Azure** incorporado.

**Terminal 2 (Agente):**

```powershell
cd mcpddgs
.\venv\Scripts\activate
streamlit run streamlit_app.py
```

## ⌨️ OPCIÓN B: Interfaz de Consola (CLI)

La interfaz clásica rápida.

**Terminal 2 (Agente):**

```powershell
cd mcpddgs
.\venv\Scripts\activate
# Ejecuta el cliente (ya no requiere definir PYTHONPATH gracias a la configuración del proyecto)
python -m a2a_protocolo_crewai.main
```

### PASO 1 (Común): Iniciar el Servidor MCP (Terminal 1)

Este servidor expone las herramientas de búsqueda.

```powershell
cd mcpddgs
.\venv\Scripts\activate
# Inicia el servidor MCP (configurado en el código en el puerto 8000)
python mcp_server.py
```

*Debe mantenerse corriendo en segundo plano.*

---

## 📁 COMPONENTES DEL PROYECTO

### 1. **Servidor MCP** (`mcp_server.py`)

Implementado con **FastMCP**, expone la herramienta `search_docs` vía HTTP (SSE).

- **Transporte**: SSE (Server-Sent Events) sobre HTTP.
- **Herramienta**: Búsqueda filtrada en `learn.microsoft.com` usando DuckDuckGo.

### 2. **Punto de Entrada Cliente** (`main.py`)

Coordina el flujo de conversación y maneja el estado de la sesión.

### 3. **Herramienta Cliente MCP** (`src/.../tools/docs_search.py`)

Una herramienta personalizada de CrewAI que actúa como **Cliente MCP**.

- Se conecta a `http://localhost:8000/sse`.
- Solicita la ejecución de la herramienta `search_docs` al servidor remoto.

### 4. **Configuración YAML**

- `config/agents.yaml`: Definición de los 3 agentes
- `config/tasks.yaml`: Definición de las tareas

### 5. **Configuración** (`.env`)

Credenciales de Azure OpenAI (API Key o Managed Identity) y Service Principal de Azure

---

## 🤖 LOS 3 AGENTES ESPECIALIZADOS

### Agente 1: Azure Specialist

**Rol**: Especialista en Infraestructura Azure
**Objetivo**: Gestionar e interactuar eficientemente con los recursos de Azure usando CLI y PowerShell.
**Herramientas**: `AzureCLITool`, `AzurePowerShellTool`

### Agente 2: System Specialist

**Rol**: Especialista de Operaciones de Sistema
**Objetivo**: Gestionar operaciones del sistema de archivos local y verificaciones del sistema.
**Herramientas**: `SystemCLITool`

### Agente 3: Docs Researcher

**Rol**: Investigador de Documentación Azure
**Objetivo**: Encontrar documentación técnica precisa.
**Innovación**: **Ya no busca directamente**. Delega la búsqueda al **Servidor MCP**.
**Herramientas**: `AuthDocsSearchTool` (Cliente MCP)

---

## 🔐 MÉTODOS DE AUTENTICACIÓN

### Método 1: API Key (Modo Clásico)

Configure `AZURE_OPENAI_API_KEY` en el archivo `.env`.

### Método 2: Managed Identity (UMI)

Soporte nativo para User Assigned Managed Identity si se ejecuta en VMs de Azure.

---

## 🛠️ FUNCIONAMIENTO DETALLADO DE LAS HERRAMIENTAS

### Herramienta 1: SystemCLI

Ejecuta comandos locales (PowerShell/cmd) con protecciones de seguridad.

### Herramienta 2: AzureCLI

Ejecuta comandos `az` de forma segura.

### Herramienta 3: AzurePowerShell

Ejecuta cmdlets `Az` utilizando el contexto de autenticación del Service Principal.

### Herramienta 4: Busqueda en Documentación (MCP)

**Qué hace:** Actúa como puente. Envía la consulta al servidor MCP en el puerto 8000.
**Flujo:**

1. Agente pide buscar "comando crear vm".
2. `AuthDocsSearchTool` conecta a `http://localhost:8000/sse`.
3. Envía mensaje JSON-RPC solicitando `call_tool("search_docs", ...)`.
4. `mcp_server.py` recibe, ejecuta DuckDuckGo y devuelve texto.
5. Herramienta recibe respuesta y se la entrega al agente.

---

## 🤝 COORDINACIÓN

El **Manager** (GPT-4) decide a quién delegar.

- Si no sabe un comando -> Delega a **Docs Researcher**.
- Docs Researcher consulta al **MCP Server**.
- Con la info, Manager delega a **Azure Specialist** para ejecutar.
