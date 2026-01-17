import json
import logging
from typing import Dict, Optional
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client, return None if API key not configured"""
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not configured, LLM parser disabled")
            return None
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


LLM_SYSTEM_PROMPT = """
Eres un parser semántico para una aplicación de memoria personal.

Tu tarea es analizar un mensaje en español y devolver EXCLUSIVAMENTE JSON VÁLIDO,
sin texto adicional, sin markdown y sin explicaciones.

Reglas estrictas:
- NO inventes personas
- Solo devuelve una persona si el texto indica claramente interacción con una persona:
  - "hablar con X"
  - "reunión con X"
  - "llamar a X"
  - "decirle a X"
- Si no hay persona explícita, usa null
- Si hay múltiples temas en el mensaje, divídelos en múltiples items
- Normaliza cada item en una frase clara y autocontenida

Listas:
- Si el usuario dice "añade X" sin especificar lista → list_name = "shopping"
- Si dice "añade a la lista de tareas X" → list_name = "tasks"
- Si dice "añade a la lista Y X" → list_name = Y

Tipos permitidos:
- REMINDER
- IDEA
- LIST_ITEM
- TASK

Formato EXACTO de salida:

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

Si no puedes entender el mensaje, devuelve:

{
  "intent": "unknown",
  "reason": "string"
}
""".strip()


def parse_with_llm(text: str) -> Dict:
    """
    Parse complex natural language text using LLM.

    Returns one of:
    - {
        "intent": "create_memory",
        "person": str | None,
        "items": [...]
      }
    - {
        "intent": "unknown",
        "reason": str
      }
    """
    client = get_openai_client()
    if not client:
        logger.error("LLM parser called but OpenAI client not available")
        return {"intent": "unknown", "reason": "llm_not_available"}

    try:
        logger.info(f"LLM parsing text: '{text[:120]}...'")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": LLM_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)

        # ---- VALIDATION ----

        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object")

        intent = parsed.get("intent")
        if intent not in {"create_memory", "unknown"}:
            raise ValueError("Invalid or missing intent")

        if intent == "unknown":
            return {
                "intent": "unknown",
                "reason": parsed.get("reason", "unknown"),
            }

        items = parsed.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError("Missing or empty items list")

        person = parsed.get("person")
        if person is not None and not isinstance(person, str):
            raise ValueError("Invalid person field")

        validated_items = []

        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Item is not an object")

            item_type = item.get("type")
            if item_type not in {"REMINDER", "IDEA", "LIST_ITEM", "TASK"}:
                raise ValueError(f"Invalid item type: {item_type}")

            content = item.get("content")
            if not content or not isinstance(content, str):
                raise ValueError("Item content missing or invalid")

            list_name = item.get("list_name")

            if item_type in {"LIST_ITEM", "TASK"}:
                if list_name is None:
                    list_name = "shopping" if item_type == "LIST_ITEM" else "tasks"
            else:
                list_name = None

            validated_items.append(
                {
                    "type": item_type,
                    "content": content.strip(),
                    "list_name": list_name,
                }
            )

        logger.info(
            f"LLM parser succeeded: intent={intent}, person={person}, items={len(validated_items)}"
        )

        return {
            "intent": "create_memory",
            "person": person,
            "items": validated_items,
        }

    except Exception as e:
        logger.error(f"LLM parser failed: {e}", exc_info=True)
        return {
            "intent": "unknown",
            "reason": "llm_parse_error",
        }