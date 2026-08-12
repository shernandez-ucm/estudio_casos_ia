import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama

load_dotenv()

# Cliente API de Semantic Scholar (ver https://github.com/allenai/s2-folks)
S2_API_KEY = os.getenv("S2_API_KEY")  # opcional: mejora el límite de tasa
# Bulk Search: https://api.semanticscholar.org/api-docs/#tag/Paper-Data/operation/get_graph_paper_bulk_search
S2_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

# Instanciar el modelo local
llm = ChatOllama(model="gemma4:12b-mlx", temperature=0.4)
llm_json = ChatOllama(model="gemma4:12b-mlx", temperature=0.1, format="json")
