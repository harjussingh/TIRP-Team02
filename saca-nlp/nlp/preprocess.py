import re
from difflib import get_close_matches
from typing import List


CONTRACTIONS = {
    "i've": "i have",
    "ive": "i have",
    "i'm": "i am",
    "im": "i am",
    "don't": "do not",
    "dont": "do not",
    "doesn't": "does not",
    "doesnt": "does not",
    "didn't": "did not",
    "didnt": "did not",
    "can't": "cannot",
    "cant": "cannot",
    "won't": "will not",
    "wont": "will not",
    "isn't": "is not",
    "isnt": "is not",
    "aren't": "are not",
    "arent": "are not",
    "wasn't": "was not",
    "wasnt": "was not",
    "weren't": "were not",
    "werent": "were not",
    "haven't": "have not",
    "havent": "have not",
    "hasn't": "has not",
    "hasnt": "has not",
    "hadn't": "had not",
    "hadnt": "had not",
    "couldn't": "could not",
    "couldnt": "could not",
    "shouldn't": "should not",
    "shouldnt": "should not",
    "wouldn't": "would not",
    "wouldnt": "would not"
}


def expand_contractions(text: str) -> str:
    """Expand contractions (with or without apostrophes) - case-insensitive."""
    # Normalize apostrophes: replace curly quotes with straight apostrophes
    text = text.replace("'", "'").replace("'", "'").replace("`", "'")
    text_lower = text.lower()
    # Sort by length (descending) to handle longer contractions first
    for short, full in sorted(CONTRACTIONS.items(), key=lambda x: len(x[0]), reverse=True):
        text_lower = text_lower.replace(short, full)
    return text_lower


def correct_spelling(text: str, known_words: List[str], cutoff: float = 0.8) -> str:
    """
    Correct misspelled words using fuzzy matching against known medical terms.
    Short words (< 4 chars) are skipped to avoid corrupting common English
    function words like 'am', 'in', 'a', 'my', 'is', etc.
    
    Args:
        text: Input text with potential misspellings
        known_words: List of correctly spelled medical terms
        cutoff: Similarity threshold (0.0-1.0), default 0.8
        
    Returns:
        Text with corrected spellings
    """
    words = text.split()
    corrected_words = []
    
    for word in words:
        # Skip short words to avoid corrupting common English words
        if len(word) < 4:
            corrected_words.append(word)
            continue
        # Check if word exists in known words
        if word in known_words:
            corrected_words.append(word)
        else:
            # Try to find a close match
            matches = get_close_matches(word, known_words, n=1, cutoff=cutoff)
            if matches:
                corrected_words.append(matches[0])
            else:
                # Keep original if no good match found
                corrected_words.append(word)
    
    return " ".join(corrected_words)


def clean_text(text: str, known_words: List[str] = None) -> str:
    """
    Basic text cleaning:
    - expand contractions (also handles lowercasing)
    - remove punctuation except spaces
    - normalize spaces
    - correct spelling (if known_words provided)
    """
    text = text.strip()
    text = expand_contractions(text)  # This also lowercases

    # Keep letters, numbers, and spaces only
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize repeated spaces
    text = re.sub(r"\s+", " ", text).strip()
    
    # Spell correction
    if known_words:
        text = correct_spelling(text, known_words)
    
    return text