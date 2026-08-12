import json

from langchain_core.prompts import ChatPromptTemplate

from ..config import llm_json
from ..prompts import QUERY_GENERATION_PROMPT
from ..state import PresentationState


def generate_queries(state: PresentationState):
    """Nodo 1: Genera consultas enfocadas en el temario universitario."""
    context_str = "\n".join(state.get("context", [])) if state.get("context") else "Ninguno todavía."

    prompt = ChatPromptTemplate.from_template(QUERY_GENERATION_PROMPT)
    chain = prompt | llm_json

    response = chain.invoke({
        "topico": state["topico"],
        "context": context_str,
        "iterations": state.get("iterations", 0),
        "max_iterations": state["max_iterations"]
    })

    try:
        data = json.loads(response.content)
        queries = data.get("consultas", [])
    except json.JSONDecodeError:
        queries = [state["topico"] + " marco teorico", state["topico"] + " articulos cientificos"]

    return {"queries": queries}
