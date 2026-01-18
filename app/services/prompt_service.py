"""
Prompt service for managing dynamic LLM prompts.

Provides functions to get the active prompt from database blocks
and fallback to default if no blocks exist.
"""
import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import PromptBlock

logger = logging.getLogger(__name__)

# Default prompt (fallback if no blocks in DB)
DEFAULT_PROMPT = """Eres un parser semántico para una aplicación de memoria personal.

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


def get_active_prompt(db: Session) -> str:
    """
    Get the active prompt by concatenating enabled blocks ordered by order.
    
    If no blocks exist or none are enabled, returns DEFAULT_PROMPT.
    
    Args:
        db: Database session
        
    Returns:
        Complete prompt string
    """
    try:
        # Get enabled blocks ordered by order
        blocks = db.query(PromptBlock).filter(
            PromptBlock.enabled == True
        ).order_by(PromptBlock.order.asc()).all()
        
        if not blocks:
            logger.info("No prompt blocks found, using default prompt")
            return DEFAULT_PROMPT
        
        # Concatenate blocks with double newline separator
        prompt_parts = [block.content.strip() for block in blocks if block.content.strip()]
        
        if not prompt_parts:
            logger.warning("All prompt blocks are empty, using default prompt")
            return DEFAULT_PROMPT
        
        active_prompt = "\n\n".join(prompt_parts)
        logger.debug(f"Using active prompt from {len(blocks)} blocks")
        return active_prompt
        
    except Exception as e:
        logger.error(f"Error getting active prompt: {e}, using default", exc_info=True)
        return DEFAULT_PROMPT


def reset_to_default_prompt(db: Session) -> None:
    """
    Reset prompt blocks to default structure.
    
    Creates default blocks or updates existing ones.
    This is a helper for initialization/testing.
    
    Args:
        db: Database session
    """
    default_blocks = [
        {
            "name": "INTENT_RULES",
            "content": "Eres un parser semántico para una aplicación de memoria personal.\n\nDevuelve EXCLUSIVAMENTE JSON válido.\nNO escribas texto adicional.\nNO uses markdown.\nNO explicas nada.",
            "order": 1,
        },
        {
            "name": "REGLAS",
            "content": "REGLAS:\n- Analiza el mensaje en español\n- Extrae TODOS los items implícitos o explícitos\n- Divide listas como \"arroz y manzanas\" en items separados\n- NO inventes personas\n- Solo devuelve persona si hay interacción explícita:\n  \"hablar con X\", \"reunión con X\", \"llamar a X\", \"decirle a X\"",
            "order": 2,
        },
        {
            "name": "LIST_RULES",
            "content": "LISTAS:\n- \"añade X\" → LIST_ITEM, list_name=\"shopping\"\n- \"añade a la lista de tareas X\" → TASK, list_name=\"tasks\"\n- \"añade a la lista Y X\" → list_name=Y",
            "order": 3,
        },
        {
            "name": "TIPOS",
            "content": "TIPOS PERMITIDOS:\n- REMINDER\n- IDEA\n- LIST_ITEM\n- TASK",
            "order": 4,
        },
        {
            "name": "FORMATO",
            "content": "FORMATO EXACTO:\n\n{\n  \"intent\": \"create_memory\" | \"unknown\",\n  \"person\": string | null,\n  \"items\": [\n    {\n      \"type\": \"REMINDER\" | \"IDEA\" | \"LIST_ITEM\" | \"TASK\",\n      \"content\": string,\n      \"list_name\": string | null\n    }\n  ]\n}\n\nSi no entiendes el mensaje:\n\n{\n  \"intent\": \"unknown\",\n  \"person\": null,\n  \"items\": []\n}",
            "order": 5,
        },
    ]
    
    try:
        for block_data in default_blocks:
            existing = db.query(PromptBlock).filter(PromptBlock.name == block_data["name"]).first()
            if existing:
                existing.content = block_data["content"]
                existing.order = block_data["order"]
                existing.enabled = True
            else:
                new_block = PromptBlock(
                    name=block_data["name"],
                    content=block_data["content"],
                    order=block_data["order"],
                    enabled=True,
                )
                db.add(new_block)
        
        db.commit()
        logger.info("Reset prompt blocks to default structure")
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting prompt blocks: {e}", exc_info=True)
        raise
