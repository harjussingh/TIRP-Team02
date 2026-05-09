from __future__ import annotations

"""
SACA Windows NLP Service V3
===========================

This service integrates the uploaded TIRP Team 02 NLP module into the PySide6
Windows app.  It keeps the interface stable for the UI while using the team
pipeline concepts:

1. Language detection: English / Kriol / mixed
2. Kriol-to-English translation
3. Text preprocessing and spelling normalisation
4. Synonym mapping
5. Symptom extraction
6. Negation detection
7. Feature-ready structured result

The heavy experimental components from the NLP module (BioClinicalBERT,
MarianMT and Bi-LSTM) are optional.  If their dependencies are not installed,
the app falls back to the deterministic dictionary + PhraseMatcher + rule-based
pipeline so the Windows prototype still runs reliably in class/demo settings.
"""

from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Tuple
import json
import re
import sys

from src.utils.paths import project_root
from src.utils.question_tree import get_red_flag_questions, select_followup_questions


ROOT = project_root()
DATA_DIR = ROOT / "data"

# Ensure the uploaded NLP package at project_root/nlp is importable.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


APP_SYMPTOM_MAP = {
    "shortness of breath": "breathing_problem",
    "trouble breathing": "breathing_problem",
    "difficulty breathing": "breathing_problem",
    "breathlessness": "breathing_problem",
    "chest pain": "chest_pain",
    "sore throat": "sore_throat",
    "abdominal pain": "stomach_pain",
    "stomach pain": "stomach_pain",
    "belly pain": "stomach_pain",
    "diarrhoea": "diarrhea",
    "diarrhea": "diarrhea",
    "dizziness": "dizzy",
    "fatigue": "weak",
    "muscle pain": "body_pain",
    "joint pain": "body_pain",
    "body pain": "body_pain",
    "body ache": "body_pain",
    "rash": "rash",
    "itching": "rash",
    "fever": "fever",
    "cough": "cough",
    "headache": "headache",
    "vomiting": "vomiting",
    "nausea": "nausea",
    "bleeding": "bleeding",
    "swelling": "swelling",
    "pain": "pain",
    "weakness": "weak",
}

# Extra terms used when the optional teammate modules are unavailable.
FALLBACK_SYMPTOMS = [
    "fever", "cough", "headache", "chest pain", "shortness of breath",
    "vomiting", "diarrhoea", "diarrhea", "abdominal pain", "stomach pain",
    "dizziness", "sore throat", "nausea", "fatigue", "body pain", "body ache",
    "muscle pain", "joint pain", "rash", "itching", "bleeding", "swelling",
    "pain", "weakness",
]

KRIOL_EXTRA = {
    "mi": "i", "ai": "i", "yu": "you", "wi": "we", "dei": "they",
    "garr": "have", "gat": "have", "gadi": "have", "gadem": "have",
    "abum": "have", "fel": "feel", "fil": "feel", "bilim": "feel",
    "no": "not", "nat": "not", "nomo": "no more", "neba": "never",
    "bat": "but", "en": "and", "o": "or", "bikos": "because", "bikaj": "because",
    "hedache": "headache", "hedake": "headache", "headek": "headache",
    "hot-bodi": "fever", "hotbodi": "fever", "hot bodi": "fever",
    "fiwa": "fever", "fiva": "fever", "kof": "cough", "koff": "cough",
    "beli": "belly", "beliak": "belly ache", "binji": "stomach",
    "pein": "pain", "pen": "pain", "sowa": "sore", "trot": "throat",
    "sowa trot": "sore throat", "throt": "throat", "disi": "dizzy",
    "gidibat": "dizzy", "spyu": "vomiting", "spew": "vomiting",
    "chak-ap": "vomiting", "ranishit": "diarrhoea", "ches": "chest",
    "jes": "chest", "traubul": "trouble", "bret": "breath", "breeding": "breathing",
    "taid": "tired", "wek": "weak",
}

