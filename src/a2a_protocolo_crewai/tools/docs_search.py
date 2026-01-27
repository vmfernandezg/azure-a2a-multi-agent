from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from ddgs import DDGS

class AuthDocsSearchToolInput(BaseModel):
    """Input schema for AuthDocsSearchTool."""
    query: str = Field(..., description="La pregunta o termino de busqueda sobre Azure.")

class AuthDocsSearchTool(BaseTool):
    name: str = "Busqueda Documentacion Azure"
    description: str = (
        "Util para buscar informacion oficial sobre comandos, servicios y configuraciones de Azure "
        "en la documentacion de Microsoft (learn.microsoft.com). "
        "Usa esta herramienta cuando no sepas como usar un comando o necesites ejemplos."
    )
    args_schema: Type[BaseModel] = AuthDocsSearchToolInput

    def _run(self, query: str) -> str:
        try:
            # Forzar busqueda en dominio oficial
            site_query = f"{query} site:learn.microsoft.com"
            
            with DDGS() as ddgs:
                results = list(ddgs.text(site_query, max_results=3))
            
            if not results:
                return "No se encontraron resultados en la documentacion oficial."

            formatted_results = []
            for r in results:
                formatted_results.append(
                    f"- Titulo: {r.get('title')}\n"
                    f"  Link: {r.get('href')}\n"
                    f"  Resumen: {r.get('body')}\n"
                )
            
            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error buscando en documentacion: {str(e)}"
