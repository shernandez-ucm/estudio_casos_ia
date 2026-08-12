import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

load_dotenv()

# Proveedor de búsqueda bibliográfica: "semantic_scholar" (por defecto) u "openalex"
SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "semantic_scholar").lower()
if SEARCH_PROVIDER not in ("semantic_scholar", "openalex"):
    raise RuntimeError(f"SEARCH_PROVIDER '{SEARCH_PROVIDER}' no reconocido; use 'semantic_scholar' u 'openalex'.")

# Cliente API de Semantic Scholar, sin autenticación (ver https://github.com/allenai/s2-folks)
# Search API (relevance search): https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_get_paper_search
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

# Cliente API de OpenAlex, sin autenticación (ver https://help.openalex.org/quickstart/)
OPENALEX_SEARCH_URL = "https://api.openalex.org/works"
# Correo opcional que habilita el "polite pool" de OpenAlex (mejor límite de tasa y confiabilidad)
OPENALEX_MAILTO = os.getenv("OPENALEX_MAILTO")

# Proveedor de LLM: "ollama" (por defecto, local) u "openrouter" (API remota vía OpenRouter.ai)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

if LLM_PROVIDER == "openrouter":
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
    if not OPENROUTER_API_KEY:
        raise RuntimeError("LLM_PROVIDER=openrouter requiere definir OPENROUTER_API_KEY en el archivo .env")
    if not OPENROUTER_MODEL:
        raise RuntimeError(
            "LLM_PROVIDER=openrouter requiere definir OPENROUTER_MODEL en el archivo .env "
            "(p. ej. OPENROUTER_MODEL=openai/gpt-4o-mini; ver https://openrouter.ai/models)"
        )

    llm = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0.4,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    llm_json = ChatOpenAI(
        model=OPENROUTER_MODEL,
        temperature=0.1,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        model_kwargs={"response_format": {"type": "json_object"}},
    )
elif LLM_PROVIDER == "ollama":
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b-mlx")
    llm = ChatOllama(model=OLLAMA_MODEL, temperature=0.4)
    llm_json = ChatOllama(model=OLLAMA_MODEL, temperature=0.1, format="json")
else:
    raise RuntimeError(f"LLM_PROVIDER '{LLM_PROVIDER}' no reconocido; use 'ollama' u 'openrouter'.")
