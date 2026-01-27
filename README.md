# Análisis Completo del Proyecto: Orquestador Azure A2A

## 📋 ¿QUÉ HACE EL PROYECTO?

El proyecto es un **Orquestador Azure A2A (Agent-to-Agent)** multi-agente que permite a los usuarios interactuar con Azure usando **lenguaje natural** en español. El sistema traduce las preguntas del usuario en comandos técnicos y los ejecuta automáticamente usando **3 agentes especializados** que trabajan juntos de forma jerárquica.

### Propósito Principal:
- **Interactuar con Azure sin conocer comandos técnicos**
- **Ejecutar comandos del sistema operativo** local
- **Gestionar recursos de Azure** usando diferentes herramientas
- **Interpretar solicitudes en español** y traducirlas a comandos
- **Buscar en documentación oficial** cuando se desconoce un comando
- **Coordinar múltiples agentes especializados** para tareas complejas

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                  USUARIO (Español)                       │
│              "listar vms", "que hora es"                │
└────────────────────┬──────────────────────────────────────┘
                     │
                     v
┌─────────────────────────────────────────────────────────────┐
│       Azure OpenAI (GPT-4.1-mini) - MANAGER              │
│          Interpreta el lenguaje natural                    │
│          Coordina a los 3 agentes especializados           │
│             (API Key o Managed Identity)                  │
└──────┬─────────────┬──────────────┬────────────────────┘
       │             │              │
       v             v              v
┌─────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│Azure Specialist │ │System Specialist │ │Docs Researcher   │
│(Azure CLI/PS)   │ │(Comandos locales)│ │(Documentación)   │
└───────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
        │                   │                     │
        v                   v                     v
   Azure CLI           System CLI         Búsqueda en Docs
   Azure PowerShell    (PowerShell)     (learn.microsoft.com)
```

### Proceso Jerárquico
- **Manager (GPT-4.1-mini)**: Analiza la solicitud y delega al agente apropiado
- **Azure Specialist**: Ejecuta comandos Azure CLI y PowerShell
- **System Specialist**: Ejecuta comandos del sistema local
- **Docs Researcher**: Busca en documentación oficial de Microsoft

---

## 📁 COMPONENTES DEL PROYECTO

### 1. **Punto de Entrada** (`main.py`)
Es el archivo que ejecutas y coordina todo el flujo.

### 2. **Crew** (`crew.py`)
Define los 3 agentes especializados y las tareas que van a ejecutar.
- Soporta autenticación con **API Key** o **Managed Identity**
- Usa **Azure Identity** para obtener tokens de forma segura
- **Proceso jerárquico** con un manager que coordina a los agentes

### 3. **Configuración YAML**
- `config/agents.yaml`: Definición de los 3 agentes
- `config/tasks.yaml`: Definición de las tareas

### 4. **Herramientas** (`tools/`)
- `system_cli.py`: Ejecuta comandos del sistema (PowerShell/cmd)
- `azure_cli.py`: Ejecuta comandos `az` de Azure CLI
- `azure_powershell.py`: Ejecuta cmdlets de PowerShell Az
- `docs_search.py`: Busca en documentación oficial de Microsoft (learn.microsoft.com)

### 5. **Configuración** (`.env`)
Credenciales de Azure OpenAI (API Key o Managed Identity) y Service Principal de Azure

---

## 🤖 LOS 3 AGENTES ESPECIALIZADOS

### Agente 1: Azure Specialist
**Rol**: Especialista en Infraestructura Azure

**Objetivo**: Gestionar e interactuar eficientemente con los recursos de Azure usando CLI y PowerShell.

**Backstory**:
```
Eres un Ingeniero de Nube experto especializado en Microsoft Azure.
Conoces todos los comandos de AZ CLI y los módulos de Azure PowerShell.
Tu trabajo es ejecutar comandos técnicos para gestionar recursos,
asegurando siempre que estás autenticado (el sistema maneja la identidad).
Prefieres usar 'az' CLI para la mayoría de las tareas, pero cambias a PowerShell si es necesario.
IMPORTANTE: Si un comando falla, analiza el error y sugiere correcciones o busca en la documentación.
```

**Herramientas**:
- `AzureCLITool`: Comandos Azure CLI
- `AzurePowerShellTool`: Cmdlets Azure PowerShell

### Agente 2: System Specialist
**Rol**: Especialista de Operaciones de Sistema

**Objetivo**: Gestionar operaciones del sistema de archivos local y verificaciones del sistema.

**Backstory**:
```
Eres un Administrador de Sistemas responsable del entorno local donde se ejecuta el agente.
Puedes listar archivos, leer contenido, verificar variables de entorno y el estado del sistema.
Te aseguras de que el entorno esté listo antes de ejecutar operaciones complejas de Azure.
```

**Herramientas**:
- `SystemCLITool`: Comandos del sistema (PowerShell/cmd)

### Agente 3: Docs Researcher
**Rol**: Investigador de Documentación Azure

**Objetivo**: Encontrar documentación técnica precisa y ejemplos para servicios de Azure.

**Backstory**:
```
Eres un Redactor Técnico e Investigador.
Cuando el equipo no conoce un comando o parámetro específico, tú lo buscas.
Usas las herramientas de búsqueda para encontrar documentación oficial de Microsoft Learn.
Evitas adivinar comandos; verificas la sintaxis con búsquedas primero si tienes dudas.
```

**Herramientas**:
- `AuthDocsSearchTool`: Búsqueda en learn.microsoft.com

---

## 🔐 MÉTODOS DE AUTENTICACIÓN

### Método 1: API Key (Modo Clásico)
```env
AZURE_OPENAI_API_KEY=tu-api-key
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**Implementación:**
```python
if api_key:
    return LLM(
        model=f"azure/{deployment}",
        api_key=api_key,
        base_url=f"{endpoint}/openai/deployments/{deployment}",
        api_version=api_version,
        temperature=0.1,
    )
```

