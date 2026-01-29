from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .mcp_client import run_mcp_tool_sync
import asyncio
import os
import sys

# Importaciones de MCP
from mcp import ClientSession
from mcp.client.sse import sse_client

class AuthDocsSearchToolInput(BaseModel):
    """Input schema for AuthDocsSearchTool."""
    query: str = Field(..., description="La pregunta o termino de busqueda sobre Azure.")

class AuthDocsSearchTool(BaseTool):
    name: str = "Busqueda Documentacion Azure (MCP)"
    description: str = (
        "Util para buscar informacion oficial sobre comandos, servicios y configuraciones de Azure "
        "en la documentacion de Microsoft (learn.microsoft.com). "
        "Usa esta herramienta cuando no sepas como usar un comando o necesites ejemplos."
        "Ejecuta la busqueda a traves de un servidor MCP local."
    )
    args_schema: Type[BaseModel] = AuthDocsSearchToolInput

    def _run(self, query: str) -> str:
        """Ejecuta la busqueda a traves del Agente Docs (Puerto 9000)."""
        return run_mcp_tool_sync(9000, "search_docs", {"query": query})

    async def _run_async(self, query: str) -> str:
        return self._run(query)
