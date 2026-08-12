from .graph import presentation_agent


def run(topico: str, max_iterations: int = 2, max_results_per_query: int = 10):
    initial_state = {
        "topico": topico,
        "context": [],
        "references": [],
        "abstracts": [],
        "papers": [],
        "iterations": 0,
        "max_iterations": max_iterations,
        "max_results_per_query": max_results_per_query
    }

    print(f"Investigando y preparando presentación sobre: {topico}...")
    final_state = presentation_agent.invoke(initial_state)

    # Guardar la presentación
    filename = "presentacion_universitaria.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_state["presentation"])

    print(f"\n¡Presentación generada! Guardada en: {filename}")

    # Guardar las referencias en un archivo Markdown independiente
    references = final_state.get("references", [])
    references_filename = "referencias.md"
    with open(references_filename, "w", encoding="utf-8") as f:
        f.write(f"# Referencias: {topico}\n\n")
        f.write("\n".join(references) if references else "No se registraron referencias.")
        f.write("\n")

    print(f"Referencias guardadas en: {references_filename}")

    return final_state


if __name__ == "__main__":
    run(topico="Aplicaciones de la Causalidad en Inteligencia Artificial")
