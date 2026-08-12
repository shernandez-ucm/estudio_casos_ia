# Estudio de Caso IA — Sistemas Multi-Agente

Material de evaluación para la actividad curricular *Inteligencia Artificial* (Ingeniería Civil Informática, UCM): un estudio de caso sobre sistemas multi-agente que utiliza **`ai_scientist`**, un sistema multi-agente basado en LangChain/LangGraph, para generar presentaciones académicas sobre temas de IA.

## Contenido del repositorio

```
.
├── ai_scientist/              # Paquete Python: sistema multi-agente
│   ├── state.py                # Estado compartido del grafo (PresentationState)
│   ├── config.py                # Configuración de LLMs (Ollama u OpenRouter) y Semantic Scholar
│   ├── prompts.py                # Plantillas de prompt de cada agente
│   ├── json_utils.py              # Parseo tolerante de JSON devuelto por el LLM
│   ├── status.py                   # Mensajes de estado/tarea de cada agente en consola
│   ├── graph.py                     # Ensamblaje del grafo con LangGraph
│   ├── main.py                       # Punto de entrada
│   └── nodes/                      # Un agente por módulo
│       ├── query_generation.py       # Agente 1: genera consultas de búsqueda
│       ├── query_formatting.py       # Agente 2: formatea consultas para Semantic Scholar
│       ├── search.py                 # Agente 3: busca en Semantic Scholar
│       ├── ranking.py                # Agente 4: rankea artículos recopilados
│       └── writing.py                # Agente 5: redacta la presentación final
├── estudio_casos.tex          # Enunciado del estudio de caso (rúbrica incluida)
├── estudio_casos.pdf          # Enunciado compilado
├── requirements.txt           # Dependencias Python
└── referencias.md / presentacion_universitaria.md   # Salida de ejemplo de ai_scientist
```

## Requisitos

- Python 3.10+
- Un proveedor de LLM configurado (ver [Configuración](#configuración) más abajo): [Ollama](https://ollama.com) corriendo localmente (por defecto), o una API key de [OpenRouter](https://openrouter.ai)

Las búsquedas se realizan sin autenticación contra un proveedor bibliográfico público ([Semantic Scholar](https://www.semanticscholar.org/product/api) u [OpenAlex](https://help.openalex.org/quickstart/)), por lo que no se requiere ninguna API key para esa parte. El tráfico no autenticado comparte un límite de tasa más bajo que el de las solicitudes autenticadas, así que si ejecutas el sistema con frecuencia podrías toparte con errores 429; `ai_scientist/nodes/search.py` reintenta automáticamente con backoff exponencial ante ese error.

## Instalación

```bash
# 1. Clonar el repositorio
git clone <URL-de-este-repositorio>
cd estudio_casos_ia

# 2. Crear y activar un entorno virtual
python3 -m venv env
source env/bin/activate      # En Windows: env\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## Configuración

`ai_scientist` soporta dos proveedores de LLM, seleccionados con la variable de entorno `LLM_PROVIDER` (por defecto `ollama`). Colócala, junto con las demás variables, en un archivo `.env` en la raíz del proyecto (no se sube al repositorio).

**Opción A — Ollama (local, por defecto)**

```bash
ollama list   # confirma que el modelo esté descargado
```

```
# .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3.5:9b-mlx   # opcional; por defecto usa qwen3.5:9b-mlx
```

**Opción B — OpenRouter (API remota)**

```
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=tu_api_key_aqui
OPENROUTER_MODEL=openai/gpt-4o-mini   # cualquier modelo listado en https://openrouter.ai/models
```

Si `LLM_PROVIDER=openrouter` y falta `OPENROUTER_API_KEY` u `OPENROUTER_MODEL`, `ai_scientist/config.py` falla de inmediato con un error explicativo al importar el paquete.

`ai_scientist` también soporta dos proveedores de búsqueda bibliográfica, seleccionados con la variable de entorno `SEARCH_PROVIDER` (por defecto `semantic_scholar`).

**Opción A — Semantic Scholar (por defecto)**

```
# .env
SEARCH_PROVIDER=semantic_scholar
```

**Opción B — OpenAlex**

```
# .env
SEARCH_PROVIDER=openalex
OPENALEX_MAILTO=tu_correo@ejemplo.com   # opcional; habilita el "polite pool" (mejor límite de tasa)
```

## Uso

Ejecuta el sistema multi-agente desde la raíz del proyecto (como módulo, no como script suelto), pasando el tópico a investigar como argumento:

```bash
python -m ai_scientist.main "Aplicaciones de la Causalidad en Inteligencia Artificial"

# Opcionalmente, ajusta la cantidad de iteraciones de búsqueda y resultados por consulta
python -m ai_scientist.main "Aplicaciones de la Causalidad en Inteligencia Artificial" --max-iterations 3 --max-results-per-query 5
```

Esto genera dos archivos en la raíz del proyecto:

- `presentacion_universitaria.md`: la presentación en formato Markdown.
- `referencias.md`: las referencias bibliográficas recopiladas.

## Compilar el enunciado (LaTeX)

```bash
pdflatex estudio_casos.tex
pdflatex estudio_casos.tex   # segunda pasada para resolver referencias cruzadas
```

Requiere una distribución LaTeX (p. ej. [TeX Live](https://www.tug.org/texlive/) o [MacTeX](https://www.tug.org/mactex/)).

## Licencia

Material académico de uso interno para la actividad curricular *Inteligencia Artificial* de la Universidad Católica del Maule.