### Método 2: Managed Identity (UMI)
```env
# Opcional: Client ID específico de la UMI
AZURE_AQUIDENTIY_CLIENT_ID=7bef6d90-a33a-4453-930c-0ce8abd23d5f

AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

**Implementación:**
```python
# Verificar si hay un Client ID específico para la UMI de OpenAI
umi_client_id = os.getenv("AZURE_AQUIDENTIY_CLIENT_ID")

credential = DefaultAzureCredential(
    managed_identity_client_id=umi_client_id,
    exclude_environment_credential=True
) if umi_client_id else DefaultAzureCredential()

# Provider de token para Azure OpenAI (scope default)
token_provider = get_bearer_token_provider(
    credential,
    "https://cognitiveservices.azure.com/.default"
)

return LLM(
    model=f"azure/{deployment}",
    base_url=f"{endpoint}/openai/deployments/{deployment}",
    api_version=api_version,
    temperature=0.1,
    azure_ad_token_provider=token_provider
)
```

---

## 🔄 CÓMO FUNCIONA - PASO A PASO

### PASO 1: Inicio del Sistema
```python
main() → check_environment()
```
- Verifica que las credenciales de Azure OpenAI estén configuradas (API Key o Managed Identity)
- Verifica credenciales del Service Principal de Azure
- Si falta algo, muestra error y termina

---

### PASO 2: Login en Azure CLI
```python
azure_cli_login()
```
Ejecuta el comando:
```bash
az login --service-principal
  -u "AZURE_CLIENT_ID"
  -p "AZURE_CLIENT_SECRET"
  --tenant "AZURE_TENANT_ID"
```
- Autentica automáticamente usando el Service Principal
- No requiere intervención del usuario

---

### PASO 3: Seleccionar Suscripción
```python
list_and_select_subscription()
```
1. Ejecuta: `az account list --output json`
2. Muestra las suscripciones disponibles
3. El usuario selecciona una (o usa la activa por defecto)
4. Establece la suscripción: `az account set --subscription "ID"`
5. Guarda la suscripción en `AZURE_SUBSCRIPTION_ID` para que PowerShell la use

---

### PASO 4: Inicializar CrewAI
```python
AzureOrchestratorCrew()
```
```python
def create_azure_openai_llm():
    # Si hay API Key configurada, usarla (modo clásico)
    if api_key:
        return LLM(model=f"azure/{deployment}", api_key=api_key, ...)

    # Si no, intentar usar Managed Identity
    credential = DefaultAzureCredential(...)
    token_provider = get_bearer_token_provider(credential, ...)
    return LLM(model=f"azure/{deployment}", azure_ad_token_provider=token_provider, ...)
