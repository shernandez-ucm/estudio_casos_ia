import requests

from ..config import S2_API_KEY, S2_SEARCH_URL
from ..state import PresentationState


def execute_searches(state: PresentationState):
    """Nodo 3: Ejecuta búsquedas reales en Semantic Scholar (Bulk Search)."""
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

    print(f"\n[Buscando en Semantic Scholar (Bulk Search)...]")

    headers = {"X-API-KEY": S2_API_KEY} if S2_API_KEY else {}

    for q in queries:
        print(f" -> Consulta: {q}")
        try:
            # Ejecutar la búsqueda en el endpoint Bulk Search (no admite el parámetro 'limit')
            # Ordenada por cantidad de citas descendente, filtrando papers poco citados
            rsp = requests.get(
                S2_SEARCH_URL,
                headers=headers,
                params={
                    "query": q,
                    "fields": "title,authors,year,abstract,url,citationCount",
                    "sort": "publicationDate:desc",
                    "minCitationCount": "10",
                },
            )
            rsp.raise_for_status()
            results = rsp.json()
            papers = results.get("data", [])

            # Descartar papers sin abstract, para que todos los seleccionados lo tengan
            papers = [p for p in papers if (p.get("abstract") or "").strip()]

            if not papers:
                # Si no hay resultados con abstract disponible para esa consulta
                new_results.append(f"[Semantic Scholar] No se encontraron papers con abstract disponible para la consulta: '{q}'")
                continue
            print(f"   -> {len(papers)} resultados con abstract disponible (usando hasta {max_results}).")

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
            new_results.append(f"[Error de Búsqueda] Fallo al buscar '{q}': {str(e)}")

    return {
        "context": current_context + new_results,
        "references": current_references + new_references,
        "abstracts": current_abstracts + new_abstracts,
        "papers": current_papers + new_papers,
        "iterations": state.get("iterations", 0) + 1
    }
