import re
import unicodedata
from datetime import datetime

def normalize_text(text):
    """Normalize Vietnamese text and remove excessive whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text).strip()

def get_now_iso():
    """Returns current ISO timestamp."""
    return datetime.now().isoformat()