```
- Crea instancia de LLM usando Azure OpenAI
- Inicializa los **3 agentes especializados**
- Configura el **proceso jerárquico** con un manager

---

### PASO 5: Loop Interactivo Principal

#### 5.1 Usuario escribe solicitud
```
> listar vms
```

#### 5.2 Manager analiza la solicitud
```python
crew.kickoff(inputs={"user_request": "listar vms"})
```

**El Manager (GPT-4.1-mini) analiza:**
1. ¿Qué tipo de solicitud es? → Operación de Azure
2. ¿Qué agente puede manejarla? → Azure Specialist
3. ¿Necesita documentación? → NO, el comando es conocido
4. Delega a Azure Specialist

#### 5.3 Azure Specialist ejecuta
```python
azure_cli._run(command="vm list --output table")
```

#### 5.4 Ejecuta el comando
```python
full_command = "az vm list --output table"
subprocess.run(
    full_command,
    shell=True,
    capture_output=True,
    timeout=120
)
```

#### 5.5 Retorna el resultado
```
Name       ResourceGroup    Location    Status
--------   --------------   ----------  --------
vm-web     rg-production    eastus      Running
vm-db      rg-production    eastus      Running
```

#### 5.6 Muestra al usuario
```
============================================================
RESULTADO:
============================================================
Name       ResourceGroup    Location    Status
--------   --------------   ----------  --------
vm-web     rg-production    eastus      Running
vm-db      rg-production    eastus      Running
```

---

### ESCENARIO 2: Solicitud del Sistema
```
> que hora es
```

**Flujo:**
1. **Manager** analiza: Es una consulta del sistema
2. Delega a **System Specialist**
3. **System Specialist** ejecuta: `powershell Get-Date`
4. Retorna la fecha/hora

---

### ESCENARIO 3: Solicitud de Documentación
```
> como creo un storage account en azure
```

**Flujo:**
1. **Manager** analiza: Necesita documentación
2. Primero delega a **Docs Researcher**
3. **Docs Researcher** busca: "crear storage account azure"
4. Obtiene documentación de learn.microsoft.com
5. **Docs Researcher** pasa los resultados al Manager
6. **Manager** delega a **Azure Specialist** con la información
7. **Azure Specialist** ejecuta el comando correcto

---

### ESCENARIO 4: Solicitud Compleja (Multi-Agente)
```
> verifica si existe el rg "test-rg" y si no, crealo
```

**Flujo:**
1. **Manager** analiza: Necesita verificar y luego crear
2. Delega a **Azure Specialist** para verificar
3. **Azure Specialist** ejecuta: `az group show -n test-rg`
4. Si existe: Informa al usuario
5. Si NO existe: **Azure Specialist** crea: `az group create -n test-rg -l eastus`
6. **Manager** presenta el resultado final

---

## 🛠️ FUNCIONAMIENTO DETALLADO DE LAS HERRAMIENTAS

### Herramienta 1: SystemCLI (`tools/system_cli.py`)

**Qué hace:** Ejecuta comandos del sistema operativo local.

**Ejemplo de uso:**
```
Usuario: "que hora es"
System Specialist: Usa system_cli con "powershell Get-Date"
```

**Características:**
- Detecta comandos peligrosos (rm, del, format)
- Tiempo de ejecución máximo: 60 segundos
- Limita la respuesta a 3000 caracteres
- Soporta PowerShell y cmd

---

### Herramienta 2: AzureCLI (`tools/azure_cli.py`)

**Qué hace:** Ejecuta comandos de Azure CLI (`az`).

**Ejemplo de uso:**
```
Usuario: "listar vms"
Azure Specialist: Usa azure_cli con "vm list --output table"
```

**Características:**
- El comando NO incluye el prefijo `az`
- Detecta comandos destructivos (delete, remove, purge)
- Tiempo de ejecución máximo: 120 segundos
- Limita la respuesta a 10000 caracteres

---

### Herramienta 3: AzurePowerShell (`tools/azure_powershell.py`)

**Qué hace:** Ejecuta cmdlets del módulo Az de PowerShell.

**Ejemplo de uso:**
```
Usuario: "usa powershell para listar vms"
Azure Specialist: Usa azure_powershell con "Get-AzVM"
```

**Características:**
- Conexión automática a Azure
- Usa credenciales del Service Principal
- Detecta comandos destructivos (Remove-, Delete-)
- Crea archivos temporales para scripts
- Usa `AZURE_SUBSCRIPTION_ID` del entorno

---

### Herramienta 4: Busqueda en Documentación (`tools/docs_search.py`)

**Qué hace:** Busca en la documentación oficial de Microsoft (learn.microsoft.com) usando DuckDuckGo Search.

**Ejemplo de uso:**
```
Usuario: "como creo una vm en azure"
Docs Researcher: Usa AuthDocsSearchTool con "crear vm azure cli"
```

**Características:**
- Busca exclusivamente en **learn.microsoft.com**
- Retorna hasta 3 resultados
- Muestra título, enlace y resumen
- Usa DuckDuckGo Search (ddgs >= 5.0.0)
- Útil cuando el agente no conoce un comando

---

## 🤝 COORDINACIÓN ENTRE AGENTES

### Flujo de Delegación Jerárquica

```
1. Solicitud del Usuario
   ↓
