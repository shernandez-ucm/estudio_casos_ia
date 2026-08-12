import json
import re

from langchain_core.prompts import ChatPromptTemplate

from ..config import llm_json
from ..json_utils import parse_llm_json
from ..prompts import QUERY_FORMATTING_PROMPT
from ..state import PresentationState
from ..status import agent_start, agent_status, agent_warning


def format_queries(state: PresentationState):
    """Nodo 2: Traduce al inglés, simplifica a palabras clave y da formato booleano
    (+ AND) a las consultas, para el endpoint Search API de Semantic Scholar.
    """
    raw_queries = state.get("queries", [])
    agent_start(
        2, "Formateo de Consultas",
        f"Traduciendo al inglés y formateando {len(raw_queries)} consulta(s) para Semantic Scholar...",
    )
    if not raw_queries:
        agent_status("No hay consultas que formatear; se omite este paso.")
        return {"queries": []}

    prompt = ChatPromptTemplate.from_template(QUERY_FORMATTING_PROMPT)
    chain = prompt | llm_json

    response = chain.invoke({"queries": json.dumps(raw_queries, ensure_ascii=False)})

    formatted_queries = []
    try:
        data = parse_llm_json(response.content)
        formatted_queries = [q for q in data.get("consultas_formateadas", []) if q]
    except json.JSONDecodeError:
        formatted_queries = []

    # Respaldo determinista si el LLM falla o no devuelve JSON válido
    if not formatted_queries:
        agent_warning("El modelo no devolvió JSON válido; usando formateo de respaldo (unión literal de términos).")
        for q in raw_queries:
            terms = re.findall(r"\w+", q, flags=re.UNICODE)
            if terms:
                formatted_queries.append("+".join(terms))
    else:
        agent_status(f"{len(formatted_queries)} consulta(s) formateada(s): {formatted_queries}")

    return {"queries": formatted_queries}
