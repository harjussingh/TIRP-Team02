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
    symptoms: List[str] = []
    for key in ["symptoms", "symptoms_present", "extracted_symptoms", "present"]:
        for item in nlp_output.get(key, []) or []:
            if isinstance(item, dict):
                value = item.get("name") or item.get("symptom") or item.get("text")
            else:
                value = item
            if value and str(value) not in symptoms:
                symptoms.append(str(value))
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
    groups = _symptom_groups(symptoms)
    candidates: List[str] = []

    # Respiratory / flu-like cases
    if groups & {"cough", "fever", "throat", "body_aches", "fatigue"}:
        candidates += ["difficulty_breathing", "chest_pain", "high_fever"]

    # Stomach cases
    if groups & {"abdomen", "vomiting", "diarrhea", "nausea"}:
        candidates += ["severe_abdominal_pain", "vomiting", "diarrhea", "fever"]

    # Chest / breathing cases
    if groups & {"chest", "breathing"}:
        candidates += ["severe_chest_pain", "severe_difficulty_breathing", "dizziness", "collapse"]

    # Head / neuro cases
    if groups & {"headache", "dizziness"}:
        candidates += ["severe_headache", "vomiting", "confusion", "vision_changes"]

    # Skin cases
    if groups & {"skin"}:
        candidates += ["spreading_redness", "fever", "skin_warmth", "pain"]

    if not candidates:
        candidates = ["fever", "cough", "difficulty_breathing"]

    return candidates


def _choose_followups(initial_ml, initial_symptoms: Iterable[str], ui_language: str) -> List[Dict]:
    current_symptoms = set(initial_ml.input_symptoms or []) | set(str(s) for s in initial_symptoms)
    current_families = {_family(s) for s in current_symptoms}

    candidates: List[str] = []

    # Use ML suggested symptoms only when the model says follow-up is needed.
    if getattr(initial_ml, "needs_follow_up", False):
        candidates.extend(getattr(initial_ml, "suggested_symptoms", []) or [])

    # Add symptom-specific questions so every disease does not get the same generic list.
    candidates.extend(_context_followup_candidates(current_symptoms))

    selected: List[str] = []
    selected_families: Set[str] = set()

    for symptom in candidates:
        symptom = str(symptom)
        family = _family(symptom)
        if symptom in current_symptoms:
            continue
        if family in current_families:
            continue
        if symptom in selected or family in selected_families:
            continue
        selected.append(symptom)
        selected_families.add(family)
        if len(selected) >= 3:
            break

    return [_question_for_symptom(symptom, ui_language) for symptom in selected]


def _dangerous_combination(symptoms: Iterable[str]) -> bool:
    symptom_set = set(symptoms)
    if symptom_set & RED_FLAG_SYMPTOMS:
        return True
    if {"chest_pain", "difficulty_breathing"}.issubset(symptom_set):
        return True
    if {"chest_pain", "shortness_of_breath"}.issubset(symptom_set):
        return True
    if {"fever", "confusion"}.issubset(symptom_set):
        return True
    if {"severe_abdominal_pain", "vomiting_blood"} & symptom_set:
        return True
    return False


def _triage_from_ml(final_ml, final_symptoms: Iterable[str]) -> str:
    symptoms = set(final_symptoms) | set(getattr(final_ml, "input_symptoms", []) or [])

    # Critical comes from red-flag symptoms/combinations, not from the pain number.
    if _dangerous_combination(symptoms):
        return "critical"

    severity = str(getattr(final_ml, "severity", "MILD") or "MILD").upper()
    if severity == "MODERATE":
        return "moderate"

    # NEEDS_REST and MILD both go to the green/rest result page.
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
    if symptom_set & {"chest_pain", "severe_chest_pain", "difficulty_breathing", "shortness_of_breath"}:
        return "Breathing or chest problem" if not _is_kriol(ui_language) else "Brith o jes trabul"
    if symptom_set & {"fever", "high_fever", "cough", "sore_throat", "body_aches", "fatigue", "runny_nose"}:
        if triage_level == "mild":
            return "A mild flu or cold" if not _is_kriol(ui_language) else "Liklik flu o kol"
        return "Flu or infection" if not _is_kriol(ui_language) else "Flu o infekshan"
    if symptom_set & {"abdominal_pain", "vomiting", "diarrhea", "nausea"}:
        return "Stomach infection" if not _is_kriol(ui_language) else "Beli infekshan"
    if symptom_set & {"rash", "skin_rash", "skin_redness", "itching", "spreading_redness"}:
        return "Skin problem" if not _is_kriol(ui_language) else "Skin trabul"
    if symptom_set & {"headache", "severe_headache", "dizziness"}:
        return "Headache or dizziness" if not _is_kriol(ui_language) else "Hedake o dizi"
    return "General health problem" if not _is_kriol(ui_language) else "Jeneral helt trabul"


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
    }
    nlp_output["symptoms"] = list(dict.fromkeys((initial_ml.input_symptoms or []) + nlp_symptoms))
    return nlp_output


def run_final_assessment(nlp_output: Dict, answers: Dict, ui_language: str = "en") -> Dict:
    ui_language = nlp_output.get("ui_language") or ui_language or "en"

    initial_symptoms = _collect_nlp_symptoms(nlp_output)
    answered_symptoms = _symptoms_from_answers(answers)
    all_symptoms = list(dict.fromkeys(initial_symptoms + answered_symptoms))

    extra_text = " ".join([
        str(nlp_output.get("translated_text_en", "")),
        str(nlp_output.get("mapped_text", "")),
        str(nlp_output.get("cleaned_text", "")),
        str(nlp_output.get("original_text", "")),
        " ".join(answered_symptoms),
    ])

    final_ml = assess_symptoms(all_symptoms, extra_text=extra_text)
    final_symptoms = list(dict.fromkeys((final_ml.input_symptoms or []) + answered_symptoms))

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