2. Manager (GPT-4.1-mini) Analiza
   ↓
3. Decide QUÉ agente usar
   ├─ Operaciones Azure → Azure Specialist
   ├─ Operaciones Sistema → System Specialist
   └─ Necesita Documentación → Docs Researcher
   ↓
4. Ejecución
   ↓
5. Resultados al Manager
   ↓
6. Manager presenta al Usuario
```

### Ejemplos de Coordinación

**Caso 1: Solicitud simple de Azure**
```
Usuario: "listar vms"
  → Manager delega a Azure Specialist
  → Azure Specialist ejecuta: az vm list --output table
  → Azure Specialist retorna resultado
  → Manager presenta resultado
```

**Caso 2: Solicitud con verificación previa**
```
Usuario: "que archivos hay en el directorio actual"
  → Manager delega a System Specialist
  → System Specialist ejecuta: Get-ChildItem
  → System Specialist retorna resultado
  → Manager presenta resultado
```

**Caso 3: Solicitud desconocida (requiere docs)**
```
Usuario: "como configuro una vnet en azure"
  → Manager NO conoce el comando exacto
  → Manager delega a Docs Researcher
  → Docs Researcher busca: "configurar vnet azure cli"
  → Docs Researcher retorna documentación
  → Manager analiza la documentación
  → Manager delega a Azure Specialist con el comando correcto
  → Azure Specialist ejecuta: az network vnet create ...
  → Manager presenta resultado final
```

**Caso 4: Solicitud compleja multi-paso**
```
Usuario: "lista los vms y dime en que resource groups estan"
  → Manager analiza: Necesita 2 pasos
  → Manager delega a Azure Specialist para listar vms
  → Azure Specialist ejecuta: az vm list --output json
  → Manager procesa los resultados
  → Manager delega a Azure Specialist para listar resource groups
  → Azure Specialist ejecuta: az group list --output json
  → Manager combina los resultados
  → Manager presenta resultado final correlacionado
```

---

## 🧠 CONFIGURACIÓN YAML

### agents.yaml
```yaml
azure_specialist:
  role: Especialista en Infraestructura Azure
  goal: Gestionar e interactuar eficientemente con los recursos de Azure
  backstory: >
    Eres un Ingeniero de Nube experto especializado en Microsoft Azure.
    Conoces todos los comandos de AZ CLI y los módulos de Azure PowerShell.
    ...
  tools: [AzureCLITool, AzurePowerShellTool]

