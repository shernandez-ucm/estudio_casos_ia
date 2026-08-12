def agent_start(number: int, name: str, task: str) -> None:
    """Anuncia qué agente está corriendo y qué tarea va a realizar."""
    print(f"\n[Agente {number} · {name}] {task}")


def agent_status(message: str) -> None:
    """Informa el resultado o estado alcanzado por el agente en curso."""
    print(f"   -> {message}")


def agent_warning(message: str) -> None:
    """Advierte al usuario que el agente usó una ruta de respaldo (p. ej. el LLM no devolvió JSON válido)."""
    print(f"   ! {message}")
