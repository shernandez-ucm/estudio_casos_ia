# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Evaluation material for the *Inteligencia Artificial* course (Ingeniería Civil Informática, UCM). The core deliverable is `ai_scientist`, a LangChain/LangGraph multi-agent system that researches an AI topic via a bibliographic search API (Semantic Scholar or OpenAlex) and writes an academic presentation from the results. `estudio_casos.tex`/`.pdf` is the assignment brief (with rubric); `presentacion_universitaria.md` and `referencias.md` are example outputs of running the system.

## Commands

```bash
# Setup (Python 3.10+)
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Run the multi-agent pipeline (must run as a module, not a loose script); topic is a required CLI arg
python -m ai_scientist.main "Aplicaciones de la Causalidad en Inteligencia Artificial"
python -m ai_scientist.main "..." --max-iterations 3 --max-results-per-query 5   # optional flags
python -m ai_scientist.main --help

# Compile the assignment brief (requires a LaTeX distribution)
pdflatex estudio_casos.tex
pdflatex estudio_casos.tex   # second pass to resolve cross-references
```

There is no test suite, linter, or build step in this repo.

Running `python -m ai_scientist.main` overwrites `presentacion_universitaria.md` and `referencias.md` in the repo root — check `git status` before/after if those example outputs matter.

## Configuration

`ai_scientist/config.py` reads a `.env` file (gitignored) at import time and **raises immediately** if configuration is invalid, so any node import will fail fast with a bad `.env`.

- `LLM_PROVIDER` — `ollama` (default, local) or `openrouter` (remote API)
- Ollama: `OLLAMA_MODEL` (default `qwen3.5:9b-mlx`); requires `ollama list` to show the model pulled locally
- OpenRouter: requires both `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` or config.py raises `RuntimeError` on import
- `SEARCH_PROVIDER` — `semantic_scholar` (default) or `openalex`; unrecognized values raise `RuntimeError` on import, same as `LLM_PROVIDER`
- OpenAlex: optional `OPENALEX_MAILTO` opts into the "polite pool" (better rate limit)
- Both search providers are unauthenticated (no key needed) and share a low public rate limit — `ai_scientist/nodes/search.py:_get_with_backoff` retries 429s with exponential backoff (starts at `INITIAL_BACKOFF_SECONDS`, doubles each attempt, `MAX_RETRIES` attempts) before giving up on that query

Two LLM instances are exported from `config.py` and used throughout the `nodes/`: `llm` (temperature 0.4, free text — used for writing) and `llm_json` (temperature 0.1, JSON-constrained — used for structured node outputs).

## Architecture

The system is a `LangGraph` `StateGraph` (`ai_scientist/graph.py`) over a single shared `TypedDict` state (`ai_scientist/state.py`, `PresentationState`). Each node lives in its own module under `ai_scientist/nodes/` and both reads and returns a partial state dict that LangGraph merges in.

Graph shape — a research loop followed by a linear finish:

```
plan (generate_queries) → format (format_queries) → search (execute_searches)
                                                            │
                                        check_iterations ───┤
                                        iterations < max ───┴──→ back to plan
                                        iterations >= max ──→ rank → write → END
```

Node responsibilities (`ai_scientist/nodes/`):
1. **query_generation.py** — LLM proposes Spanish search queries from the topic + accumulated context so far (`llm_json`)
2. **query_formatting.py** — LLM translates/simplifies queries into boolean (`term+AND+term`) English keywords for the bibliographic search API (`llm_json`); has a deterministic regex-based fallback if the LLM output isn't valid JSON
3. **search.py** — dispatches each query to the provider selected by `SEARCH_PROVIDER` via `requests` (no LangChain/LLM involved); see "Search providers" below
4. **ranking.py** — LLM ranks all accumulated papers by citations/impact/semantic relevance to the topic (`llm_json`); falls back to a pure citation-count sort if the LLM output is invalid
5. **writing.py** — LLM writes the final presentation body from accumulated context (`llm`), then the node itself (not the LLM) appends the ranking, source-abstracts, and references sections verbatim

### Search providers

`search.py` normalizes both providers to the same shape before the rest of the node touches them, so provider-specific fields never leak past `_search_semantic_scholar`/`_search_openalex`:
- `_SEARCH_PROVIDERS` maps `SEARCH_PROVIDER` to a `(display_name, search_fn)` pair; `execute_searches` looks up the pair once and calls `search_fn(query)` per query
- each `search_fn` returns a list of dicts with the same keys (`title`, `authors`, `year`, `abstract`, `url`, `citation_count`) and already discards results without an abstract — OpenAlex has no plain-text abstract field, so `_reconstruct_openalex_abstract` rebuilds it from the API's inverted-index representation
- `execute_searches` accumulates `context`, `references`, `abstracts`, and `papers` onto the state from that normalized shape, assigns `ref_index`, and increments `iterations`
- adding a third provider means writing one more `_search_*(query) -> list[dict]` function with that same normalized shape and registering it in `_SEARCH_PROVIDERS`

`check_iterations` (in `graph.py`) is the loop's exit condition: it routes back to `plan` while `iterations < max_iterations`, otherwise proceeds to `rank`.

Cross-cutting modules:
- **json_utils.py** — `parse_llm_json` strips Markdown code fences before `json.loads`, since some models wrap JSON output in ` ```json ` blocks even when a JSON response format is requested
- **status.py** — `agent_start`/`agent_status`/`agent_warning` print a consistent `[Agente N · Name] ...` console trace for every node; use these (not bare `print`) when adding to a node's console output
- **prompts.py** — all prompt templates as string constants, one per node, consumed via `ChatPromptTemplate.from_template`

Every LLM-driven node follows the same pattern: try `parse_llm_json` on the response, and if it raises `json.JSONDecodeError`, fall back to a deterministic (non-LLM) result rather than crashing the graph. Preserve this pattern when touching a node.

`referencias.md`/`references` list numbering (`ref_index`) is assigned once in `search.py` and threaded through unchanged to `papers`, `abstracts`, ranking, and the final references section — it is the join key across all of those state lists.

Entry point `ai_scientist/main.py:main()` parses the CLI args (topic + optional iteration/result-count flags) and calls `run()`, which invokes the compiled graph and writes `presentacion_universitaria.md` and `referencias.md` to the repo root.
