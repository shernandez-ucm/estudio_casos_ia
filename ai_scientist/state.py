from typing import TypedDict, List


class PresentationState(TypedDict):
    topico: str
    queries: List[str]
    context: List[str]
    references: List[str]
    abstracts: List[str]
    papers: List[dict]
    ranked_summary: str
    presentation: str
    iterations: int
    max_iterations: int
    max_results_per_query: int
