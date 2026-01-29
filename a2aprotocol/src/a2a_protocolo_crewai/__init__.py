"""
Orquestador Azure con Protocolo A2A.

Este paquete implementa un ejemplo completo de comunicacion
Agent-to-Agent (A2A) usando CrewAI para gestionar recursos Azure.

Mecanismos de comunicacion A2A demostrados:
- Delegacion de tareas (allow_delegation)
- Transferencia de contexto entre tareas (context)
- Memoria compartida entre agentes (memory)
- Proceso jerarquico con manager (Process.hierarchical)

Herramientas disponibles:
- System CLI: Comandos del sistema operativo
- Azure CLI: Comandos az para Azure
- Azure PowerShell: Cmdlets del modulo Az

Uso basico:
    from a2a_protocolo_crewai import AzureOrchestratorCrew

    crew = AzureOrchestratorCrew()
    result = crew.crew().kickoff(inputs={...})

Para mas informacion, consulta README.md
"""

from .main import main

__version__ = "2.1.0"
__all__ = ["main"]