system_specialist:
  role: Especialista de Operaciones de Sistema
  goal: Gestionar operaciones del sistema local
  backstory: >
    Eres un Administrador de Sistemas responsable del entorno local.
    Puedes listar archivos, verificar variables de entorno, ...
  tools: [SystemCLITool]

docs_researcher:
  role: Investigador de Documentación Azure
  goal: Encontrar documentación técnica precisa
  backstory: >
    Eres un Redactor Técnico e Investigador.
    Cuando el equipo no conoce un comando, tú lo buscas.
    Usas las herramientas de búsqueda para encontrar documentación oficial.
  tools: [AuthDocsSearchTool]
```

### tasks.yaml
```yaml
handle_request:
  description: >
    Analiza y ejecuta la solicitud del usuario: "{user_request}"

    Actúa como un orquestador inteligente:
    1. Si la solicitud requiere conocimientos que no son obvios, utiliza al Researcher para buscar en la documentación de Azure.
    2. Si la solicitud implica verificar archivos o estado local, utiliza al System Specialist.
    3. Para crear, listar o modificar recursos de Azure, utiliza al Azure Specialist.

    Debes planificar los pasos lógicos. Por ejemplo, antes de crear un recurso, verifica si ya existe o busca el comando correcto si no estás seguro.

  expected_output: >
    Un informe final detallando las acciones realizadas, los resultados de los comandos ejecutados y cualquier información relevante encontrada.

  agent: azure_specialist  # Agente por defecto (puede cambiar según la solicitud)
```

---

## 💾 GESTIÓN DE ESTADO

### Historial de Conversación
```python
chat_history = []

# Guarda cada intercambio
chat_history.append((user_input, result_str))

# Los últimos 10 mensajes se pasan como contexto
context = "\n\nHISTORIAL DE CONVERSACION RECIENTE:\n"
for q, a in chat_history[-10:]:
    context += f"Usuario: {q}\nAgente: {a}\n"
```

### Reutilización del Crew
```python
crew_instance = AzureOrchestratorCrew()

# Se reusa la misma instancia en cada iteración
result = crew_instance.crew().kickoff(inputs={...})
```

### Memoria de Agentes
- **CrewAI Process.hierarchical**: El manager mantiene contexto de las delegaciones
- **Historial compartido**: Todos los agentes ven el historial de conversación
- **Resultados intermedios**: El manager acumula resultados de múltiples agentes

---

## 🔐 SEGURIDAD

### Detección de comandos peligrosos:

**System CLI:**
```python
dangerous_patterns = ['rm ', 'del ', 'format', 'rmdir', 'rd ', 'deltree']
if any(pattern in command.lower() for pattern in dangerous_patterns):
    return "BLOQUEADO: Comando potencialmente destructivo"
```

**Azure CLI:**
```python
dangerous_patterns = ['delete', 'remove', 'purge', 'deallocate', 'stop']
if any(pattern in command.lower() for pattern in dangerous_patterns):
    print("[AZURE CLI] Comando potencialmente destructivo detectado")
```

**Azure PowerShell:**
```python
dangerous_patterns = ['Remove-', 'Delete-', 'Stop-', 'Deallocate']
if any(pattern in command for pattern in dangerous_patterns):
    print("[AZURE POWERSHELL] Cmdlet potencialmente destructivo detectado")
```

### Timeouts:
- System CLI: 60 segundos
- Azure CLI: 120 segundos
- Azure PowerShell: 120 segundos

---

## 📊 FLUJO COMPLETO DE EJECUCIÓN

```
1. USUARIO INICIA PROGRAMA
   ↓
2. VERIFICAR ENTORNO (.env)
   - Azure OpenAI (API Key o Managed Identity) ✓
   - Azure Service Principal ✓
   ↓
3. LOGIN AZURE CLI
   az login --service-principal
   ↓
4. LISTAR SUSCRIPCIONES
   az account list --output json
   ↓
5. SELECCIONAR SUSCRIPCIÓN
   az account set --subscription "ID"
   Guardar en AZURE_SUBSCRIPTION_ID
   ↓
6. INICIALIZAR CREWAI
   - Crear LLM (GPT-4.1-mini) con API Key o Managed Identity
   - Crear 3 agentes especializados (Azure, System, Docs)
   - Configurar proceso jerárquico con manager
   ↓
