import json
import re

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_llm_json(content: str) -> dict:
    """Parsea la respuesta JSON de un LLM, tolerando el envoltorio en bloques
    de código Markdown (```json ... ```) que algunos modelos añaden incluso
    con format="json"."""
    cleaned = _CODE_FENCE_RE.sub("", content.strip()).strip()
    return json.loads(cleaned)
