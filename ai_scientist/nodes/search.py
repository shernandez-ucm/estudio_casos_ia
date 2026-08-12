import time

import requests

from ..config import OPENALEX_MAILTO, OPENALEX_SEARCH_URL, S2_SEARCH_URL, SEARCH_PROVIDER
from ..state import PresentationState
from ..status import agent_start, agent_status, agent_warning

# Reintentos con backoff exponencial ante 429 (límite de tasa del endpoint no autenticado)
MAX_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 1.1


def _get_with_backoff(url, params):
    """Ejecuta un GET reintentando con backoff exponencial (2s, 4s, 8s, ...) ante
    respuestas 429 (rate limit). Otros errores HTTP se propagan de inmediato."""
    backoff = INITIAL_BACKOFF_SECONDS
    for attempt in range(MAX_RETRIES + 1):
        rsp = requests.get(url, params=params)
        if rsp.status_code != 429:
            rsp.raise_for_status()
            return rsp

        if attempt == MAX_RETRIES:
            rsp.raise_for_status()  # agota los reintentos: propaga el 429 como HTTPError

        agent_warning(
            f"Límite de tasa alcanzado (429); reintentando en {backoff}s "
            f"(intento {attempt + 1}/{MAX_RETRIES})..."
        )
        time.sleep(backoff)
        backoff *= 2


def _search_semantic_scholar(query, limit=100):
    """Busca en Semantic Scholar (Search API, por relevancia, no admite 'sort') y
    devuelve una lista de papers normalizados (title, authors, year, abstract, url,
    citation_count), descartando los que no tengan abstract."""
    rsp = _get_with_backoff(
        S2_SEARCH_URL,
        params={
            "query": query,
            "fields": "title,authors,year,abstract,url,citationCount",
            "minCitationCount": "10",
            "limit": limit,
        },
    )
    papers = rsp.json().get("data", [])

    normalized = []
    for p in papers:
        abstract = (p.get("abstract") or "").strip()
        if not abstract:
            continue
        normalized.append({
            "title": p.get("title") or "Sin título",
            "authors": ", ".join(a.get("name", "") for a in p.get("authors", [])) or "Autor desconocido",
            "year": p.get("year") or "Año desconocido",
            "abstract": abstract,
            "url": p.get("url") or "",
            "citation_count": p.get("citationCount") or 0,
        })
    return normalized


def _reconstruct_openalex_abstract(inverted_index):
    """OpenAlex entrega el abstract como índice invertido {palabra: [posiciones]}
    (para evitar restricciones de copyright); se reconstruye el texto a partir de él."""
    if not inverted_index:
        return ""
    positions = [(pos, word) for word, idxs in inverted_index.items() for pos in idxs]
    positions.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positions)


def _search_openalex(query, per_page=100):
    """Busca en OpenAlex (Works API, ver https://help.openalex.org/quickstart/) y
    devuelve una lista de papers normalizados (title, authors, year, abstract, url,
    citation_count), descartando los que no tengan abstract."""
    params = {
        "search": query,
        "filter": "cited_by_count:>10",
        "per-page": per_page,
        "select": "title,publication_year,cited_by_count,authorships,abstract_inverted_index,primary_location,doi",
    }
    if OPENALEX_MAILTO:
        # Correo de contacto: habilita el "polite pool" de OpenAlex (mejor límite de tasa)
        params["mailto"] = OPENALEX_MAILTO

    rsp = _get_with_backoff(OPENALEX_SEARCH_URL, params=params)
    works = rsp.json().get("results", [])

    normalized = []
    for w in works:
        abstract = _reconstruct_openalex_abstract(w.get("abstract_inverted_index")).strip()
        if not abstract:
            continue
        authors = ", ".join(
            (a.get("author") or {}).get("display_name", "") for a in w.get("authorships", [])
        ) or "Autor desconocido"
        primary_location = w.get("primary_location") or {}
        url = primary_location.get("landing_page_url") or (
            f"https://doi.org/{w['doi']}" if w.get("doi") else ""
        )
        normalized.append({
            "title": w.get("title") or "Sin título",
            "authors": authors,
            "year": w.get("publication_year") or "Año desconocido",
            "abstract": abstract,
            "url": url,
            "citation_count": w.get("cited_by_count") or 0,
        })
    return normalized


# Nombre de despliegue y función de búsqueda normalizada de cada proveedor soportado
_SEARCH_PROVIDERS = {
    "semantic_scholar": ("Semantic Scholar", _search_semantic_scholar),
    "openalex": ("OpenAlex", _search_openalex),
}


def execute_searches(state: PresentationState):
    """Nodo 3: Ejecuta búsquedas reales contra el proveedor configurado (SEARCH_PROVIDER)."""
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

    provider_name, search_fn = _SEARCH_PROVIDERS[SEARCH_PROVIDER]

    agent_start(
        3, "Búsqueda Bibliográfica",
        f"Ejecutando {len(queries)} consulta(s) contra {provider_name} (hasta {max_results} resultado(s) c/u)...",
    )

    for q in queries:
        agent_status(f"Consulta: {q}")
        try:
            # Sin autenticación: el endpoint admite acceso no autenticado (sujeto a límites de tasa compartidos)
            papers = search_fn(q)

            if not papers:
                # Si no hay resultados con abstract disponible para esa consulta
                agent_warning(f"Sin resultados con abstract disponible para '{q}'.")
                new_results.append(f"[{provider_name}] No se encontraron papers con abstract disponible para la consulta: '{q}'")
                continue
            agent_status(f"{len(papers)} resultado(s) con abstract disponible (usando hasta {max_results}).")

            # Conservar la lista de resultados (no solo el primero), hasta max_results
            for paper in papers[:max_results]:
                title = paper["title"]
                authors = paper["authors"]
                year = paper["year"]
                abstract = paper["abstract"]
                url = paper["url"]
                citation_count = paper["citation_count"]

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
