# Estudio de Caso IA — Sistemas Multi-Agente

Material de evaluación para la actividad curricular *Inteligencia Artificial* (Ingeniería Civil Informática, UCM): un estudio de caso sobre sistemas multi-agente que utiliza **`ai_scientist`**, un sistema multi-agente basado en LangChain/LangGraph, para generar presentaciones académicas sobre temas de IA.

## Contenido del repositorio

```
.
├── ai_scientist/              # Paquete Python: sistema multi-agente
│   ├── state.py                # Estado compartido del grafo (PresentationState)
│   ├── config.py                # Configuración de LLMs (Ollama) y Semantic Scholar
│   ├── prompts.py                # Plantillas de prompt de cada agente
│   ├── graph.py                  # Ensamblaje del grafo con LangGraph
│   ├── main.py                    # Punto de entrada
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
- [Ollama](https://ollama.com) corriendo localmente, con un modelo de chat descargado (p. ej. `ollama pull gemma4:12b-mlx` o el modelo que configures en `ai_scientist/config.py`)
- (Opcional pero recomendado) una API key de [Semantic Scholar](https://www.semanticscholar.org/product/api) para evitar límites de tasa en las búsquedas

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

Crea un archivo `.env` en la raíz del proyecto (no se sube al repositorio) con tu API key de Semantic Scholar:

```
S2_API_KEY=tu_api_key_aqui
```

Verifica que Ollama esté corriendo y que el modelo configurado en `ai_scientist/config.py` esté descargado:

```bash
ollama list
```

## Uso

Ejecuta el sistema multi-agente desde la raíz del proyecto (como módulo, no como script suelto):

```bash
python -m ai_scientist.main
```

Esto genera dos archivos en la raíz del proyecto:

- `presentacion_universitaria.md`: la presentación en formato Markdown.
- `referencias.md`: las referencias bibliográficas recopiladas.

Para investigar un tópico distinto, edita el argumento de `run()` en `ai_scientist/main.py`.

## Compilar el enunciado (LaTeX)

```bash
pdflatex estudio_casos.tex
pdflatex estudio_casos.tex   # segunda pasada para resolver referencias cruzadas
```

Requiere una distribución LaTeX (p. ej. [TeX Live](https://www.tug.org/texlive/) o [MacTeX](https://www.tug.org/mactex/)).

## Licencia

Material académico de uso interno para la actividad curricular *Inteligencia Artificial* de la Universidad Católica del Maule.
