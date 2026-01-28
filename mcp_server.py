from fastmcp import FastMCP
from duckduckgo_search import DDGS
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
    try:
        with DDGS() as ddgs:
            # Forzamos busqueda en sitio oficial
            search_query = f"site:learn.microsoft.com {query}"
            results = list(ddgs.text(search_query, max_results=3))
            
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
        sys.stderr.write(f"[ERROR] {str(e)}\n")
        return f"Error en la busqueda: {str(e)}"

if __name__ == "__main__":
    # Ejecuta el servidor usando stdio
    mcp.run()