7. LOOP INTERACTIVO
   ↓
   7.1 USUARIO ESCRIBE: "listar vms"
   ↓
   7.2 MANAGER ANALIZA
   - ¿Es operación Azure? SÍ
   - ¿Conoce el comando? SÍ
   - ¿Qué agente? Azure Specialist
   ↓
   7.3 MANAGER DELEGA A AZURE SPECIALIST
   ↓
   7.4 AZURE SPECIALIST EJECUTA
   az vm list --output table
   ↓
   7.5 AZURE SPECIALIST RETORNA RESULTADO
   ↓
   7.6 MANAGER PRESENTA RESULTADO
   (tabla con las VMs)
   ↓
   7.7 GUARDA EN HISTORIAL
   ↓
   7.8 VUELTA AL PASO 7.1
   (hasta que usuario escribe "exit")
```

**FLUJO CON DOCUMENTACIÓN:**

```
7.2 MANAGER ANALIZA
   - ¿Es operación Azure? SÍ
   - ¿Conoce el comando? NO
   ↓
7.3 MANAGER DELEGA A DOCS RESEARCHER
   ↓
7.4 DOCS RESEARCHER BUSCA
   "crear storage account azure cli"
   ↓
7.5 DOCS RESEARCHER RETORNA DOCS
   - Títulos, enlaces y resúmenes
   ↓
7.6 MANAGER ANALIZA DOCUMENTACIÓN
   ↓
7.7 MANAGER DELEGA A AZURE SPECIALIST
   ↓
7.8 AZURE SPECIALIST EJECUTA
   az storage account create ...
   ↓
7.9 MANAGER PRESENTA RESULTADO FINAL
```

---

## 🎯 EJEMPLOS DE USO

### Ejemplo 1: Comando del sistema (System Specialist)
```
> que hora es

[*] Procesando: que hora es
------------------------------------------------------------

[MANAGER] Delegando a System Specialist...

[SYSTEM CLI] Ejecutando: powershell Get-Date

[SYSTEM CLI] Completado (codigo: 0)

============================================================
RESULTADO:
============================================================
Monday, January 26, 2026 2:45:30 PM
```

### Ejemplo 2: Azure CLI - Listar VMs (Azure Specialist)
```
> listar vms

[*] Procesando: listar vms
------------------------------------------------------------

[MANAGER] Delegando a Azure Specialist...

[AZURE CLI] Ejecutando: az vm list --output table

[AZURE CLI] Completado (codigo: 0)

============================================================
RESULTADO:
============================================================
Name       ResourceGroup    Location    Status
--------   --------------   ----------  --------
vm-web     rg-production    eastus      Running
vm-db      rg-production    eastus      Running
```

### Ejemplo 3: Azure PowerShell (Azure Specialist)
```
> usa powershell para listar los resource groups

[*] Procesando: usa powershell para listar los resource groups
------------------------------------------------------------

[MANAGER] Delegando a Azure Specialist...

[AZURE POWERSHELL] Ejecutando: Get-AzResourceGroup

[AZURE POWERSHELL] Completado (codigo: 0)

============================================================
RESULTADO:
============================================================
ResourceGroupName Location
----------------- --------
rg-production     eastus
rg-test          westus
```

### Ejemplo 4: Búsqueda en Documentación (Docs Researcher + Azure Specialist)
```
> como creo un storage account en azure

[*] Procesando: como creo un storage account en azure
------------------------------------------------------------

[MANAGER] No conozco el comando exacto. Delegando a Docs Researcher...

[DOCS RESEARCHER] Buscando: crear storage account azure cli

[DOCS RESEARCHER] Resultados:
- Titulo: Crear una cuenta de almacenamiento en Azure con la CLI de Azure
  Link: https://learn.microsoft.com/es-es/azure/storage/common/storage-account-create?tabs=azure-cli
  Resumen: En este artículo aprenderá a crear una cuenta de almacenamiento...

[MANAGER] Documentación encontrada. Delegando a Azure Specialist...

[AZURE CLI] Ejecutando: az storage account create -n mystorageaccount -l eastus -g myresourcegroup

