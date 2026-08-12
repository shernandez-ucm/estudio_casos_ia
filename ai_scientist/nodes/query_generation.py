import json

from langchain_core.prompts import ChatPromptTemplate

from ..config import llm_json
from ..json_utils import parse_llm_json
from ..prompts import QUERY_GENERATION_PROMPT
from ..state import PresentationState
from ..status import agent_start, agent_status, agent_warning


def generate_queries(state: PresentationState):
    """Nodo 1: Genera consultas enfocadas en el temario universitario."""
    iterations = state.get("iterations", 0)
    max_iterations = state["max_iterations"]
    agent_start(
        1, "Generación de Consultas",
        f"Analizando el contexto recopilado (iteración {iterations + 1}/{max_iterations}) "
        f"para generar nuevas consultas de búsqueda sobre '{state['topico']}'...",
    )

    context_str = "\n".join(state.get("context", [])) if state.get("context") else "Ninguno todavía."

    prompt = ChatPromptTemplate.from_template(QUERY_GENERATION_PROMPT)
    chain = prompt | llm_json

    response = chain.invoke({
        "topico": state["topico"],
        "context": context_str,
        "iterations": iterations,
        "max_iterations": max_iterations
    })

    try:
        data = parse_llm_json(response.content)
        queries = data.get("consultas", [])
        agent_status(f"{len(queries)} consulta(s) generada(s): {queries}")
    except json.JSONDecodeError:
        queries = [state["topico"] + " marco teorico", state["topico"] + " articulos cientificos"]
        agent_warning("El modelo no devolvió JSON válido; usando consultas de respaldo predefinidas.")

    return {"queries": queries}