FALLBACK_SYNONYMS = {
    "high temperature": "fever",
    "temperature": "fever",
    "hot body": "fever",
    "body hot": "fever",
    "feverish": "fever",
    "head pain": "headache",
    "head hurts": "headache",
    "migraine": "headache",
    "dry cough": "cough",
    "wet cough": "cough",
    "trouble breathing": "shortness of breath",
    "difficulty breathing": "shortness of breath",
    "hard to breathe": "shortness of breath",
    "cannot breathe": "shortness of breath",
    "breathing problem": "shortness of breath",
    "chest tightness": "chest pain",
    "heart pain": "chest pain",
    "stomach ache": "abdominal pain",
    "stomach pain": "abdominal pain",
    "belly ache": "abdominal pain",
    "belly pain": "abdominal pain",
    "tummy pain": "abdominal pain",
    "body ache": "body pain",
    "body aches": "body pain",
    "throat pain": "sore throat",
    "throw up": "vomiting",
    "throwing up": "vomiting",
    "vomit": "vomiting",
    "feel sick": "nausea",
    "feeling sick": "nausea",
    "nauseous": "nausea",
    "dizzy": "dizziness",
    "lightheaded": "dizziness",
    "weak": "fatigue",
    "tired": "fatigue",
    "skin problem": "rash",
    "skin rash": "rash",
    "itchy skin": "itching",
    "blood": "bleeding",
    "bleed": "bleeding",
}

COMMON_WORDS = {
    "i", "a", "an", "the", "my", "me", "we", "he", "she", "it", "they",
    "am", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "will", "would", "can", "could", "should",
    "and", "or", "but", "not", "no", "so", "if", "in", "on", "at", "to",
    "for", "of", "with", "as", "by", "from", "up", "that", "this", "what",
    "which", "who", "when", "where", "how", "feel", "feels", "feeling", "felt",
    "hurt", "hurts", "pain", "bad", "very", "some", "any", "also", "now",
    "still", "since", "today", "yesterday", "days", "day", "water", "drink",
    "never", "none", "without", "nothing", "nobody", "deny", "denies", "lack",
    "absent", "only", "just", "there", "their", "these", "those",
}

NEGATION_WORDS = {"no", "not", "without", "never", "none", "nothing", "nobody", "deny", "denies", "lack", "absent"}
SCOPE_RESET_WORDS = {"but", "however", "although", "though", "yet", "except", "while", "whereas"}


@dataclass
class PipelineOutput:
    original_text: str
    detected_language: str
    language_confidence: float
    translated_text: str
    translation_method: str
    cleaned_text: str
    mapped_text: str
    extracted_symptoms: List[str]
    symptoms_present: List[str]
    symptoms_negated: List[str]
    canonical_symptoms: List[str]
    features: Dict[str, object]
    pipeline_source: str
    nlp_warning: str | None = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "original_text": self.original_text,
            "input_text": self.original_text,
            "detected_language": self.detected_language,
            "language_confidence": self.language_confidence,
            "translated_text": self.translated_text,
            "translated_text_en": self.translated_text,
            "translation_method": self.translation_method,
            "cleaned_text": self.cleaned_text,
            "mapped_text": self.mapped_text,
            "extracted_symptoms": self.extracted_symptoms,
            "symptoms_present": self.symptoms_present,
            "symptoms_negated": self.symptoms_negated,
            "canonical_symptoms": self.canonical_symptoms,
            "symptoms": self.canonical_symptoms,
            "features": self.features,
            "pipeline_source": self.pipeline_source,
            "nlp_warning": self.nlp_warning,
        }


