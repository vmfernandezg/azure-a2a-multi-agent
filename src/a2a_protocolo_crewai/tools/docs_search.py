from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
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
        """Ejecuta la herramienta conectando al servidor MCP local."""
        return asyncio.run(self._run_async(query))

    async def _run_async(self, query: str) -> str:
        # Configurar parametros del servidor
        # Asumimos que mcp_server.py esta en la raiz del proyecto mcpddgs
        # Buscamos el archivo subiendo niveles si es necesario
        current_dir = os.getcwd()
        server_script = os.path.join(current_dir, "mcp_server.py")
        
        if not os.path.exists(server_script):
             return f"Error: No se encuentra el servidor MCP en {server_script}. CWD: {current_dir}"

        try:
            # Conexión SSE al servidor MCP local (asumimos puerto 8000)
            url = "http://localhost:8000/sse"
            
            async with sse_client(url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Llamar a la herramienta 'search_docs' definida en el servidor
                    result = await session.call_tool("search_docs", arguments={"query": query})
                    
                    if result and result.content:
                        text_content = "\n".join([c.text for c in result.content if c.type == 'text'])
                        return text_content
                    return "No se recibió contenido del servidor MCP."

        except Exception as e:
            return f"Error conectando al servidor MCP (HTTP/SSE): {str(e)}"
