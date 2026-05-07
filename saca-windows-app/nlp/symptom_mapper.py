import json
import re
from pathlib import Path

# Intensifier words that can appear inside synonym phrases and should be
# stripped before matching (e.g. "throat is very sore" → "throat is sore")
INTENSIFIERS = {"very", "really", "quite", "extremely", "severely", "badly",
                "a bit", "a little", "slightly", "so", "too", "bigwan",
                "bigfala", "tumas", "prapfala", "jidan", "rili", "lil", "lilbit"}


def load_synonyms(filepath: str = "data/synonyms.json") -> dict:
    """Load synonym mappings from JSON. Skips section-header sentinel keys."""
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("____")}


def _strip_intensifiers(text: str) -> str:
    """Remove intensifier words from text to improve phrase matching."""
    for word in INTENSIFIERS:
        # Only strip standalone intensifier words (not inside other words)
        text = re.sub(r'\b' + re.escape(word) + r'\b', '', text)
    # Normalize spaces left behind
    return re.sub(r'\s+', ' ', text).strip()


def map_synonyms(text: str, synonyms: dict) -> str:
    """
    Replace known synonym phrases with canonical symptom names.
    Uses word-boundary regex to avoid partial-word replacements.
    Strips intensifiers before matching so 'throat is very sore'
    maps to 'sore throat' just as 'throat is sore' does.
    Longer phrases are replaced first to avoid partial overlaps.
    """
    sorted_synonyms = sorted(synonyms.items(), key=lambda x: len(x[0]), reverse=True)

    # First pass: match on intensifier-stripped text, apply to original
    stripped = _strip_intensifiers(text)

    mapped_text = stripped
    for phrase, canonical in sorted_synonyms:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        mapped_text = re.sub(pattern, canonical, mapped_text)

    return mapped_text