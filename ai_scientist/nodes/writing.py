from langchain_core.prompts import ChatPromptTemplate

from ..config import llm
from ..prompts import PRESENTATION_WRITING_PROMPT
from ..state import PresentationState


def write_presentation(state: PresentationState):
    """Nodo 4: Redacta la presentación siguiendo el esquema estricto e incorpora las referencias."""
    context_str = "\n\n".join(state["context"])

    prompt = ChatPromptTemplate.from_template(PRESENTATION_WRITING_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        "topico": state["topico"],
        "context": context_str
    })

    # Añadir automáticamente las diapositivas de Resumen de Fuentes y Referencias
    abstracts = state.get("abstracts", [])
    abstracts_str = "\n\n".join(abstracts) if abstracts else "No se registraron resúmenes."

    references = state.get("references", [])
    references_str = "\n".join(references) if references else "No se registraron referencias."

    ranked_summary = state.get("ranked_summary") or "No se generó un ranking de artículos."

    presentation = (
        f"{response.content}\n\n"
        f"---\n\n"
        f"# Ranking de Artículos Científicos (citas, impacto y relevancia semántica)\n\n"
        f"{ranked_summary}\n\n"
        f"---\n\n"
        f"# Resumen de las Fuentes\n\n"
        f"{abstracts_str}\n\n"
        f"---\n\n"
        f"# Referencias\n\n"
        f"{references_str}\n"
    )

    return {"presentation": presentation}
