import json
import re

from langchain_core.prompts import ChatPromptTemplate

from ..config import llm_json
from ..prompts import QUERY_FORMATTING_PROMPT
from ..state import PresentationState


def format_queries(state: PresentationState):
    """Nodo 2: Traduce al inglés, simplifica a palabras clave y da formato booleano
    (+ AND) a las consultas, según la sintaxis del endpoint Bulk Search de Semantic Scholar.
    """
    raw_queries = state.get("queries", [])
    if not raw_queries:
        return {"queries": []}

    prompt = ChatPromptTemplate.from_template(QUERY_FORMATTING_PROMPT)
    chain = prompt | llm_json

    response = chain.invoke({"queries": json.dumps(raw_queries, ensure_ascii=False)})

    formatted_queries = []
    try:
        data = json.loads(response.content)
        formatted_queries = [q for q in data.get("consultas_formateadas", []) if q]
    except json.JSONDecodeError:
        formatted_queries = []

    # Respaldo determinista si el LLM falla o no devuelve JSON válido
    if not formatted_queries:
        for q in raw_queries:
            terms = re.findall(r"\w+", q, flags=re.UNICODE)
            if terms:
                formatted_queries.append("+".join(terms))

    return {"queries": formatted_queries}
