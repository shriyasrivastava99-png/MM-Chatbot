import os
import re
import unicodedata
from typing import Set

ALLOWED_DOCUMENT_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}
ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AUDIO_EXTENSIONS: Set[str] = {".mp3", ".wav", ".m4a", ".ogg"}

ALLOWED_ALL_EXTENSIONS: Set[str] = (
    ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS
)

# Copyrighted / Protected Intellectual Property Characters & Entities Guardrail
PROTECTED_IP_CHARACTERS = {
    # Marvel / Disney
    "spiderman", "spider man", "spider-man", "iron man", "ironman", "captain america",
    "thor", "black panther", "avengers", "deadpool", "wolverine", "thanos",
    "mickey mouse", "donald duck", "elsa", "darth vader", "yoda",
    # DC Comics / Warner
    "batman", "superman", "joker", "harley quinn", "wonder woman", "flash",
    # Nintendo / Gaming
    "mario", "pikachu", "pokemon", "sonic the hedgehog",
    # Other Famous Trademarks
    "shrek", "harry potter", "goku"
}


def check_copyright_ip_guardrail(query: str) -> bool:
    """
    Returns True if the prompt references protected copyrighted characters or IP.
    """
    lower = query.lower()
    # Normalize spaces and punctuation
    cleaned = re.sub(r"[^\w\s]", "", lower)
    for ip in PROTECTED_IP_CHARACTERS:
        ip_clean = re.sub(r"[^\w\s]", "", ip)
        if re.search(rf"\b{re.escape(ip_clean)}\b", cleaned) or ip_clean in cleaned.replace(" ", ""):
            return True
    return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a file name to prevent path traversal, shell injection,
    and invalid characters while retaining its extension.
    """
    # Strip any directory path components
    basename = os.path.basename(filename)
    
    # Normalize unicode characters
    cleaned = unicodedata.normalize("NFKD", basename).encode("ascii", "ignore").decode("ascii")
    
    # Separate name and extension
    name, ext = os.path.splitext(cleaned)
    ext = ext.lower().strip()
    
    # Remove all characters except alphanumeric, hyphen, underscore, and space
    sanitized_name = re.sub(r"[^\w\s-]", "", name).strip()
    # Replace whitespace sequences with an underscore
    sanitized_name = re.sub(r"[-\s]+", "_", sanitized_name)
    
    if not sanitized_name:
        sanitized_name = "uploaded_file"
        
    # Limit length
    sanitized_name = sanitized_name[:100]
    
    return f"{sanitized_name}{ext}"


def is_allowed_file(filename: str, allowed_extensions: Set[str] = ALLOWED_ALL_EXTENSIONS) -> bool:
    """Checks if a file extension is in the set of allowed extensions."""
    _, ext = os.path.splitext(filename)
    return ext.lower() in allowed_extensions


def get_file_type(filename: str) -> str:
    """Classifies a filename into 'document', 'image', 'audio', or 'unknown'."""
    _, ext = os.path.splitext(filename.lower())
    if ext in ALLOWED_DOCUMENT_EXTENSIONS:
        return "document"
    if ext in ALLOWED_IMAGE_EXTENSIONS:
        return "image"
    if ext in ALLOWED_AUDIO_EXTENSIONS:
        return "audio"
    return "unknown"
