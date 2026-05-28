from __future__ import annotations

"""
SACA Triage Orchestrator
========================
Use this file as: src/services/triage_orchestrator.py

Fixes included:
1. No repeated generic questions for every disease.
2. No old pain-scale rule: 1-3 / 4-7 / 8-10 no longer decides result.
3. NLP + ML drive the follow-up questions and the final result.
4. Critical result is based on red-flag symptoms / dangerous combinations, not pain scale alone.
"""

from typing import Dict, Iterable, List, Set
import re

from src.services.nlp_service import process_user_input
from src.services.ml_tflite_service import assess_symptoms


YES_VALUES = {"yes", "y", "yeah", "yep", "true", "1", "yuwai", "ha"}
NO_VALUES = {"no", "n", "nope", "false", "0", "nomu", "nah"}

RED_FLAG_SYMPTOMS = {
    "not_breathing",
    "unresponsive",
    "severe_difficulty_breathing",
    "severe_shortness_of_breath",
    "severe_chest_pain",
    "sudden_severe_chest_pain",
    "crushing_chest_pain",
    "coughing_blood",
    "vomiting_blood",
    "confusion",
    "collapse",
    "seizure",
    "continuous_seizure",
    "slurred_speech",
    "facial_drooping",
    "sudden_facial_drooping",
    "unable_to_speak_full_sentences",
}

# Symptom families stop the app asking the same thing in a different wording.
SYMPTOM_FAMILY = {
    "fever": "fever",
    "mild_fever": "fever",
    "high_fever": "fever",
    "cough": "cough",
    "mild_cough": "cough",
    "productive_cough": "cough",
    "headache": "headache",
    "mild_headache": "headache",
    "severe_headache": "headache",
    "sudden_severe_headache": "headache",
    "sore_throat": "throat",
    "severe_throat_pain": "throat",
    "throat_swelling": "throat",
    "body_aches": "body_aches",
    "fatigue": "fatigue",
    "weakness": "fatigue",
    "dizziness": "dizziness",
    "severe_dizziness": "dizziness",
    "abdominal_pain": "abdomen",
    "abdominal_discomfort": "abdomen",
    "severe_abdominal_pain": "abdomen",
    "sudden_severe_abdominal_pain": "abdomen",
    "upper_abdominal_pain": "abdomen",
    "right_upper_abdominal_pain": "abdomen",
    "vomiting": "vomiting",
    "vomiting_blood": "vomiting",
    "diarrhea": "diarrhea",
    "nausea": "nausea",
    "difficulty_breathing": "breathing",
    "severe_difficulty_breathing": "breathing",
    "shortness_of_breath": "breathing",
    "severe_shortness_of_breath": "breathing",
    "wheezing": "breathing",
    "severe_wheezing": "breathing",
    "chest_pain": "chest",
    "severe_chest_pain": "chest",
    "sudden_chest_pain": "chest",
    "sudden_severe_chest_pain": "chest",
    "crushing_chest_pain": "chest",
    "chest_tightness": "chest",
    "rash": "skin",
    "skin_rash": "skin",
    "skin_redness": "skin",
    "spreading_redness": "skin",
    "itching": "skin",
}

LABELS_EN = {
    "difficulty_breathing": "difficulty breathing",
    "shortness_of_breath": "shortness of breath",
    "severe_difficulty_breathing": "severe difficulty breathing",
    "severe_shortness_of_breath": "severe shortness of breath",
    "chest_pain": "chest pain",
    "severe_chest_pain": "severe chest pain",
    "sudden_severe_chest_pain": "sudden severe chest pain",
    "crushing_chest_pain": "crushing chest pain",
    "fever": "fever",
    "high_fever": "high fever",
    "cough": "cough",
    "productive_cough": "productive cough",
    "headache": "headache",
    "severe_headache": "severe headache",
    "sore_throat": "sore throat",
    "body_aches": "body pain",
    "fatigue": "tiredness",
    "weakness": "weakness",
    "vomiting": "vomiting",
    "diarrhea": "diarrhea",
    "nausea": "nausea",
    "abdominal_pain": "stomach pain",
    "severe_abdominal_pain": "severe stomach pain",
    "dizziness": "dizziness",
    "rash": "skin rash",
    "skin_rash": "skin rash",
    "spreading_redness": "spreading redness",
    "coughing_blood": "coughing blood",
    "vomiting_blood": "vomiting blood",
    "confusion": "confusion",
    "collapse": "collapse",
    "seizure": "seizure",
}

