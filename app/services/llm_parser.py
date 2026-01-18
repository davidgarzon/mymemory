import json
import logging
from typing import Dict, Optional, List
from openai import OpenAI
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client, return None if API key not configured"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, LLM disabled")
            return None
        try:
            _client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    return _client


LLM_SYSTEM_PROMPT = """
Eres un parser semántico para una aplicación de memoria personal.

Devuelve EXCLUSIVAMENTE JSON válido.
NO escribas texto adicional.
NO uses markdown.
NO expliques nada.

REGLAS:
- Analiza el mensaje en español
- Extrae TODOS los items implícitos o explícitos
- Divide listas como "arroz y manzanas" en items separados
- NO inventes personas
- Solo devuelve persona si hay interacción explícita:
  "hablar con X", "reunión con X", "llamar a X", "decirle a X"

LISTAS:
- "añade X" → LIST_ITEM, list_name="shopping"
- "añade a la lista de tareas X" → TASK, list_name="tasks"
- "añade a la lista Y X" → list_name=Y

TIPOS PERMITIDOS:
- REMINDER
- IDEA
- LIST_ITEM
- TASK

FORMATO EXACTO:

{
  "intent": "create_memory" | "unknown",
  "person": string | null,
  "items": [
    {
      "type": "REMINDER" | "IDEA" | "LIST_ITEM" | "TASK",
      "content": string,
      "list_name": string | null
    }
  ]
}

Si no entiendes el mensaje:

{
  "intent": "unknown",
  "person": null,
  "items": []
}
""".strip()


def parse_with_llm(text: str, db: Optional[Session] = None) -> Dict:
    client = get_openai_client()
    if not client:
        logger.error("LLM parser called but OpenAI client not available")
        return {
            "intent": "unknown",
            "person": None,
            "items": []
        }

    try:
        # Get active prompt from database (dynamic)
        system_prompt = LLM_SYSTEM_PROMPT
        if db:
            try:
                from app.services.prompt_service import get_active_prompt
                system_prompt = get_active_prompt(db)
            except Exception as e:
                logger.warning(f"Could not load active prompt from DB: {e}, using default")
        
        logger.info(f"LLM parsing text: '{text[:120]}...'")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not an object")

        intent = parsed.get("intent")
        if intent not in {"create_memory", "unknown"}:
            raise ValueError("Invalid intent")

        person = parsed.get("person")
        if person is not None and not isinstance(person, str):
            person = None

        items = parsed.get("items", [])
        if not isinstance(items, list):
            items = []

        validated_items: List[Dict] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            content = item.get("content")
            list_name = item.get("list_name")

            if item_type not in {"REMINDER", "IDEA", "LIST_ITEM", "TASK"}:
                continue

            if not isinstance(content, str) or not content.strip():
                continue

            if item_type in {"LIST_ITEM", "TASK"}:
                if not list_name:
                    list_name = "shopping" if item_type == "LIST_ITEM" else "tasks"
            else:
                list_name = None

            validated_items.append({
                "type": item_type,
                "content": content.strip(),
                "list_name": list_name,
            })

        return {
            "intent": intent,
            "person": person,
            "items": validated_items,
        }

    except Exception as e:
        logger.error(f"LLM parser error: {e}", exc_info=True)
        return {
            "intent": "unknown",
            "person": None,
            "items": []
        }
