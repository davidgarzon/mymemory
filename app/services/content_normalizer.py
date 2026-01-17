import logging
import unicodedata
import hashlib
import re

logger = logging.getLogger(__name__)

# Stopwords simples en español
STOPWORDS = {
    "hablar", "habla", "hablo", "hablas",
    "recuérdame", "recuerdame", "recordar", "recuerda",
    "apunta", "apúntame", "apuntame",
    "tema", "temas",
    "sobre", "de", "del", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "con", "para", "por", "que", "qué",
    "me", "te", "le", "nos", "os", "les"
}


def normalize_content(text: str) -> str:
    """
    Normalize content text for comparison.
    
    - Convert to lowercase
    - Remove accents
    - Remove punctuation
    - Remove stopwords
    - Reduce spaces
    
    Examples:
        "Hablar con Toni de salarios" -> "salarios"
        "Subidas salariales" -> "subidas salariales"
        "Tema salarios" -> "salarios"
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Remove accents (NFD normalization + remove combining marks)
    normalized = unicodedata.normalize('NFD', normalized)
    normalized = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    # Remove punctuation (keep spaces)
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    
    # Split into words
    words = normalized.split()
    
    # Remove stopwords
    filtered_words = [word for word in words if word not in STOPWORDS]
    
    # Join and reduce spaces
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def content_fingerprint(normalized: str) -> str:
    """
    Generate a stable fingerprint for normalized content.
    
    Uses SHA1 hash for comparison (not for security).
    
    Args:
        normalized: Normalized content string
        
    Returns:
        SHA1 hash hex string
    """
    if not normalized:
        return ""
    
    return hashlib.sha1(normalized.encode('utf-8')).hexdigest()