LABELS_KRIOL = {
    "difficulty_breathing": "brithin trabul",
    "shortness_of_breath": "short brith",
    "severe_difficulty_breathing": "brabli had fo brith",
    "severe_shortness_of_breath": "brabli short brith",
    "chest_pain": "jes pein",
    "severe_chest_pain": "brabli jes pein",
    "sudden_severe_chest_pain": "kwikwan brabli jes pein",
    "crushing_chest_pain": "brabli hevi jes pein",
    "fever": "fiba",
    "high_fever": "brabli fiba",
    "cough": "kof",
    "productive_cough": "kof wit gris",
    "headache": "hedake",
    "severe_headache": "brabli hedake",
    "sore_throat": "throt pein",
    "body_aches": "bodi pein",
    "fatigue": "brabli taid",
    "weakness": "wik",
    "vomiting": "spyu",
    "diarrhea": "ranishit",
    "nausea": "fil laik spyu",
    "abdominal_pain": "beli pein",
    "severe_abdominal_pain": "brabli beli pein",
    "dizziness": "dizi",
    "rash": "skin trabul",
    "skin_rash": "skin trabul",
    "spreading_redness": "redwan im spred",
    "coughing_blood": "kof blad",
    "vomiting_blood": "spyu blad",
    "confusion": "konfius",
    "collapse": "poldaun",
    "seizure": "seizha",
}


def _is_kriol(ui_language: str) -> bool:
    return str(ui_language or "en").lower().strip() in {"kriol", "kr"}


def _label(symptom: str, ui_language: str = "en") -> str:
    symptom = str(symptom)
    if _is_kriol(ui_language):
        return LABELS_KRIOL.get(symptom, symptom.replace("_", " "))
    return LABELS_EN.get(symptom, symptom.replace("_", " "))


def _family(symptom: str) -> str:
    return SYMPTOM_FAMILY.get(str(symptom), str(symptom))