[AZURE CLI] Completado (codigo: 0)

============================================================
RESULTADO:
============================================================
{
  "id": "/subscriptions/.../storageAccounts/mystorageaccount",
  "location": "eastus",
  "name": "mystorageaccount",
  ...
}

Documentación consultada: https://learn.microsoft.com/es-es/azure/storage/common/storage-account-create
```

### Ejemplo 5: Solicitud compleja multi-paso
```
> verifica si existe el rg "test-rg" y si no, crealo

[*] Procesando: verifica si existe el rg "test-rg" y si no, crealo
------------------------------------------------------------

[MANAGER] Necesito verificar y luego crear. Delegando a Azure Specialist...

[AZURE CLI] Ejecutando: az group show -n test-rg

[AZURE CLI] Error: Resource group 'test-rg' could not be found.

[MANAGER] Resource group no existe. Creando...

[AZURE CLI] Ejecutando: az group create -n test-rg -l eastus

[AZURE CLI] Completado (codigo: 0)

============================================================
RESULTADO:
============================================================
✓ Verificado: El resource group "test-rg" no existía.
✓ Creado: Resource group "test-rg" en eastus.

ID: /subscriptions/.../resourceGroups/test-rg
Location: eastus
ProvisioningState: Succeeded
```

---

## ⚙️ CONFIGURACIÓN REQUERIDA

### Archivo `.env`:

**Opción 1: API Key (Modo Clásico)**
```env
# Azure OpenAI con API Key
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure Service Principal
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=...
AZURE_SUBSCRIPTION_ID=...
```

**Opción 2: Managed Identity (UMI)**
```env
# Azure OpenAI con Managed Identity (sin API Key)
AZURE_AQUIDENTIY_CLIENT_ID=7bef6d90-a33a-4453-930c-0ce8abd23d5f  # Opcional
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure Service Principal
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
AZURE_TENANT_ID=...
AZURE_SUBSCRIPTION_ID=...
```

### Dependencias:
```toml
dependencies = [
    "crewai[tools]>=0.86.0",
    "python-dotenv>=1.0.0",
    "azure-identity>=1.15.0",
    "ddgs>=5.0.0",
]
```

---

## 🚀 RESUMEN

El proyecto es un **asistente inteligente multi-agente** que:

1. **Recibe** comandos en español del usuario
2. **Usa un Manager (Azure OpenAI GPT-4.1-mini)** para coordinar:
   - **Azure Specialist**: Operaciones de Azure
   - **System Specialist**: Operaciones del sistema
   - **Docs Researcher**: Búsqueda en documentación
3. **Delega tareas** al agente apropiado según la solicitud
4. **Ejecuta** comandos técnicos automáticamente:
   - Comandos del sistema local
   - Comandos Azure CLI
   - Cmdlets Azure PowerShell
   - Búsqueda en documentación oficial
5. **Coordina** múltiples agentes para tareas complejas
6. **Mantiene** un historial de conversación
7. **Detecta** comandos peligrosos para evitar accidentes

### Ventajas principales:
- **Multi-agente especializado**: Cada agente es experto en su dominio
- **Coordinación jerárquica**: Manager optimiza la ejecución de tareas
- No necesitas conocer comandos técnicos
- Interfaz en lenguaje natural
- Automatización completa
- Seguridad integrada
- Múltiples opciones de ejecución (CLI, PowerShell)
- Búsqueda en documentación oficial cuando no conoce un comando
- Soporte para Managed Identity (más seguro)
- Tareas complejas con múltiples agentes

### Stack Tecnológico:
- **Python**: Lenguaje principal
- **CrewAI**: Framework de multi-agentes
- **Azure OpenAI**: GPT-4.1-mini como LLM (Manager)
- **Azure Identity**: Gestión de credenciales y tokens
- **DuckDuckGo Search**: Búsqueda en documentación
- **Azure CLI**: Gestión de recursos Azure
- **PowerShell**: Cmdlets del módulo Az

---

## 📚 ESTRUCTURA DE ARCHIVOS

```
a2a_protocolo_crewai/
├── .env                          # Credenciales
├── pyproject.toml                # Dependencias
├── README.md                     # Documentación principal
├── EXPLAIN.md                    # Este archivo
└── src/
    └── a2a_protocolo_crewai/
        ├── __init__.py
        ├── main.py              # Punto de entrada
        ├── crew.py              # Definición del Crew
        ├── config/
        │   ├── agents.yaml      # Configuración de los 3 agentes
        │   └── tasks.yaml       # Configuración de tareas
        └── tools/
            ├── __init__.py
            ├── system_cli.py     # Herramienta de sistema
            ├── azure_cli.py      # Herramienta Azure CLI
            ├── azure_powershell.py  # Herramienta Azure PowerShell
            └── docs_search.py    # Búsqueda en documentación
