from fastmcp import FastMCP
from duckduckgo_search import DDGS
from dotenv import load_dotenv

load_dotenv()
import sys

# Crear el servidor MCP
mcp = FastMCP("azure-docs-search")

@mcp.tool()
def search_docs(query: str) -> str:
    """
    Busca documentacion en learn.microsoft.com sobre Azure.
    Retorna un string con los resultados (titulo, link, resumen).
    """
    # Escribir a stderr para no romper el protocolo JSON-RPC en stdout
    sys.stderr.write(f"[MCP SERVER] Buscando: {query}\n")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # DDGS usa httpx internamente, a veces falla la primera conexion
            with DDGS(timeout=20) as ddgs:
                # Forzamos busqueda en sitio oficial
                search_query = f"site:learn.microsoft.com {query}"
                # Ajustamos region a wt-wt (global) para evitar bloqueos regionales
                results = list(ddgs.text(search_query, region='wt-wt', max_results=3))
                
                if not results:
                    return "No se encontraron resultados en la documentación oficial."
                
                formatted_results = []
                for r in results:
                    title = r.get('title', 'Sin titulo')
                    href = r.get('href', '#')
                    body = r.get('body', 'Sin descripcion')
                    formatted_results.append(f"- Titulo: {title}\n  Link: {href}\n  Resumen: {body}\n")
                
                return "\n".join(formatted_results)

        except Exception as e:
            sys.stderr.write(f"[WARNING] Intento {attempt+1}/{max_retries} fallido: {str(e)}\n")
            if attempt == max_retries - 1:
                return f"Error en la busqueda tras {max_retries} intentos: {str(e)}"
            import time
            time.sleep(1) # Esperar un segundo antes de reintentar

if __name__ == "__main__":
    # Ejecuta el servidor usando SSE en puerto 9000 por defecto
    mcp.run(transport="sse", port=9000)