def _dedupe_by_family(symptoms: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen_families: Set[str] = set()
    for symptom in symptoms or []:
        symptom = str(symptom)
        family = _family(symptom)
        if family in seen_families:
            continue
        out.append(symptom)
        seen_families.add(family)
    return out


def _question_for_symptom(symptom: str, ui_language: str = "en") -> Dict:
    label = _label(symptom, ui_language)
    if _is_kriol(ui_language):
        text_map = {
            "difficulty_breathing": "Yu garr brithin trabul?",
            "shortness_of_breath": "Yu garr short brith?",
            "chest_pain": "Yu garr jes pein?",
            "severe_chest_pain": "Jes pein im brabli nogud?",
            "high_fever": "Yu bodi brabli hot?",
            "fever": "Yu garr fiba?",
            "vomiting": "Yu spyu?",
            "diarrhea": "Yu garr ranishit?",
            "severe_abdominal_pain": "Beli pein im brabli nogud?",
            "dizziness": "Yu fil dizi?",
            "confusion": "Yu fil konfius?",
            "collapse": "Yu bin poldaun?",
            "spreading_redness": "Skin redwan im spred?",
        }
        text = text_map.get(symptom, f"Yu garr {label}?")
        return {"id": f"mlsym_{symptom}", "text": text, "options": ["yes", "no"], "ml_symptom": symptom}

    text_map = {
        "difficulty_breathing": "Are you having trouble breathing?",
        "shortness_of_breath": "Are you short of breath?",
        "chest_pain": "Do you have chest pain?",
        "severe_chest_pain": "Is the chest pain severe?",
        "high_fever": "Is your fever very high?",
        "fever": "Do you have a fever?",
        "vomiting": "Are you vomiting?",
        "diarrhea": "Do you have diarrhea?",
        "severe_abdominal_pain": "Is the stomach pain severe?",
        "dizziness": "Are you feeling dizzy?",
        "confusion": "Are you feeling confused?",
        "collapse": "Have you collapsed or fainted?",
        "spreading_redness": "Is the redness spreading?",
    }
    text = text_map.get(symptom, f"Do you also have {label}?")
    return {"id": f"mlsym_{symptom}", "text": text, "options": ["yes", "no"], "ml_symptom": symptom}


def _collect_nlp_symptoms(nlp_output: Dict) -> List[str]:
    # Prefer canonical_symptoms — these are already deduplicated and have
    # generic 'pain' stripped when a specific pain symptom is present.
    # Fall back to symptoms_present only when canonical is absent.
    negated = set(str(s) for s in (nlp_output.get("symptoms_negated") or []))

    canonical = [
        str(s) for s in (nlp_output.get("canonical_symptoms") or [])
        if s and str(s) not in negated
    ]
    if canonical:
        return canonical

    # Fallback path: use symptoms_present but exclude negated ones
    symptoms: List[str] = []
    for key in ["symptoms", "symptoms_present", "extracted_symptoms", "present"]:
        for item in nlp_output.get(key, []) or []:
            if isinstance(item, dict):
                value = item.get("name") or item.get("symptom") or item.get("text")
            else:
                value = item
            if value and str(value) not in symptoms and str(value) not in negated:
                symptoms.append(str(value))
        if symptoms:
            break
    return symptoms


def _answer_is_yes(value) -> bool:
    return str(value or "").strip().lower() in YES_VALUES


def _symptoms_from_answers(answers: Dict) -> List[str]:
    symptoms: List[str] = []
    for key, value in (answers or {}).items():
        if not str(key).startswith("mlsym_"):
            continue
        if _answer_is_yes(value):
            symptoms.append(str(key).replace("mlsym_", "", 1))
    return symptoms


def _pain_scale(answers: Dict) -> int:
    # Pain scale is saved for display only. It no longer decides green/orange/red.
    try:
        return max(1, min(10, int((answers or {}).get("pain_scale", 3))))
    except Exception:
        return 3


def _symptom_groups(symptoms: Iterable[str]) -> Set[str]:
    return {_family(str(s)) for s in symptoms or []}


def _context_followup_candidates(symptoms: Iterable[str]) -> List[str]:
    """Legacy fallback — only used when no ML candidates are available."""
    groups = _symptom_groups(symptoms)
    candidates: List[str] = []
    if groups & {"cough", "fever", "throat", "body_aches", "fatigue"}:
        candidates += ["difficulty_breathing", "chest_pain", "high_fever"]
    if groups & {"abdomen", "vomiting", "diarrhea", "nausea"}:
        candidates += ["severe_abdominal_pain", "vomiting", "diarrhea", "fever"]
    if groups & {"chest", "breathing"}:
        candidates += ["severe_chest_pain", "severe_difficulty_breathing", "dizziness", "collapse"]
    if groups & {"headache", "dizziness"}:
        candidates += ["severe_headache", "vomiting", "confusion", "vision_changes"]
    if groups & {"skin"}:
        candidates += ["spreading_redness", "fever", "skin_warmth", "pain"]
    if not candidates:
        candidates = ["fever", "cough", "difficulty_breathing"]
    return candidates


def _discriminating_symptoms(
    top_candidates: List,
    confirmed_symptoms: Set[str],
    max_questions: int = 3,
) -> List[str]:
    """
    Find symptoms that best discriminate between the top candidate diseases.

    Strategy
    --------
    For each pair of the top-2 candidates, a symptom is "discriminating" if it
    appears in ONE candidate's profile but NOT in the other's.  Asking about it
    lets the model separate the two diseases.

    Additionally, for candidates that are close in score, we include high-value
    missing symptoms (ones that appear in many of the top candidates) so that
    confirming them would boost confidence across the board.

    Returns a de-duplicated list of vocab symptom names, capped at max_questions.
    """
    if not top_candidates:
        return []

    selected: List[str] = []
    selected_families: Set[str] = set()

    def _add(symptom: str) -> bool:
        """Add symptom if not already confirmed or family-covered. Return True if added."""
        if symptom in confirmed_symptoms:
            return False
        fam = _family(symptom)
        if fam in selected_families:
            return False
        if symptom in selected:
            return False
        selected.append(symptom)
        selected_families.add(fam)
        return True

    # ── Phase 1: pairwise discriminating symptoms between top-2 candidates ─────
    if len(top_candidates) >= 2:
        a_profile = set(top_candidates[0].missing_symptoms + top_candidates[0].matching_symptoms)
        b_profile = set(top_candidates[1].missing_symptoms + top_candidates[1].matching_symptoms)

        only_in_a = [s for s in top_candidates[0].missing_symptoms if s in a_profile - b_profile]
        only_in_b = [s for s in top_candidates[1].missing_symptoms if s in b_profile - a_profile]

        # Interleave: one from A, one from B — gives maximum discrimination
        for sym_a, sym_b in zip(only_in_a, only_in_b):
            if len(selected) >= max_questions:
                break
            _add(sym_a)
            if len(selected) < max_questions:
                _add(sym_b)

        # If still have room, fill from remaining discriminating symptoms
        for sym in only_in_a + only_in_b:
            if len(selected) >= max_questions:
                break
            _add(sym)

    # ── Phase 2: high-value missing symptoms shared across top candidates ─────
    # A symptom appearing in multiple top candidates that is not yet confirmed
    # gives the model more signal regardless of which disease wins.
    if len(selected) < max_questions:
        from collections import Counter
        frequency: Counter = Counter()
        for candidate in top_candidates:
            for sym in candidate.missing_symptoms:
                frequency[sym] += 1
        # Prioritise symptoms missing from 2+ candidates, not already selected
        for sym, count in frequency.most_common():
            if len(selected) >= max_questions:
                break
            if count >= 2:
                _add(sym)

    # ── Phase 3: any missing symptom from the top candidate (fallback) ───────
    if len(selected) < max_questions and top_candidates:
        for sym in top_candidates[0].missing_symptoms:
            if len(selected) >= max_questions:
                break
            _add(sym)

    return selected


def _choose_followups(initial_ml, initial_symptoms: Iterable[str], ui_language: str) -> List[Dict]:
    """
    Generate follow-up questions that discriminate between the ML's top
    candidate diseases.

    Flow
    ----
    1. If ML confidence is already high (>= 0.80) AND no needs_follow_up flag
       → no questions needed.
    2. Use top_candidates from the ML result to find discriminating symptoms.
    3. Fall back to context rules only if no candidates available.
    """
    confirmed = set(initial_ml.input_symptoms or []) | set(str(s) for s in initial_symptoms)
    top_candidates = getattr(initial_ml, "top_candidates", []) or []

    # No follow-up if already high confidence and model is sure
    if (
        not getattr(initial_ml, "needs_follow_up", True)
        and getattr(initial_ml, "confidence", 0) >= 0.80
        and not top_candidates
    ):
        return []

    # ── Discriminating approach ───────────────────────────────────────────
    if top_candidates:
        discriminating = _discriminating_symptoms(top_candidates, confirmed)
        if discriminating:
            return [_question_for_symptom(sym, ui_language) for sym in discriminating]

    # ── Fallback: legacy context rules (no ML candidates) ─────────────────
    legacy_candidates = _context_followup_candidates(confirmed)
    selected: List[str] = []
    selected_families: Set[str] = set()
    for symptom in legacy_candidates:
        fam = _family(symptom)
        if symptom in confirmed or fam in selected_families or symptom in selected:
            continue
        selected.append(symptom)
        selected_families.add(fam)
        if len(selected) >= 3:
            break
    return [_question_for_symptom(sym, ui_language) for sym in selected]


# Symptoms that always warrant a clinic visit regardless of ML severity output.
# This guards against models that are biased towards outputting MILD.
MODERATE_SYMPTOMS = {
    "difficulty_breathing", "shortness_of_breath",
    "chest_pain", "chest_tightness", "wheezing", "severe_wheezing",
    "high_fever",
    "severe_headache", "sudden_severe_headache",
    "severe_abdominal_pain", "sudden_severe_abdominal_pain", "right_upper_abdominal_pain",
    "severe_dizziness", "rapid_heart_rate", "palpitations",
    "vomiting_blood", "coughing_blood",
    "stiff_neck", "photophobia",
    "arm_weakness", "vision_changes", "blurred_vision",
    "spreading_redness", "jaundice",
    "severe_back_pain", "blood_in_urine",
    "low_blood_pressure",
}


def _dangerous_combination(symptoms: Iterable[str]) -> bool:
    symptom_set = set(symptoms)
    if symptom_set & RED_FLAG_SYMPTOMS:
        return True
    if {"chest_pain", "difficulty_breathing"}.issubset(symptom_set):
        return True
    if {"chest_pain", "shortness_of_breath"}.issubset(symptom_set):
        return True
    if {"chest_pain", "sweating"}.issubset(symptom_set):
        return True
    if {"fever", "confusion"}.issubset(symptom_set):
        return True
    if {"fever", "stiff_neck"}.issubset(symptom_set):
        return True
    if {"severe_headache", "vomiting"}.issubset(symptom_set):
        return True
    if {"severe_abdominal_pain", "fever"}.issubset(symptom_set):
        return True
    if {"severe_abdominal_pain", "vomiting_blood"} & symptom_set:
        return True
    return False


def _triage_from_ml(final_ml, final_symptoms: Iterable[str]) -> str:
    symptoms = set(final_symptoms) | set(getattr(final_ml, "input_symptoms", []) or [])

    # ── Critical: red-flag symptoms or dangerous combinations ─────────────
    if _dangerous_combination(symptoms):
        return "critical"

    # ── Moderate: rule-based (takes precedence over ML severity output) ───
    # The TFLite model can output MILD even for moderate symptoms if its
    # training data was imbalanced. Apply symptom rules regardless.
    if symptoms & MODERATE_SYMPTOMS:
        return "moderate"

    # ── Also honour ML severity if it says MODERATE ───────────────────────
    severity = str(getattr(final_ml, "severity", "MILD") or "MILD").upper()
    if severity == "MODERATE":
        return "moderate"

    # ── Mild / rest at home ───────────────────────────────────────────────
    return "mild"


def _ats_from_triage(triage_level: str) -> int:
    if triage_level == "critical":
        return 1
    if triage_level == "moderate":
        return 3
    return 5


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.70:
        return "High"
    if confidence >= 0.45:
        return "Medium"
    return "Low"


def _condition_name(symptoms: Iterable[str], triage_level: str, ui_language: str) -> str:
    symptom_set = set(symptoms)
    kr = _is_kriol(ui_language)

    # Critical / emergency conditions first
    if triage_level == "critical":
        if symptom_set & {"chest_pain", "severe_chest_pain", "crushing_chest_pain",
                          "difficulty_breathing", "shortness_of_breath",
                          "severe_difficulty_breathing", "severe_shortness_of_breath"}:
            return "Possible heart or lung emergency" if not kr else "Mait bigwan hat o lank trabul"
        if symptom_set & {"severe_headache", "sudden_severe_headache", "confusion",
                          "facial_drooping", "slurred_speech", "seizure"}:
            return "Possible brain emergency" if not kr else "Mait bigwan bren trabul"
        if symptom_set & {"severe_abdominal_pain", "vomiting_blood"}:
            return "Possible abdominal emergency" if not kr else "Mait bigwan beli trabul"
        return "Medical emergency" if not kr else "Medikal imijensi"

    # Moderate conditions
    if triage_level == "moderate":
        if symptom_set & {"chest_pain", "difficulty_breathing", "shortness_of_breath",
                          "chest_tightness", "wheezing"}:
            return "Breathing or chest problem" if not kr else "Brith o jes trabul"
        if symptom_set & {"severe_headache", "sudden_severe_headache", "stiff_neck"}:
            return "Severe headache — needs review" if not kr else "Brabli hedake — nid lukluk"
        if symptom_set & {"severe_abdominal_pain", "right_upper_abdominal_pain"}:
            return "Severe stomach pain" if not kr else "Brabli beli pein"
        if symptom_set & {"high_fever", "fever"} and symptom_set & {"cough", "body_aches", "fatigue"}:
            return "Flu or infection" if not kr else "Flu o infekshan"
        if symptom_set & {"spreading_redness", "rash", "skin_rash"}:
            return "Skin infection — needs review" if not kr else "Skin infekshan — nid lukluk"

    # Mild conditions
    if symptom_set & {"chest_pain", "severe_chest_pain", "difficulty_breathing", "shortness_of_breath", "breathing_problem"}:
        return "Breathing or chest problem" if not kr else "Brith o jes trabul"
    if symptom_set & {"stomach_pain", "abdominal_pain", "vomiting", "diarrhea", "nausea"}:
        return "Stomach upset" if not kr else "Beli trobul"
    if symptom_set & {"fever", "high_fever", "cough", "sore_throat", "body_aches", "fatigue", "runny_nose", "mild_fever", "mild_cough"}:
        return "A mild flu or cold" if not kr else "Liklik flu o kol"
    if symptom_set & {"rash", "skin_rash", "skin_redness", "itching"}:
        return "Skin irritation" if not kr else "Skin trabul"
    if symptom_set & {"headache", "severe_headache", "dizziness", "dizzy", "mild_headache"}:
        return "Headache or dizziness" if not kr else "Hedake o dizi"
    return "General health concern" if not kr else "Jeneral helt trabul"


def _display_symptoms(symptoms: Iterable[str], ui_language: str) -> List[Dict[str, str]]:
    clean = _dedupe_by_family(symptoms)
    return [
        {
            "code": symptom,
            "label": _label(symptom, "en"),
            "kriol_label": _label(symptom, "kriol"),
            "display": _label(symptom, ui_language),
        }
        for symptom in clean
    ]


def _result_content(triage_level: str, symptoms: Iterable[str], condition: str, confidence: float, ui_language: str) -> Dict:
    is_kriol = _is_kriol(ui_language)
    confidence_text = _confidence_label(confidence)

    if triage_level == "critical":
        return {
            "status": "critical",
            "header": "Garr imijensi elp nau" if is_kriol else "Get emergency help now",
            "main_action": "KOL 000 NAU" if is_kriol else "CALL 000 NOW",
            "primary_icon": "☎",
            "left_title": "Wanim fo du:" if is_kriol else "What to do:",
            "right_title": "Wai dis result:" if is_kriol else "Why this result:",
            "what_to_do": [
                "Kol 000" if is_kriol else "Call 000",
                "No draib yuself" if is_kriol else "Do not drive yourself",
                "Askim sambodi neba fo help" if is_kriol else "Ask someone nearby for help",
            ],
            "why": "Red-flag symptoms detected." if not is_kriol else "Bigwan denja simptom bin faindim.",
            "warning": "⚠ This may be serious. Get help now." if not is_kriol else "⚠ Diswan mait bigwan. Garr elp nau.",
            "confidence_label": confidence_text,
        }

    if triage_level == "moderate":
        return {
            "status": "moderate",
            "header": "Plis kolim klinik sun" if is_kriol else "Please contact the clinic soon",
            "main_action": "KOL KLINIK NAU" if is_kriol else "CALL CLINIC NOW",
            "primary_icon": "☎",
            "left_title": "Yu simptom:" if is_kriol else "Your symptoms:",
            "right_title": "Wanim fo du nekis:" if is_kriol else "What to do next:",
            "what_to_do": [
                "Kol klinik tidei o tumoro" if is_kriol else "Call clinic today or tomorrow",
                "Rest wen yu weit" if is_kriol else "Rest while waiting",
                "Garr elp kwik if simptom kam nogud" if is_kriol else "Seek help faster if symptoms get worse",
            ],
            "why": "Your symptoms may need health worker review." if not is_kriol else "Yu simptom mait nid helt wokabala lukluk.",
            "warning": "⚠ If breathing becomes hard, chest pain starts, or you collapse, use Emergency Help."
            if not is_kriol else "⚠ If brith kam had, jes pein stat, o yu poldaun, yusim Imijensi Elp.",
            "confidence_label": confidence_text,
        }

    return {
        "status": "mild",
        "header": "Yu ken rest langa haus fo nau" if is_kriol else "You can rest at home for now",
        "main_action": "Yu nid fo rest" if is_kriol else "You need to take a rest",
        "primary_icon": "▱",
        "left_title": "Wanim fo du:" if is_kriol else "What to do:",
        "right_title": "Wai dis result:" if is_kriol else "Why this result:",
        "what_to_do": [
            "Rest" if is_kriol else "Rest",
            "Dringgim woda" if is_kriol else "Drink water",
            "Lukluk simptom" if is_kriol else "Monitor symptoms",
        ],
        "why": "Based on your symptoms, this looks mild" if not is_kriol else "Bikos langa yu simptom, diswan luk liklik",
        "warning": "ℹ If you get worse, call the clinic." if not is_kriol else "ℹ If yu kam nogud, kolim klinik.",
        "confidence_label": confidence_text,
    }


# ---------------------------------------------------------------------------
# Public functions used by MainWindow
# ---------------------------------------------------------------------------


def run_initial_assessment(raw_text: str, ui_language: str = "en") -> Dict:
    nlp_output = process_user_input(raw_text, ui_language=ui_language)
    nlp_symptoms = _collect_nlp_symptoms(nlp_output)

    extra_text = " ".join([
        str(raw_text or ""),
        str(nlp_output.get("translated_text_en", "")),
        str(nlp_output.get("mapped_text", "")),
        str(nlp_output.get("cleaned_text", "")),
        str(nlp_output.get("original_text", "")),
    ])

    initial_ml = assess_symptoms(nlp_symptoms, extra_text=extra_text)
    followups = _choose_followups(initial_ml, nlp_symptoms, ui_language)

    # Serialize top_candidates for downstream use
    top_candidates_data = [
        {
            "name": c.name,
            "score": c.score,
            "ats_level": c.ats_level,
            "matching_symptoms": c.matching_symptoms,
            "missing_symptoms": c.missing_symptoms,
        }
        for c in (initial_ml.top_candidates or [])
    ]

    nlp_output["ui_language"] = ui_language
    nlp_output["followup_questions"] = followups
    nlp_output["ml_initial"] = {
        "confidence": round(float(initial_ml.confidence), 4),
        "needs_follow_up": bool(initial_ml.needs_follow_up),
        "needs_follow_up_score": round(float(initial_ml.needs_follow_up_score), 4),
        "severity": initial_ml.severity,
        "suggested_symptoms": initial_ml.suggested_symptoms,
        "input_symptoms": initial_ml.input_symptoms,
        "model_available": initial_ml.model_available,
        "top_candidates": top_candidates_data,
    }
    nlp_output["symptoms"] = list(dict.fromkeys((initial_ml.input_symptoms or []) + nlp_symptoms))
    return nlp_output


def run_final_assessment(nlp_output: Dict, answers: Dict, ui_language: str = "en") -> Dict:
    ui_language = nlp_output.get("ui_language") or ui_language or "en"

    initial_symptoms = _collect_nlp_symptoms(nlp_output)
    answered_symptoms = _symptoms_from_answers(answers)
    all_symptoms = list(dict.fromkeys(initial_symptoms + answered_symptoms))

    negated_symptoms = set(str(s) for s in (nlp_output.get("symptoms_negated") or []))
    # Also build a set of negated canonical codes for post-filtering
    from src.services.nlp_service import APP_SYMPTOM_MAP as _ASM
    negated_codes = set()
    for s in negated_symptoms:
        negated_codes.add(_ASM.get(s, s.replace(" ", "_")))
    negated_codes.update(negated_symptoms)

    extra_text = " ".join([
        str(nlp_output.get("translated_text_en", "")),
        str(nlp_output.get("mapped_text", "")),
        str(nlp_output.get("cleaned_text", "")),
        str(nlp_output.get("original_text", "")),
        " ".join(answered_symptoms),
    ])
    # Remove negated symptom words from extra_text so the ML service
    # does not re-detect symptoms the user explicitly denied
    for neg in negated_symptoms:
        extra_text = re.sub(r"\b" + re.escape(neg) + r"\b", "", extra_text, flags=re.IGNORECASE)
    extra_text = re.sub(r"\s+", " ", extra_text).strip()

    final_ml = assess_symptoms(all_symptoms, extra_text=extra_text)
    final_symptoms = [
        s for s in list(dict.fromkeys((final_ml.input_symptoms or []) + answered_symptoms))
        if s not in negated_codes
    ]

    triage_level = _triage_from_ml(final_ml, final_symptoms)
    ats_level = _ats_from_triage(triage_level)
    condition = _condition_name(final_symptoms, triage_level, ui_language)
    content = _result_content(triage_level, final_symptoms, condition, float(final_ml.confidence), ui_language)

    ats_label = "Emergency" if triage_level == "critical" else "Clinic" if triage_level == "moderate" else "Rest"

    return {
        "nlp": {
            **nlp_output,
            "symptoms": final_symptoms,
            "symptoms_from_followup": answered_symptoms,
            "display_symptoms": _display_symptoms(final_symptoms, ui_language),
        },
        "answers": answers or {},
        "result": {
            "predicted_disease": condition,
            "confidence": round(float(final_ml.confidence), 4),
            "confidence_label": _confidence_label(float(final_ml.confidence)),
            "ats_level": ats_level,
            "ats_label": ats_label,
            "triage_level": triage_level,
            "pain_scale": _pain_scale(answers),
            "advice": content["header"],
            "result_content": content,
            "detected_symptoms": _display_symptoms(final_symptoms, ui_language),
            "possible_conditions": [
                {
                    "name": condition,
                    "why": content["why"],
                    "severity": final_ml.severity,
                    "image": "assets/images/default_condition.png",
                }
            ],
            "ml": {
                "model_available": final_ml.model_available,
                "severity": final_ml.severity,
                "needs_follow_up": final_ml.needs_follow_up,
                "needs_follow_up_score": round(float(final_ml.needs_follow_up_score), 4),
                "suggested_symptoms": final_ml.suggested_symptoms,
                "input_symptoms": final_ml.input_symptoms,
            },
        },
    }
