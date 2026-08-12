import requests

from ..config import S2_SEARCH_URL
from ..state import PresentationState
from ..status import agent_start, agent_status, agent_warning


def execute_searches(state: PresentationState):
    """Nodo 3: Ejecuta búsquedas reales en Semantic Scholar (Search API, por relevancia)."""
    queries = state["queries"]
    current_context = state.get("context", [])
    current_references = state.get("references", [])
    current_abstracts = state.get("abstracts", [])
    current_papers = state.get("papers", [])
    new_results = []
    new_references = []
    new_abstracts = []
    new_papers = []

    # Cantidad de resultados a conservar por cada consulta (configurable en el estado)
    max_results = state.get("max_results_per_query", 10)

    agent_start(
        3, "Búsqueda en Semantic Scholar",
        f"Ejecutando {len(queries)} consulta(s) contra el Search API (hasta {max_results} resultado(s) c/u)...",
    )

    for q in queries:
        agent_status(f"Consulta: {q}")
        try:
            # Ejecutar la búsqueda en el endpoint Search API (por relevancia, no admite 'sort')
            # Filtrando papers poco citados; limit=100 admite un margen para descartar los que no tengan abstract
            # Sin autenticación: el endpoint admite acceso no autenticado (sujeto a límites de tasa compartidos)
            rsp = requests.get(
                S2_SEARCH_URL,
                params={
                    "query": q,
                    "fields": "title,authors,year,abstract,url,citationCount",
                    "minCitationCount": "10",
                    "limit": 100,
                },
            )
            rsp.raise_for_status()
            results = rsp.json()
            papers = results.get("data", [])

            # Descartar papers sin abstract, para que todos los seleccionados lo tengan
            papers = [p for p in papers if (p.get("abstract") or "").strip()]

            if not papers:
                # Si no hay resultados con abstract disponible para esa consulta
                agent_warning(f"Sin resultados con abstract disponible para '{q}'.")
                new_results.append(f"[Semantic Scholar] No se encontraron papers con abstract disponible para la consulta: '{q}'")
                continue
            agent_status(f"{len(papers)} resultado(s) con abstract disponible (usando hasta {max_results}).")

            # Conservar la lista de resultados (no solo el primero), hasta max_results
            for paper in papers[:max_results]:
                title = paper.get("title") or "Sin título"
                authors = ", ".join(a.get("name", "") for a in paper.get("authors", [])) or "Autor desconocido"
                year = paper.get("year") or "Año desconocido"
                abstract = paper.get("abstract").strip()
                url = paper.get("url") or ""
                citation_count = paper.get("citationCount") or 0

                # Número de referencia único, consecutivo a las ya acumuladas
                ref_index = len(current_references) + len(new_references) + 1

                # Formatear el resultado para el LLM, etiquetado con su número de referencia
                result_str = (
                    f"[Documento Científico #{ref_index}]\n"
                    f"Título: {title}\n"
                    f"Autores: {authors} ({year})\n"
                    f"Resumen/Hallazgos: {abstract}\n"
                )
                new_results.append(result_str)

                # Guardar la referencia bibliográfica correspondiente
                reference_str = f"[{ref_index}] {authors} ({year}). {title}. {url}".strip()
                new_references.append(reference_str)

                # Guardar el abstract asociado a esa misma referencia
                abstract_str = f"[{ref_index}] {title}: {abstract}"
                new_abstracts.append(abstract_str)

                # Guardar los datos estructurados del artículo para el ranking posterior
                new_papers.append({
                    "ref_index": ref_index,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "url": url,
                    "citation_count": citation_count,
                })

        except requests.RequestException as e:
            # Manejo de errores de conexión o rate-limiting
            agent_warning(f"Fallo al buscar '{q}': {str(e)}")
            new_results.append(f"[Error de Búsqueda] Fallo al buscar '{q}': {str(e)}")

    agent_status(f"Total acumulado: {len(current_papers) + len(new_papers)} artículo(s) recopilado(s).")

    return {
        "context": current_context + new_results,
        "references": current_references + new_references,
        "abstracts": current_abstracts + new_abstracts,
        "papers": current_papers + new_papers,
        "iterations": state.get("iterations", 0) + 1
    }