```

---

## 🎓 CONCEPTOS CLAVE

### Agent-to-Agent (A2A)
Sistema multi-agente donde los agentes colaboran entre sí para completar tareas complejas.

### Process Hierarchical (Proceso Jerárquico)
Modo de ejecución de CrewAI donde un manager coordina a múltiples agentes especializados.

### CrewAI
Framework de Python para construir equipos de agentes IA que trabajan juntos.

### Azure OpenAI
Servicio de Microsoft que proporciona acceso a modelos de IA de OpenAI (GPT-4, etc.) alojados en Azure.

### Managed Identity (UMI)
Característica de Azure que permite a los servicios autenticarse automáticamente sin necesidad de credenciales explícitas.

### Service Principal
Identidad de aplicación en Azure que permite autenticación programática sin necesidad de credenciales de usuario.

### Model Context Protocol (MCP)
Protocolo estándar para conectar modelos de IA con herramientas y servicios externos (futuro).

### DuckDuckGo Search (ddgs)
Librería de Python para realizar búsquedas en DuckDuckGo sin API key. Usada para buscar en learn.microsoft.com.

---

## 🚧 ESTADO ACTUAL DEL PROYECTO

### ✅ Implementado:
- [x] Login automático con Service Principal
- [x] Selección de suscripciones
- [x] **3 agentes especializados** (Azure, System, Docs)
- [x] **Proceso jerárquico** con Manager
- [x] Agente ejecutor con Azure OpenAI (GPT-4.1-mini)
- [x] Soporte para **API Key** y **Managed Identity** (UMI)
- [x] 4 herramientas: System CLI, Azure CLI, Azure PowerShell, Búsqueda en Docs
- [x] Configuración YAML para agentes y tareas
- [x] Detección de comandos peligrosos
- [x] Historial de conversación
- [x] Timeouts en comandos
- [x] Validación de entorno
- [x] Búsqueda en documentación oficial de Microsoft
- [x] Coordinación multi-agente para tareas complejas

### 🔄 Posibles Mejoras:
- [ ] Integración con Azure MCP Server
- [ ] Más agentes especializados (Red, Security, Monitoring)
- [ ] Validación de comandos antes de ejecutar
- [ ] Soporte para comandos más complejos
- [ ] Mejor manejo de errores y recuperaciones
- [ ] Caché de resultados de búsqueda en docs
- [ ] Parallel execution para tareas independientes

---

## 📖 REFERENCIAS

- [CrewAI Documentation](https://docs.crewai.com/)
- [Azure CLI Documentation](https://docs.microsoft.com/cli/azure/)
- [Azure PowerShell Documentation](https://docs.microsoft.com/powershell/azure/)
- [Azure OpenAI Service](https://docs.microsoft.com/azure/cognitive-services/openai/)
- [Azure Identity Documentation](https://docs.microsoft.com/python/api/azure-identity/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [DuckDuckGo Search (ddgs)](https://github.com/deedy5/ddgs)

---

**Última actualización**: Enero 2026
**Versión del proyecto**: 8.0.0
**Novedades en esta versión**:
- ✅ **Arquitectura multi-agente** con 3 especialistas
- ✅ **Proceso jerárquico** (Manager + Agentes)
- ✅ Configuración YAML para agentes y tareas
- ✅ Coordinación automática entre agentes
- ✅ Mejor organización y especialización
- ✅ Soporte para tareas complejas multi-paso
