import json

from langchain_core.prompts import ChatPromptTemplate

from ..config import llm_json
from ..json_utils import parse_llm_json
from ..prompts import RANK_AND_SUMMARIZE_PROMPT
from ..state import PresentationState
from ..status import agent_start, agent_status, agent_warning


def rank_and_summarize(state: PresentationState):
    """Nodo: lee TODOS los artículos recopilados y los rankea según citas, impacto
    y relevancia semántica con el tópico, generando un resumen del ranking en español."""
    papers = state.get("papers", [])
    agent_start(
        4, "Ranking y Resumen",
        f"Rankeando {len(papers)} artículo(s) recopilado(s) según citas, impacto y relevancia semántica...",
    )

    if not papers:
        agent_status("No se recopilaron artículos; se omite el ranking.")
        return {"ranked_summary": "No se recopilaron artículos para rankear."}

    papers_str = "\n\n".join(
        f"[Documento Científico #{p['ref_index']}] {p['title']} ({p['year']}) - Citas: {p['citation_count']}\n"
        f"Resumen: {p['abstract']}"
        for p in papers
    )

    prompt = ChatPromptTemplate.from_template(RANK_AND_SUMMARIZE_PROMPT)
    chain = prompt | llm_json

    response = chain.invoke({
        "topico": state["topico"],
        "papers": papers_str
    })

    ranking = []
    try:
        data = parse_llm_json(response.content)
        ranking = [r for r in data.get("ranking", []) if r.get("ref_index") is not None]
    except json.JSONDecodeError:
        ranking = []

    # Respaldo determinista si el LLM falla: ordenar solo por número de citas
    if not ranking:
        agent_warning("El modelo no devolvió JSON válido; usando ranking de respaldo ordenado solo por citas.")
        ranking = [
            {
                "ref_index": p["ref_index"],
                "puntaje_global": "N/D",
                "justificacion": "Ranking de respaldo generado solo a partir del número de citas "
                                 "(el modelo no devolvió un JSON válido).",
            }
            for p in sorted(papers, key=lambda p: p["citation_count"], reverse=True)
        ]

    papers_by_index = {p["ref_index"]: p for p in papers}
    lines = []
    for posicion, item in enumerate(ranking, start=1):
        paper = papers_by_index.get(item.get("ref_index"))
        if not paper:
            continue
        puntaje = item.get("puntaje_global", "N/D")
        justificacion = item.get("justificacion", "Sin justificación.")
        lines.append(
            f"{posicion}. [{paper['ref_index']}] **{paper['title']}** ({paper['year']}) "
            f"— Citas: {paper['citation_count']}, Puntaje: {puntaje}\n   {justificacion}"
        )

    ranked_summary = "\n\n".join(lines) if lines else "No fue posible generar el ranking de artículos."
    agent_status(f"Ranking generado para {len(lines)} de {len(papers)} artículo(s).")

    return {"ranked_summary": ranked_summary}
