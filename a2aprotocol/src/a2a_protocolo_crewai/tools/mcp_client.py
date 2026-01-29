import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
import os

async def execute_mcp_tool(port: int, tool_name: str, arguments: dict) -> str:
    """
    Conecta a un servidor FastMCP local vía SSE y ejecuta una herramienta.
    """
    url = f"http://localhost:{port}/sse"
    try:
        async with sse_client(url, timeout=30) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Llamar a la herramienta
                result = await session.call_tool(tool_name, arguments=arguments)
                
                if result and result.content:
                    text_content = "\n".join([c.text for c in result.content if c.type == 'text'])
                    return text_content
                return "[MCP WARNING] No se recibió contenido del servidor."

    except Exception as e:
        return f"[MCP ERROR] Fallo conexión a localhost:{port}/{tool_name}: {str(e)}"

def run_mcp_tool_sync(port: int, tool_name: str, arguments: dict) -> str:
    """Wrapper síncrono para ser llamado desde herramientas de CrewAI."""
    return asyncio.run(execute_mcp_tool(port, tool_name, arguments))
