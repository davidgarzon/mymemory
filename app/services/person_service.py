import logging
import unicodedata
from sqlalchemy.orm import Session
from typing import List

from app.models import Person

logger = logging.getLogger(__name__)


def normalize_person_name(name: str) -> str:
    """
    Normalize person name for comparison.
    
    - Strip spaces
    - Convert to lowercase
    - Remove accents
    
    Examples:
        "Andrés" -> "andres"
        " Toni " -> "toni"
        "TONI" -> "toni"
    """
    if not name:
        return ""
    
    # Strip spaces
    normalized = name.strip()
    
    # Convert to lowercase
    normalized = normalized.lower()
    
    # Remove accents (NFD normalization + remove combining marks)
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    return normalized


def get_or_create_person(db: Session, raw_name: str) -> Person:
    """
    Get existing person or create new one.
    
    Flow:
    1. Normalize the name
    2. Search for existing person where:
       - normalized display_name matches
       - OR aliases contains the normalized name
    3. If exists: return it
    4. If not exists:
       - Create new Person with:
         - display_name = original name capitalized
         - aliases = [normalized name]
       - Return it
    """
    if not raw_name or not raw_name.strip():
        raise ValueError("Person name cannot be empty")
    
    normalized_name = normalize_person_name(raw_name)
    
    # Search for existing person by normalized display_name or aliases
    # Get all persons and check normalized names
    all_persons = db.query(Person).all()
    
    for person in all_persons:
        # Ensure aliases is initialized
        if person.aliases is None:
            person.aliases = []
        
        # Check if normalized display_name matches
        normalized_display = normalize_person_name(person.display_name)
        if normalized_display == normalized_name:
            add_alias_if_needed(db, person, normalized_name)
            return person
        
        # Check if normalized_name is in aliases
        for alias in person.aliases:
            if normalize_person_name(alias) == normalized_name:
                # Found by alias
                add_alias_if_needed(db, person, normalized_name)
                return person
    
    # Person not found, create new one
    # Capitalize first letter of each word for display_name
    display_name = raw_name.strip()
    # Simple capitalization: first letter uppercase, rest lowercase
    display_name = display_name[0].upper() + display_name[1:].lower() if len(display_name) > 1 else display_name.upper()
    
    person = Person(
        display_name=display_name,
        aliases=[normalized_name]
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    
    logger.info(f"Created new person: {display_name} (normalized: {normalized_name})")
    return person


def add_alias_if_needed(db: Session, person: Person, normalized_name: str) -> None:
    """
    Add normalized name to person's aliases if not already present.
    
    Args:
        db: Database session
        person: Person object
        normalized_name: Normalized name to add as alias
    """
    if person.aliases is None:
        person.aliases = []
    
    # Check if alias already exists (case-insensitive)
    alias_exists = False
    for existing_alias in person.aliases:
        if normalize_person_name(existing_alias) == normalized_name:
            alias_exists = True
            break
    
    if not alias_exists:
        person.aliases.append(normalized_name)
        db.commit()
        db.refresh(person)
        logger.info(f"Added alias '{normalized_name}' to person '{person.display_name}'")
