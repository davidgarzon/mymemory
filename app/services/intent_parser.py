import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def parse_intent(text: str) -> Dict:
    """
    Parse natural language text to extract intent and data.
    
    Returns:
        {
            "intent": "create_memory | list_pending | unknown",
            "confidence": 0.0-1.0,
            "data": {
                "content": str | None,
                "related_person_name": str | None
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
        r"anota"
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
    
    # Extract person name (simple pattern: "con <Nombre>")
    related_person_name = None
    person_match = re.search(r'\bcon\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)', text)
    if not person_match:
        # Try lowercase too
        person_match = re.search(r'\bcon\s+([a-záéíóúñ]+)', text_lower)
        if person_match:
            # Capitalize first letter
            related_person_name = person_match.group(1).capitalize()
    else:
        related_person_name = person_match.group(1)
    
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
    
    return {
        "intent": intent,
        "confidence": confidence,
        "data": {
            "content": content,
            "related_person_name": related_person_name
        }
    }
