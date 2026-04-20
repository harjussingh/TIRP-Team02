import json
import os
import re
from typing import Dict, List

from src.services.question_tree import select_followup_questions, get_red_flag_questions

try:
    from src.integrations.team_nlp import process_user_input as teammate_nlp
except Exception:
    teammate_nlp = None


SYMPTOM_MAP = {
    "fever": [
        "fever", "fiba", "fiva", "fiwa", "biba",
        "hot body", "hotbodi", "hot-bodi", "very sick"
    ],
    "cough": [
        "cough", "coughing", "kof", "cof", "koff", "coff", "kob", "kofsik"
    ],
    "breathing_problem": [
        "trouble breathing", "difficulty breathing", "shortness of breath",
        "breathing", "breathe", "bret", "blowin", "bluin", "bluinbluin", "shotwin"
    ],
    "chest_pain": [
        "chest pain", "ches pein", "jes pein", "chest", "ches", "jes", "briskit"
    ],
    "vomiting": [
        "vomit", "vomiting", "throwing up", "spew", "spyu",
        "bako", "bamit", "bomit", "chak-ap"
    ],
    "diarrhea": [
        "diarrhea", "diarrhoea", "loose stool", "shit",
        "ranishit", "gatseik", "jurratj", "toilet"
    ],
    "rash": [
        "rash", "itchy skin", "red skin", "itji", "itchiness", "skin"
    ],
    "pain": [
        "pain", "hurt", "aching", "sore", "pein", "pen",
        "peining", "etim", "herdam", "herding", "juwa"
    ],
    "headache": [
        "headache", "head pain", "hedache", "hedake", "headek",
        "hedeik", "edeik"
    ],
    "sore_throat": [
        "sore throat", "throat pain", "throt", "throut", "trot", "sowa"
    ],
    "dizzy": [
        "dizzy", "disi", "gidibat", "dizzi", "dizi", "lightheaded", "aigran", "gabarra"
    ],
    "weak": [
        "weak", "wek", "wik", "wikbala", "wikwan", "tired", "nagap"
    ],
}


def _root_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _load_kriol_dictionary() -> Dict:
    path = os.path.join(_root_dir(), "data", "dictionaries", "kriol_dictionary.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_kriol_to_english(dictionary: Dict) -> Dict[str, str]:
    flattened = {}

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
            flattened[str(kriol_word).strip().lower()] = str(english_word).strip().lower()

    return flattened


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_language(text: str, kriol_map: Dict[str, str]) -> str:
    words = re.findall(r"[a-zA-Z0-9_-]+", text.lower())
    if not words:
        return "english"

    kriol_hits = sum(1 for w in words if w in kriol_map)

    if kriol_hits == 0:
        return "english"
    if kriol_hits >= max(1, len(words) // 3):
        return "kriol"
    return "mixed"


def _translate_kriol_to_english(text: str, kriol_map: Dict[str, str]) -> str:
    tokens = re.findall(r"[A-Za-z0-9_'-]+|[^A-Za-z0-9_'-]+", text)
    translated = []

    for token in tokens:
        lower = token.lower()
        if re.fullmatch(r"[A-Za-z0-9_'-]+", token):
            translated.append(kriol_map.get(lower, lower))
        else:
            translated.append(token)

    translated_text = "".join(translated)
    translated_text = re.sub(r"\s+", " ", translated_text).strip()
    return translated_text


def _extract_symptoms(text_en: str) -> List[str]:
    found = []

    for symptom, aliases in SYMPTOM_MAP.items():
        if any(alias in text_en for alias in aliases):
            found.append(symptom)

    return found or ["general symptoms"]


def process_user_input(raw_text: str, ui_language: str) -> Dict:
    if teammate_nlp:
        teammate_output = teammate_nlp(raw_text, ui_language)

        symptoms = teammate_output.get("symptoms", [])
        detected_language = teammate_output.get("detected_language", ui_language)
        original_text = teammate_output.get("original_text", raw_text.strip())
        translated_text_en = teammate_output.get("translated_text_en", raw_text.strip())
        normalized_text_en = teammate_output.get("normalized_text_en", translated_text_en)
        red_flags = teammate_output.get("red_flags", [])

        return {
            "detected_language": detected_language,
            "original_text": original_text,
            "translated_text_en": translated_text_en,
            "normalized_text_en": normalized_text_en,
            "symptoms": symptoms,
            "red_flags": red_flags,
            "red_flag_questions": get_red_flag_questions(language_code=ui_language),
            "followup_questions": select_followup_questions(
                symptoms,
                max_questions=5,
                language_code=ui_language
            ),
        }

    dictionary = _load_kriol_dictionary()
    kriol_map = _flatten_kriol_to_english(dictionary)

    original_text = raw_text.strip()
    normalized = _normalize_text(original_text)

    detected_language = _detect_language(normalized, kriol_map)

    if detected_language in ("kriol", "mixed") or ui_language == "kriol":
        translated_text_en = _translate_kriol_to_english(normalized, kriol_map)
    else:
        translated_text_en = normalized

    symptoms = _extract_symptoms(translated_text_en)

    red_flags = []
    if "breathing_problem" in symptoms:
        red_flags.append("breathing_problem")
    if "chest_pain" in symptoms:
        red_flags.append("chest_pain")

    followup_questions = select_followup_questions(
        symptoms,
        max_questions=5,
        language_code=ui_language
    )

    return {
        "detected_language": detected_language,
        "original_text": original_text,
        "translated_text_en": translated_text_en,
        "normalized_text_en": translated_text_en,
        "symptoms": symptoms,
        "red_flags": red_flags,
        "red_flag_questions": get_red_flag_questions(language_code=ui_language),
        "followup_questions": followup_questions,
    }