def _load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _normalise_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("’", "'").replace("`", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_language_fallback(text: str) -> Tuple[str, float]:
    words = re.findall(r"[a-zA-Z'-]+", _normalise_text(text))
    if not words:
        return "english", 1.0
    kriol_words = set(KRIOL_EXTRA.keys()) | {"garr", "gat", "mi", "yu", "bat", "nomo", "hedache", "hot-bodi", "kof", "beli", "pein", "sowa", "trot"}
    hits = sum(1 for w in words if w in kriol_words)
    joined = " ".join(words)
    patterns = ["mi garr", "mi gat", "mi fel", "no garr", "bat mi", "sowa trot", "beli pein"]
    if any(p in joined for p in patterns):
        return "kriol", 0.9
    ratio = hits / max(len(words), 1)
    if ratio >= 0.15:
        return "kriol", min(0.95, 0.55 + ratio)
    if ratio > 0:
        return "mixed", min(0.8, 0.45 + ratio)
    return "english", 0.95


def _detect_language(text: str) -> Tuple[str, float, str | None]:
    try:
        from nlp.language_detector import detect_language as team_detect_language
        label, confidence = team_detect_language(text)
        return str(label), float(confidence), None
    except Exception as exc:
        label, confidence = _detect_language_fallback(text)
        return label, confidence, f"Team language detector unavailable; fallback used ({exc})."


def _load_kriol_dictionary() -> Dict[str, str]:
    dictionary: Dict[str, str] = {}
    try:
        from nlp.kriol_translator import load_kriol_dictionary
        dictionary = load_kriol_dictionary(str(DATA_DIR / "kriol_dictionary.json"))
    except Exception:
        raw = _load_json(DATA_DIR / "kriol_dictionary.json", {})
        if isinstance(raw, dict):
            # Handles both flat and grouped dictionary formats.
            for key, value in raw.items():
                if isinstance(value, dict):
                    dictionary.update({str(k).lower(): str(v).lower() for k, v in value.items()})
                else:
                    dictionary[str(key).lower()] = str(value).lower()
    dictionary.update(KRIOL_EXTRA)
    return dictionary


def _translate_fallback(text: str, kriol_dict: Dict[str, str], detected_language: str) -> Tuple[str, str, float]:
    if detected_language == "english":
        return text, "passthrough", 0.0

    text_l = _normalise_text(text)
    # Phrase replacements first.
    for phrase in sorted(kriol_dict.keys(), key=len, reverse=True):
        if " " in phrase or "-" in phrase:
            text_l = re.sub(r"\b" + re.escape(phrase) + r"\b", kriol_dict[phrase], text_l)

    tokens = re.findall(r"[a-zA-Z'-]+|\d+", text_l)
    translated = []
    oov = 0
    for tok in tokens:
        if tok in kriol_dict:
            translated.append(kriol_dict[tok])
        else:
            match = get_close_matches(tok, kriol_dict.keys(), n=1, cutoff=0.86)
            if match:
                translated.append(kriol_dict[match[0]])
            else:
                translated.append(tok)
                if tok not in COMMON_WORDS:
                    oov += 1
    out = " ".join(translated)
    out = re.sub(r"\bhot body\b", "fever", out)
    out = re.sub(r"\bbelly pain\b", "abdominal pain", out)
    out = re.sub(r"\bchest pain\b", "chest pain", out)
    out = re.sub(r"\bsore throat\b", "sore throat", out)
    out = re.sub(r"\btrouble breath(ing)?\b", "shortness of breath", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out, "fallback_dict", round(oov / max(len(tokens), 1), 4)


def _translate(text: str, kriol_dict: Dict[str, str], detected_language: str) -> Tuple[str, str, float, str | None]:
    # Use the uploaded team dictionary translator for predictable offline GUI use.
    # The teammate neural_translator.py can load a MarianMT model from HuggingFace;
    # that is useful for research but can pause/fail in a classroom demo, so it is
    # intentionally not called from the Windows app.
    if detected_language == "english":
        return text, "passthrough", 0.0, None
    try:
        from nlp.kriol_translator import translate_kriol_to_english, post_process_translation
        translated = translate_kriol_to_english(text, kriol_dict)
        translated = post_process_translation(translated)
        return translated, "dict", 0.0, None
    except Exception as exc:
        translated, method, oov = _translate_fallback(text, kriol_dict, detected_language)
        return translated, method, oov, f"Team dictionary translator unavailable; fallback used ({exc})."


def _clean_and_map(text: str, symptoms: List[str], synonyms: Dict[str, str]) -> Tuple[str, str, str | None]:
    known_words = set(COMMON_WORDS) | set(symptoms)
    for sym in symptoms:
        known_words.update(sym.split())
    for phrase in synonyms.keys():
        if not str(phrase).startswith("____"):
            known_words.update(str(phrase).split())

    try:
        from nlp.preprocess import clean_text
        from nlp.symptom_mapper import map_synonyms
        cleaned = clean_text(text, known_words=list(known_words))
        mapped = map_synonyms(cleaned, synonyms)
        return cleaned, mapped, None
    except Exception as exc:
        cleaned = _normalise_text(text)
        cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        mapped = cleaned
        for phrase, canonical in sorted(synonyms.items(), key=lambda x: len(str(x[0])), reverse=True):
            if str(phrase).startswith("____"):
                continue
            mapped = re.sub(r"\b" + re.escape(str(phrase).lower()) + r"\b", str(canonical).lower(), mapped)
        return cleaned, mapped, f"Team preprocessing unavailable; fallback used ({exc})."


def _load_symptoms_and_synonyms() -> Tuple[List[str], Dict[str, str]]:
    symptoms = _load_json(DATA_DIR / "symptoms.json", FALLBACK_SYMPTOMS)
    if not isinstance(symptoms, list):
        symptoms = FALLBACK_SYMPTOMS
    symptoms = list(dict.fromkeys([str(s).lower() for s in symptoms] + FALLBACK_SYMPTOMS))

    raw_synonyms = _load_json(DATA_DIR / "synonyms.json", {})
    synonyms = {str(k).lower(): str(v).lower() for k, v in raw_synonyms.items() if not str(k).startswith("____")}
    synonyms.update(FALLBACK_SYNONYMS)
    return symptoms, synonyms


def _extract_symptoms(mapped_text: str, symptoms: List[str]) -> Tuple[List[str], str | None]:
    try:
        from nlp.symptom_extractor import SymptomExtractor
        found = SymptomExtractor(symptoms).extract_symptoms(mapped_text)
        return list(dict.fromkeys([s.lower() for s in found])), None
    except Exception as exc:
        found: List[str] = []
        for symptom in sorted(symptoms, key=len, reverse=True):
            if re.search(r"\b" + re.escape(symptom) + r"\b", mapped_text):
                if symptom not in found:
                    found.append(symptom)
        return found, f"Team symptom extractor unavailable; fallback used ({exc})."


def _is_negated(tokens: List[str], symptom_start_idx: int) -> bool:
    window = tokens[max(0, symptom_start_idx - 6):symptom_start_idx]
    for i in range(len(window) - 1, -1, -1):
        if window[i] in SCOPE_RESET_WORDS:
            window = window[i + 1:]
            break
    window_text = " ".join(window)
    if any(t in NEGATION_WORDS for t in window):
        return True
    if re.search(r"\b(do|does|did|have|has|had|will|would|can|could|should)\s+not\b", window_text):
        return True
    return False


def _detect_negations_fallback(mapped_text: str, symptoms: List[str]) -> Tuple[List[str], List[str]]:
    tokens = mapped_text.split()
    present: List[str] = []
    negated: List[str] = []
    for symptom in symptoms:
        parts = symptom.split()
        occurrences = []
        for i in range(len(tokens) - len(parts) + 1):
            if tokens[i:i + len(parts)] == parts:
                occurrences.append((i, _is_negated(tokens, i)))
        if not occurrences:
            continue
        if any(not neg for _, neg in occurrences):
            present.append(symptom)
        elif any(neg for _, neg in occurrences):
            negated.append(symptom)
    return present, negated


def _detect_negations(mapped_text: str, extracted: List[str]) -> Tuple[List[str], List[str], str | None]:
    # The teammate module includes an experimental Bi-LSTM negation model that
    # can train/load on import. For the Windows prototype we keep the same
    # negation-scope logic but use the fast deterministic rule path so the UI
    # never freezes while processing a sentence.
    present, negated = _detect_negations_fallback(mapped_text, extracted)
    return present, negated, None


def _canonical_for_app(symptoms_present: List[str]) -> List[str]:
    canonical: List[str] = []
    for sym in symptoms_present:
        app_key = APP_SYMPTOM_MAP.get(sym, sym.replace(" ", "_"))
        if app_key not in canonical:
            canonical.append(app_key)
    return canonical


def _engineer_features(result: Dict[str, object]) -> Tuple[Dict[str, object], str | None]:
    # Keep GUI feature generation compact and deterministic. The teammate module
    # also has an advanced BERT embedding feature engineer, but that requires
    # transformers/model downloads and is better left optional for research runs.
    present = list(result.get("symptoms_present", []))
    negated = list(result.get("symptoms_negated", []))
    red_flags = {"chest pain", "shortness of breath", "bleeding"}
    severity_score = 0
    for sym in present:
        if sym in red_flags:
            severity_score += 8
        elif sym in {"fever", "vomiting", "diarrhoea", "diarrhea", "dizziness", "abdominal pain"}:
            severity_score += 5
        else:
            severity_score += 3
    if severity_score >= 12:
        category = "high"
    elif severity_score >= 6:
        category = "medium"
    else:
        category = "low"
    return {
        "symptom_count": len(present),
        "negated_count": len(negated),
        "severity_score": severity_score,
        "severity_category": category,
        "translation_applied": int(result.get("translation_method") != "passthrough"),
        "detected_language_label": result.get("detected_language", "english"),
    }, None


def run_team_pipeline(text: str, source: str = "text") -> PipelineOutput:
    original = (text or "").strip()
    symptoms, synonyms = _load_symptoms_and_synonyms()
    kriol_dict = _load_kriol_dictionary()

    warnings: List[str] = []
    detected_lang, confidence, warning = _detect_language(original)
    if warning:
        warnings.append(warning)

    translated, method, oov, warning = _translate(original, kriol_dict, detected_lang)
    if warning:
        warnings.append(warning)

    cleaned, mapped, warning = _clean_and_map(translated, symptoms, synonyms)
    if warning:
        warnings.append(warning)

    extracted, warning = _extract_symptoms(mapped, symptoms)
    if warning:
        warnings.append(warning)

    present, negated, warning = _detect_negations(mapped, extracted)
    if warning:
        warnings.append(warning)

    canonical = _canonical_for_app(present)
    partial_result: Dict[str, object] = {
        "input_text": original,
        "input_source": source,
        "detected_language": detected_lang,
        "language_confidence": round(confidence, 4),
        "translated_text": translated,
        "translation_method": method,
        "oov_ratio": oov,
        "cleaned_text": cleaned,
        "mapped_text": mapped,
        "extracted_symptoms": extracted,
        "symptoms_present": present,
        "symptoms_negated": negated,
    }
    features, warning = _engineer_features(partial_result)
    if warning:
        warnings.append(warning)

    return PipelineOutput(
        original_text=original,
        detected_language=detected_lang,
        language_confidence=round(confidence, 4),
        translated_text=translated,
        translation_method=method,
        cleaned_text=cleaned,
        mapped_text=mapped,
        extracted_symptoms=extracted,
        symptoms_present=present,
        symptoms_negated=negated,
        canonical_symptoms=canonical,
        features=features,
        pipeline_source="TIRP-Team02 NLP module + safe GUI adapter",
        nlp_warning=" | ".join(warnings) if warnings else None,
    )


def process_user_input(raw_text: str, ui_language: str = "en", source: str = "text") -> Dict[str, object]:
    """
    Entry point used by the Windows app.
    Returns the same keys expected by MainWindow, QuestionsPage and ML service.
    """
    output = run_team_pipeline(raw_text, source=source)
    result = output.as_dict()

    language_code = "kriol" if ui_language == "kriol" else "en"
    canonical = list(result.get("canonical_symptoms", []))

    questions = select_followup_questions(canonical, max_questions=5, language_code=language_code)

    # Add red flags when high-risk symptoms are detected.
    high_risk = {"chest_pain", "breathing_problem", "bleeding"}
    if any(sym in high_risk for sym in canonical):
        red = get_red_flag_questions(language_code=language_code)
        existing = {q.get("id") for q in questions}
        questions = red + [q for q in questions if q.get("id") not in existing]
        questions = questions[:5]

    # Avoid asking "where is the problem" again when the NLP already found an
    # area-specific symptom such as headache, chest pain, stomach pain or sore
    # throat. This keeps the flow shorter and less repetitive for users.
    area_specific = {"headache", "chest_pain", "stomach_pain", "sore_throat", "rash", "breathing_problem"}
    if any(sym in area_specific for sym in canonical):
        questions = [q for q in questions if q.get("id") not in {"where_problem", "pain_where"}]

    # If no symptoms are detected, use a compact general flow.
    if not questions:
        questions = select_followup_questions(["pain"], max_questions=5, language_code=language_code)

    result["followup_questions"] = questions
    return result
