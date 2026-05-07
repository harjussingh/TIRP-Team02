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
