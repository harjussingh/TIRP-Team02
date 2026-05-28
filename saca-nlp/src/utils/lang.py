import json
import os
import re
from typing import Dict


def _root_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_kriol_dictionary() -> Dict:
    path = os.path.join(_root_dir(), "data", "dictionaries", "kriol_dictionary.json")
    return _load_json(path)


def _build_english_to_kriol_map(dictionary: Dict) -> Dict[str, str]:
    """
    Build a simple English -> Kriol lookup from the uploaded Kriol -> English dictionary.
    This is used only as a fallback for UI strings.
    """
    english_to_kriol = {}

    sections = [
        "pronouns",
        "verbs",
        "negation",
        "conjunctions",
        "interrogatives",
        "prepositions",
        "medical_symptoms",
        "intensifiers",
        "time",
        "adjectives",
        "common_words",
    ]

    for section in sections:
        items = dictionary.get(section, {})
        for kriol_word, english_word in items.items():
            if not english_word:
                continue

            english_key = str(english_word).strip().lower()
            kriol_value = str(kriol_word).strip()

            if english_key and english_key not in english_to_kriol:
                english_to_kriol[english_key] = kriol_value

    return english_to_kriol


def _word_translate_to_kriol(text: str, english_to_kriol: Dict[str, str]) -> str:
    """
    Safe fallback:
    - word-by-word translation if mapping exists
    - otherwise keep English word as-is
    """
    if not text:
        return text

    tokens = re.findall(r"[A-Za-z0-9_'-]+|[^A-Za-z0-9_'-]+", text)
    translated = []

    for token in tokens:
        lower = token.lower()
        if re.fullmatch(r"[A-Za-z0-9_'-]+", token):
            translated.append(english_to_kriol.get(lower, token))
        else:
            translated.append(token)

    return "".join(translated).strip()


def load_strings(language_code: str) -> Dict[str, str]:
    """
    UI language loading logic:
    1. Always load English base strings
    2. If Kriol is selected:
       - load exact phrase translations from assets/lang/kriol.json
       - for missing keys, use dictionary-based word fallback
    """
    root = _root_dir()

    en_path = os.path.join(root, "assets", "lang", "en.json")
    kriol_path = os.path.join(root, "assets", "lang", "kriol.json")

    english_strings = _load_json(en_path)

    if language_code != "kriol":
        return english_strings

    kriol_strings = _load_json(kriol_path)
    kriol_dictionary = _load_kriol_dictionary()
    english_to_kriol = _build_english_to_kriol_map(kriol_dictionary)

    merged = {}
    for key, english_value in english_strings.items():
        exact_value = ""
        if kriol_strings:
            exact_value = str(kriol_strings.get(key, "")).strip()

        if exact_value:
            merged[key] = exact_value
        else:
            merged[key] = _word_translate_to_kriol(english_value, english_to_kriol)

    return merged