import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def parse_intent(text: str, use_llm: bool = True) -> Dict:
    """
    Parse natural language text to extract intent and data.
    
    Hybrid approach:
    - First tries deterministic parsing
    - Falls back to LLM for complex cases
    
    Args:
        text: Input text to parse
        use_llm: Whether to use LLM fallback (default: True)
    
    Returns:
        {
            "intent": "create_memory | list_pending | unknown",
            "confidence": 0.0-1.0,
            "data": {
                "content": str | None,  # For single item (deterministic)
                "related_person_name": str | None,  # For single item (deterministic)
                "items": [...]  # For multiple items (LLM)
            }
        }
    """
    if not text or not text.strip():
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "data": {
                "content": None,
                "related_person_name": None
            }
        }
    
    text_lower = text.lower().strip()
    
    # Intent detection
    intent = "unknown"
    confidence = 0.0
    
    # Check for create_memory intent
    create_patterns = [
        r"recuérdame",
        r"recuerdame",
        r"apunta",
        r"apúntame",
        r"guarda",
        r"anota",
        r"añade",
        r"anade"
    ]
    
    for pattern in create_patterns:
        if re.search(pattern, text_lower):
            intent = "create_memory"
            confidence = 0.9
            break
    
    # Check for list_pending intent
    if intent == "unknown":
        list_patterns = [
            r"qué tengo pendiente",
            r"que tengo pendiente",
            r"qué pendiente",
            r"que pendiente",
            r"pendientes",
            r"qué tengo que hacer",
            r"que tengo que hacer"
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, text_lower):
                intent = "list_pending"
                confidence = 0.9
                break
    
    # Extract person name ONLY when explicit person-related patterns are found
    # Patterns that indicate a real person:
    # - "hablar con {persona}"
    # - "cuando hable con {persona}"
    # - "reunión con {persona}"
    # - "llamar a {persona}"
    # - "decirle a {persona}"
    # 
    # Important: Stop at "de" to avoid capturing "Toni de salarios" -> only "Toni"
    related_person_name = None
    
    # Explicit person patterns (must match one of these to extract person)
    # Pattern explanation: 
    # - Match the verb phrase (hablar con, etc.)
    # - Capture person name (one or more words, but stop at "de" or end of phrase)
    # - Use word boundaries to avoid partial matches
    person_patterns = [
        # "hablar con {persona}" or "hablar con {persona} de"
        r'\bhablar\s+con\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?:\s+de\s|$)',
        r'\bhablar\s+con\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)(?:\s+de\s|$)',
        # "cuando hable con {persona}"
        r'\bcuando\s+hable\s+con\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?:\s+de\s|$)',
        r'\bcuando\s+hable\s+con\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)(?:\s+de\s|$)',
        # "reunión con {persona}"
        r'\breunión\s+con\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?:\s+de\s|$)',
        r'\breunión\s+con\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)(?:\s+de\s|$)',
        # "llamar a {persona}"
        r'\bllamar\s+a\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?:\s+de\s|$)',
        r'\bllamar\s+a\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)(?:\s+de\s|$)',
        # "decirle a {persona}"
        r'\bdecirle\s+a\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)(?:\s+de\s|$)',
        r'\bdecirle\s+a\s+([a-záéíóúñ]+(?:\s+[a-záéíóúñ]+)?)(?:\s+de\s|$)',
    ]
    
    for pattern in person_patterns:
        person_match = re.search(pattern, text, re.IGNORECASE)
        if person_match:
            # Extract person name (stop at "de" if present)
            person_name = person_match.group(1)
            # Split by "de" and take only the first part (the name)
            person_name = person_name.split(' de ')[0].split(' del ')[0]
            # Capitalize first letter of each word
            related_person_name = ' '.join(word.capitalize() for word in person_name.split())
            break
    
    # Extract content
    content = None
    if intent == "create_memory":
        # Remove command words and clean up
        content = text
        
        # Remove "recuérdame" / "recuerdame"
        content = re.sub(r'\b(recuérdame|recuerdame)\s*', '', content, flags=re.IGNORECASE)
        
        # Remove "apunta" / "apúntame"
        content = re.sub(r'\b(apunta|apúntame)\s*', '', content, flags=re.IGNORECASE)
        
        # Remove "guarda" / "anota"
        content = re.sub(r'\b(guarda|anota)\s*', '', content, flags=re.IGNORECASE)
        
        # Remove "añade" / "anade"
        content = re.sub(r'\b(añade|anade)\s*', '', content, flags=re.IGNORECASE)
        
        # Remove "esta idea:" / "idea:"
        content = re.sub(r'\b(esta\s+)?idea\s*:\s*', '', content, flags=re.IGNORECASE)
        
        # Remove "hablar" if it's just "hablar con X"
        if related_person_name:
            # Remove "hablar con X"
            content = re.sub(r'\bhablar\s+con\s+' + re.escape(related_person_name), '', content, flags=re.IGNORECASE)
            # Remove "con X" anywhere
            content = re.sub(r'\bcon\s+' + re.escape(related_person_name), '', content, flags=re.IGNORECASE)
            # Remove just the person name if it appears
            content = re.sub(r'\b' + re.escape(related_person_name) + r'\s+', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s+' + re.escape(related_person_name) + r'\b', '', content, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        content = re.sub(r'\s+', ' ', content).strip()
        
        # Remove "de" at the start if present
        content = re.sub(r'^\s*de\s+', '', content, flags=re.IGNORECASE)
        
        # Remove trailing "de" if present
        content = re.sub(r'\s+de\s*$', '', content, flags=re.IGNORECASE)
        
        # If content is empty or too short, use original text
        if not content or len(content) < 3:
            content = text.strip()
    
    # Check if we should delegate to LLM
    should_use_llm = False
    
    if intent == "unknown" and use_llm:
        # Unknown intent -> try LLM
        should_use_llm = True
        logger.info("Intent unknown, delegating to LLM parser")
    elif intent == "create_memory" and use_llm:
        # Check for signals of multiple topics
        multiple_topic_signals = [
            r'\by\s+',  # "y" (and)
            r'\btambién\s+',  # "también" (also)
            r'\bademás\s+',  # "además" (besides)
            r',\s+',  # Commas (lists)
            r'\bidea\s+y\s+',  # "idea y" (idea and)
            r'\bidea\s+también\s+',  # "idea también" (idea also)
        ]
        
        signal_count = sum(1 for pattern in multiple_topic_signals if re.search(pattern, text_lower))
        if signal_count >= 2:
            should_use_llm = True
            logger.info(f"Multiple topic signals detected ({signal_count}), delegating to LLM parser")
    
    # Delegate to LLM if needed
    if should_use_llm:
        try:
            from app.services.llm_parser import parse_with_llm
            llm_result = parse_with_llm(text)
            
            # If LLM succeeded, adapt to expected format
            if llm_result["intent"] != "unknown":
                items = llm_result.get("items", [])
                person = llm_result.get("person")
                
                # Adapt LLM result to expected format
                # Convert items to format expected by routes_inbox
                adapted_items = []
                for item in items:
                    # Map LLM types to our types
                    item_type = item.get("type", "REMINDER").upper()
                    if item_type in ["LIST_ITEM", "TASK"]:
                        # Map LIST_ITEM and TASK to REMINDER for now
                        item_type = "REMINDER"
                    
                    adapted_item = {
                        "content": item.get("content", ""),
                        "type": item_type.lower(),  # Convert to lowercase (reminder, idea)
                        "related_person_name": person,  # Person is at top level in LLM response
                        "list_name": item.get("list_name"),
                    }
                    adapted_items.append(adapted_item)
                
                logger.info(f"LLM parser succeeded: {len(adapted_items)} items, person={person}")
                return {
                    "intent": "create_memory",
                    "confidence": 0.9,
                    "data": {
                        "items": adapted_items
                    }
                }
            else:
                logger.warning("LLM parser returned unknown, falling back to deterministic result")
        except Exception as e:
            logger.error(f"LLM parser failed: {e}, falling back to deterministic result", exc_info=True)
    
    # Return deterministic result
    return {
        "intent": intent,
        "confidence": confidence,
        "data": {
            "content": content,
            "related_person_name": related_person_name
        }
    }
