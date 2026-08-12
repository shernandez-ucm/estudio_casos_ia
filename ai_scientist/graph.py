from langgraph.graph import StateGraph, END

from .nodes import (
    execute_searches,
    format_queries,
    generate_queries,
    rank_and_summarize,
    write_presentation,
)
from .state import PresentationState


def check_iterations(state: PresentationState):
    if state["iterations"] >= state["max_iterations"]:
        return "rank_and_summarize"
    return "generate_queries"


def build_graph():
    workflow = StateGraph(PresentationState)

    workflow.add_node("plan", generate_queries)
    workflow.add_node("format", format_queries)
    workflow.add_node("search", execute_searches)
    workflow.add_node("rank", rank_and_summarize)
    workflow.add_node("write", write_presentation)

    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "format")
    workflow.add_edge("format", "search")

    workflow.add_conditional_edges(
        "search",
        check_iterations,
        {
            "generate_queries": "plan",
            "rank_and_summarize": "rank"
        }
    )

    workflow.add_edge("rank", "write")
    workflow.add_edge("write", END)

    return workflow.compile()


presentation_agent = build_graph()
