import json
import re
from typing import Dict, List
from difflib import get_close_matches


def load_kriol_dictionary(filepath: str) -> Dict[str, str]:
    """
    Load Kriol-to-English dictionary from JSON file.
    Flattens all categories into a single word mapping.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Flatten all categories into one dictionary
    word_map = {}
    for category, words in data.items():
        if category == "comment":
            continue
        if isinstance(words, dict):
            word_map.update(words)
    
    return word_map


def tokenize_kriol(text: str) -> List[str]:
    """
    Tokenize Kriol text into words.
    Handles hyphens in compound words like 'hot-bodi'.
    Preserves apostrophes in contractions like "don't".
    """
    # Keep hyphens and apostrophes in words
    text = text.lower().strip()
    # Replace punctuation except hyphens and apostrophes with spaces
    text = re.sub(r"[^\w\s'\-]", " ", text)
    # Normalize apostrophes to standard straight apostrophe
    text = text.replace("'", "'").replace("'", "'").replace("`", "'")
    # Normalize spaces
    text = re.sub(r"\s+", " ", text)
    return text.split()


def normalize_spelling(word: str, dictionary: Dict[str, str], cutoff: float = 0.85) -> str:
    """
    Normalize spelling variations using fuzzy matching.
    
    Args:
        word: Kriol word (potentially misspelled)
        dictionary: Kriol-to-English mapping
        cutoff: Similarity threshold for fuzzy matching
        
    Returns:
        Normalized Kriol word (or original if no match)
    """
    if word in dictionary:
        return word
    
    # Try fuzzy matching against known Kriol words
    matches = get_close_matches(word, dictionary.keys(), n=1, cutoff=cutoff)
    if matches:
        return matches[0]
    
    return word


def translate_kriol_to_english(text: str, dictionary: Dict[str, str]) -> str:
    """
    Translate Kriol text to English.
    
    Pipeline:
    1. Tokenize the text
    2. Normalize spelling variations
    3. Map Kriol words to English
    4. Reconstruct sentence
    
    Args:
        text: Input text in Kriol
        dictionary: Kriol-to-English word mapping
        
    Returns:
        Translated English text
    """
    tokens = tokenize_kriol(text)
    english_tokens = []
    
    for token in tokens:
        # Normalize spelling
        normalized = normalize_spelling(token, dictionary)
        
        # Translate to English
        if normalized in dictionary:
            english_tokens.append(dictionary[normalized])
        else:
            # Keep unknown words as-is (might be already English)
            english_tokens.append(token)
    
    return " ".join(english_tokens)


def post_process_translation(text: str) -> str:
    """
    Post-process translated text to fix grammar.
    
    - Add articles where needed
    - Fix common patterns
    """
    # Replace "hot body" with "fever"
    text = re.sub(r'\bhot\s+body\b', 'fever', text)
    text = re.sub(r'\bhave\s+pain\b', 'have a pain', text)
    
    # Add article before "headache", "fever", etc.
    text = re.sub(r'\bhave\s+(headache|cough|fever)\b', r'have a \1', text)
    text = re.sub(r'\bhave\s+(diarrhea|vomiting|nausea)\b', r'have \1', text)
    
    return text


# ---------------------------------------------------------------------------
# Whisper post-correction for Kriol
# ---------------------------------------------------------------------------

# Phonetic substitutions: things Whisper commonly mishears when a Kriol
# speaker is recorded. Applied word-by-word BEFORE dictionary lookup.
_WHISPER_PHONETIC: Dict[str, str] = {
    # Kriol yes/no — preserve as-is so option matcher can handle them
    "yuwai":    "yuwai",
    "yuwei":    "yuwai",
    "you why":  "yuwai",
    "you way":  "yuwai",
    "nomu":     "nomu",
    "no more":  "nomu",
    # numbers / time words Whisper writes in English
    "two":      "tu",
    "one":      "wan",
    "three":    "tri",
    "four":     "fo",
    "five":     "faiv",
    "six":      "sikis",
    "seven":    "sebn",
    "eight":    "eit",
    "nine":     "nain",
    "ten":      "ten",
    "day":      "dei",
    "days":     "dei",
    "week":     "wik",
    "weeks":    "wik",
    # phonetic f/v swap (Kriol 'fo'→Whisper 'vo')
    "vo":       "fo",
    "va":       "fa",
    "ve":       "fe",
    "viva":     "fiva",
    "viba":     "fiba",
    # common Whisper mishearings
    "bella":    "beli",
    "bela":     "beli",
    "hatit":    "hati",
    "my":       "mi",
    "me":       "mi",
    "i've":     "mi",
    "i":        "mi",
    "have":     "garr",
    "got":      "gat",
    "and":      "en",
    "the":      "",
    "for":      "fo",
    "been":     "bin",
    "hurting":  "hati",
    "hurt":     "hati",
    "pain":     "pen",
    "fever":    "fiva",
    "stomach":  "beli",
    "belly":    "beli",
}


def _split_runon(word: str, dictionary: Dict[str, str], cutoff: float = 0.82) -> List[str]:
    """
    Try to split a run-together word (e.g. 'garafiva') into two valid
    Kriol dictionary tokens. Tries every split point from position 2 onward.
    Returns a list of one or two tokens.
    """
    if len(word) < 4 or word in dictionary:
        return [word]
    keys = list(dictionary.keys())
    for i in range(2, len(word) - 1):
        left  = word[:i]
        right = word[i:]
        left_match  = left  if left  in dictionary else (get_close_matches(left,  keys, n=1, cutoff=cutoff) or [None])[0]
        right_match = right if right in dictionary else (get_close_matches(right, keys, n=1, cutoff=cutoff) or [None])[0]
        if left_match and right_match:
            return [left_match, right_match]
    return [word]


def correct_kriol_transcription(raw_text: str, dictionary: Dict[str, str]) -> str:
    """
    Clean up a raw Whisper transcription of Kriol speech.

    Pipeline
    --------
    1. Lowercase + basic normalisation
    2. Split run-together words using the dictionary
    3. Apply phonetic substitution table (_WHISPER_PHONETIC)
    4. Strip common Whisper trailing artefacts (-t, -d) on known Kriol roots
    5. Fuzzy-match each token against the dictionary
    6. Reconstruct and return the cleaned text
    """
    if not raw_text:
        return raw_text

    text = raw_text.lower().strip()
    # remove punctuation except hyphens/apostrophes
    text = re.sub(r"[^\w\s'\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Step 0: multi-word phrase substitutions BEFORE tokenising
    _MULTIWORD = [
        ("you why",  "yuwai"),
        ("you way",  "yuwai"),
        ("no more",  "nomu"),
        ("not can",  "no ken"),
    ]
    for phrase, replacement in _MULTIWORD:
        text = re.sub(r"\b" + re.escape(phrase) + r"\b", replacement, text)

    tokens: List[str] = []
    for token in text.split():
        # Step 1: try to split run-on words first
        parts = _split_runon(token, dictionary)
        tokens.extend(parts)

    cleaned: List[str] = []
    for token in tokens:
        if not token:
            continue

        # Step 2: phonetic substitution
        sub = _WHISPER_PHONETIC.get(token, token)
        if sub == "":        # dropped stop-word (e.g. "the")
            continue
        token = sub

        # Step 3: strip common trailing artefacts Whisper adds
        # e.g. hatit→hati, bint→bin, wast→was
        stripped = token
        if token not in dictionary:
            for suffix in ("it", "t", "d", "ed"):
                candidate = token[: -len(suffix)] if token.endswith(suffix) and len(token) - len(suffix) >= 2 else None
                if candidate and (candidate in dictionary or get_close_matches(candidate, dictionary.keys(), n=1, cutoff=0.88)):
                    stripped = candidate
                    break
        token = stripped

        # Step 4: fuzzy-match to nearest dictionary key
        if token not in dictionary:
            matches = get_close_matches(token, dictionary.keys(), n=1, cutoff=0.80)
            if matches:
                token = matches[0]

        cleaned.append(token)

    return " ".join(cleaned)
