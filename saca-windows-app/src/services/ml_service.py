import os
from typing import Dict, List

try:
    from src.integrations.team_ml import classify_case as teammate_ml
except Exception:
    teammate_ml = None


def _image(name: str) -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(root, "assets", "images", name)


def _build_conditions(symptoms: List[str]) -> List[Dict]:
    conditions = []

    if "fever" in symptoms or "cough" in symptoms or "sore_throat" in symptoms:
        conditions.append({
            "name": "Fever / Viral sickness",
            "why": "Matched with fever, cough or throat symptoms",
            "severity": "moderate",
            "image": _image("fever.png"),
        })

    if "breathing_problem" in symptoms or "chest_pain" in symptoms:
        conditions.append({
            "name": "Chest / breathing problem",
            "why": "Matched with breathing or chest symptoms",
            "severity": "serious",
            "image": _image("respiratory.png"),
        })

    if "vomiting" in symptoms or "diarrhea" in symptoms:
        conditions.append({
            "name": "Stomach / dehydration problem",
            "why": "Matched with vomiting or diarrhea symptoms",
            "severity": "moderate",
            "image": _image("stomach.png"),
        })

    if "rash" in symptoms:
        conditions.append({
            "name": "Skin / rash problem",
            "why": "Matched with rash symptoms",
            "severity": "moderate",
            "image": _image("skin.png"),
        })

    if not conditions:
        conditions.append({
            "name": "General health problem",
            "why": "General symptom pattern only",
            "severity": "mild",
            "image": _image("default_condition.png"),
        })

    return conditions


def classify_case(nlp_output: Dict, answers: Dict) -> Dict:
    if teammate_ml:
        return teammate_ml(nlp_output, answers)

    symptoms = nlp_output["symptoms"]
    pain_score = int(answers.get("pain_scale", 3))

    serious = False
    moderate = False

    if "breathing_problem" in symptoms or "chest_pain" in symptoms:
        serious = True

    if answers.get("red_breathing") == "yes":
        serious = True

    if answers.get("worse") == "yes":
        moderate = True

    if pain_score >= 8:
        serious = True
    elif pain_score >= 5:
        moderate = True

    if serious:
        triage_level = "serious"
        advice = "Get urgent help now."
    elif moderate:
        triage_level = "moderate"
        advice = "Visit clinic soon."
    else:
        triage_level = "mild"
        advice = "Rest and watch symptoms."

    return {
        "triage_level": triage_level,
        "possible_conditions": _build_conditions(symptoms),
        "advice": advice,
        "pain_scale": pain_score,
    }