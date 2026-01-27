import os
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

# FIXED IMPORTS - Matching filenames in src/a2a_protocolo_crewai/tools/
from .tools.system_cli import SystemCLITool
from .tools.azure_cli import AzureCLITool
from .tools.azure_powershell import AzurePowerShellTool
from .tools.docs_search import AuthDocsSearchTool

load_dotenv()

def create_azure_openai_llm():
    """Crea una instancia de LLM usando Azure OpenAI."""
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

    if not endpoint or not deployment:
        raise ValueError(
            "Azure OpenAI no configurado. Verifica AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_DEPLOYMENT en .env"
        )

    # Si hay API Key configurada, usarla (modo clasico)
    if api_key:
        return LLM(
            model=f"azure/{deployment}",
            api_key=api_key,
            base_url=f"{endpoint}/openai/deployments/{deployment}",
            api_version=api_version,
            temperature=0.1,
        )
    
    # Si no, intentar usar Managed Identity (DefaultAzureCredential)
    try:
        # Verificar si hay un Client ID especifico para la UMI de OpenAI
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
        
        # En Litellm (usado por CrewAI), se pasa azure_ad_token_provider
        return LLM(
            model=f"azure/{deployment}",
            base_url=f"{endpoint}/openai/deployments/{deployment}",
            api_version=api_version,
            temperature=0.1,
            azure_ad_token_provider=token_provider
        )
    except Exception as e:
        raise ValueError(f"Fallo al autenticar con Managed Identity: {str(e)}")

@CrewBase
class AzureOrchestratorCrew:
    """AzureOrchestrator crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """Inicializa el crew."""
        self.llm = create_azure_openai_llm()

    @agent
    def azure_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['azure_specialist'],
            tools=[AzureCLITool(), AzurePowerShellTool()],
            verbose=True,
            llm=self.llm
        )

    @agent
    def system_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['system_specialist'],
            tools=[SystemCLITool()],
            verbose=True,
            llm=self.llm
        )

    @agent
    def docs_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['docs_researcher'],
            tools=[AuthDocsSearchTool()],
            verbose=True,
            llm=self.llm
        )

    @task
    def handle_request(self) -> Task:
        return Task(
            config=self.tasks_config['handle_request'],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the AzureOrchestrator crew"""
        return Crew(
            agents=self.agents, # Automatically collected by the @agent decorator
            tasks=self.tasks,   # Automatically collected by the @task decorator
            process=Process.hierarchical,
            manager_llm=self.llm,
            verbose=True,
        )
