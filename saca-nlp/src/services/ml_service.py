from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

try:
    import joblib  # type: ignore
except Exception:  # pragma: no cover
    joblib = None


ATS_LABELS = {
    1: "Resuscitation",
    2: "Emergency",
    3: "Urgent",
    4: "Semi-Urgent",
    5: "Non-Urgent",
}

ATS_ADVICE = {
    1: "Get urgent help now",
    2: "Go to hospital immediately",
    3: "Visit clinic soon",
    4: "Visit a GP or clinic",
    5: "Rest and monitor",
}

# Notebook disease list copied from teammate notebook so the Windows app matches the ML scope.
SELECTED_DISEASES: Dict[str, int] = {
    "heart attack": 1,
    "cardiac arrest": 1,
    "stroke": 1,
    "sepsis": 1,
    "meningitis": 1,
    "pulmonary embolism": 2,
    "appendicitis": 2,
    "acute pancreatitis": 2,
    "ectopic pregnancy": 2,
    "gastrointestinal hemorrhage": 2,
    "acute kidney injury": 2,
    "preeclampsia": 2,
    "peritonitis": 2,
    "alcohol withdrawal": 2,
    "pneumonia": 3,
    "asthma": 3,
    "chronic obstructive pulmonary disease (copd)": 3,
    "pyelonephritis": 3,
    "kidney stone": 3,
    "cholecystitis": 3,
    "angina": 3,
    "deep vein thrombosis (dvt)": 3,
    "diverticulitis": 3,
    "acute sinusitis": 3,
    "acute bronchitis": 3,
    "acute bronchiolitis": 3,
    "intestinal obstruction": 3,
    "liver disease": 3,
    "cirrhosis": 3,
    "fracture of the leg": 3,
    "fracture of the arm": 3,
    "fracture of the rib": 3,
    "concussion": 3,
    "pneumothorax": 3,
    "atrial fibrillation": 3,
    "pericarditis": 3,
    "encephalitis": 3,
    "endocarditis": 3,
    "osteomyelitis": 3,
    "septic arthritis": 3,
    "strep throat": 3,
    "hyperemesis gravidarum": 3,
    "urinary tract infection": 4,
    "otitis media": 4,
    "conjunctivitis": 4,
    "cataract": 4,
    "glaucoma": 4,
    "hypertension": 4,
    "diabetes": 4,
    "anxiety": 4,
    "depression": 4,
    "panic disorder": 4,
    "chronic back pain": 4,
    "osteoarthritis": 4,
    "rheumatoid arthritis": 4,
    "gout": 4,
    "eczema": 4,
    "contact dermatitis": 4,
    "psoriasis": 4,
    "scabies": 4,
    "impetigo": 4,
    "fungal infection of the skin": 4,
    "iron deficiency anemia": 4,
    "gastritis": 4,
    "gastroesophageal reflux disease (gerd)": 4,
    "infectious gastroenteritis": 4,
    "tonsillitis": 4,
    "cystitis": 4,
    "prostatitis": 4,
    "pelvic inflammatory disease": 4,
    "chlamydia": 4,
    "gonorrhea": 4,
    "multiple sclerosis": 4,
    "epilepsy": 4,
    "migraine": 4,
    "tension headache": 4,
    "fibromyalgia": 4,
    "hypothyroidism": 4,
    "polycystic ovarian syndrome (pcos)": 4,
    "endometriosis": 4,
    "ovarian cyst": 4,
    "smoking or tobacco addiction": 4,
    "alcohol abuse": 4,
    "drug abuse": 4,
    "attention deficit hyperactivity disorder (adhd)": 4,
    "autism": 4,
    "dementia": 4,
    "parkinson disease": 4,
    "common cold": 5,
    "flu": 5,
    "viral infection": 5,
    "upper respiratory infection": 5,
    "food poisoning": 5,
    "seasonal allergies (hay fever)": 5,
    "allergy": 5,
    "hemorrhoids": 5,
    "chronic constipation": 5,
    "irritable bowel syndrome": 5,
    "dental caries": 5,
    "gum disease": 5,
    "acne": 5,
    "seborrheic dermatitis": 5,
    "insect bite": 5,
    "varicose veins": 5,
    "osteoporosis": 5,
    "macular degeneration": 5,
    "dry eye of unknown cause": 5,
}

# Fallback profiles keep the app usable when the trained notebook artifacts have not been exported yet.
PROFILE_RULES = [
    {
        "name": "gastritis",
        "ats": 4,
        "symptoms": {"stomach_pain", "pain"},
        "why": "matched with stomach/abdominal pain symptoms",
        "image": "assets/images/stomach.png",
    },
    {
        "name": "infectious gastroenteritis",
        "ats": 4,
        "symptoms": {"stomach_pain", "vomiting", "diarrhea", "fever"},
        "why": "matched with stomach symptoms and possible infection pattern",
        "image": "assets/images/stomach.png",
    },
    {
        "name": "common cold",
        "ats": 5,
        "symptoms": {"cough", "sore_throat", "fever"},
        "why": "matched with cough and throat symptoms",
        "image": "assets/images/respiratory.png",
    },
    {
        "name": "flu",
        "ats": 5,
        "symptoms": {"fever", "cough", "pain", "weak", "headache"},
        "why": "matched with fever, cough and body symptoms",
        "image": "assets/images/fever.png",
    },
    {
        "name": "upper respiratory infection",
        "ats": 5,
        "symptoms": {"cough", "sore_throat", "breathing_problem", "fever"},
        "why": "matched with respiratory symptoms",
        "image": "assets/images/respiratory.png",
    },
    {
        "name": "pneumonia",
        "ats": 3,
        "symptoms": {"cough", "fever", "breathing_problem", "chest_pain"},
        "why": "matched with fever, cough and breathing difficulty",
        "image": "assets/images/respiratory.png",
    },
    {
        "name": "asthma",
        "ats": 3,
        "symptoms": {"breathing_problem", "cough", "chest_pain"},
        "why": "matched with breathing-related symptoms",
        "image": "assets/images/respiratory.png",
    },
    {
        "name": "infectious gastroenteritis",
        "ats": 4,
        "symptoms": {"stomach_pain", "vomiting", "diarrhea", "fever", "pain"},
        "why": "matched with vomiting and diarrhea symptoms",
        "image": "assets/images/stomach.png",
    },
    {
        "name": "food poisoning",
        "ats": 5,
        "symptoms": {"stomach_pain", "vomiting", "diarrhea", "pain"},
        "why": "matched with stomach and vomiting symptoms",
        "image": "assets/images/stomach.png",
    },
    {
        "name": "appendicitis",
        "ats": 2,
        "symptoms": {"stomach_pain", "pain", "vomiting", "fever"},
        "why": "matched with abdominal pain, vomiting and fever",
        "image": "assets/images/stomach.png",
    },
    {
        "name": "migraine",
        "ats": 4,
        "symptoms": {"headache", "dizzy", "vomiting"},
        "why": "matched with headache and dizziness symptoms",
        "image": "assets/images/default_condition.png",
    },
    {
        "name": "meningitis",
        "ats": 1,
        "symptoms": {"fever", "headache", "vomiting"},
        "why": "matched with severe fever and headache pattern",
        "image": "assets/images/fever.png",
    },
    {
        "name": "eczema",
        "ats": 4,
        "symptoms": {"rash"},
        "why": "matched with skin irritation symptoms",
        "image": "assets/images/skin.png",
    },
    {
        "name": "contact dermatitis",
        "ats": 4,
        "symptoms": {"rash", "pain"},
        "why": "matched with skin rash symptoms",
        "image": "assets/images/skin.png",
    },
    {
        "name": "heart attack",
        "ats": 1,
        "symptoms": {"chest_pain", "breathing_problem", "pain"},
        "why": "matched with chest pain and breathing distress",
        "image": "assets/images/default_condition.png",
    },
]

SEVERITY_LABELS = {
    "mild": "Non-Urgent",
    "moderate": "Semi-Urgent",
    "high": "Urgent",
    "critical": "Emergency",
}

DEFAULT_FEATURES = [
    "fever", "cough", "breathing_problem", "chest_pain", "vomiting", "diarrhea",
    "rash", "pain", "headache", "sore_throat", "dizzy", "weak",
]


@dataclass
class PredictionOutput:
    disease: str
    confidence: float
    ats_level: int
    ats_label: str
    advice: str
    possible_conditions: List[Dict[str, str]]
    triage_level: str


class NotebookMLAdapter:
    """Drop-in service for the teammate notebook.

    If exported sklearn artifacts are present, they are used.
    Otherwise, the adapter falls back to rule-based matching that mirrors the
    teammate notebook's disease and ATS logic closely enough for the Windows app.
    """

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or Path(__file__).resolve().parents[2] / "models"
        self.feature_names: List[str] = []
        self.weights: Dict[str, int] = {
            "random_forest": 1,
            "extra_trees": 2,
            "naive_bayes": 3,
            "decision_tree": 1,
        }
        self.models: Dict[str, object] = {}
        self.classes_: Optional[np.ndarray] = None
        self._load_exported_artifacts()

    def _load_exported_artifacts(self) -> None:
        if joblib is None or not self.model_dir.exists():
            return

        metadata_path = self.model_dir / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                self.feature_names = metadata.get("feature_names", [])
                self.weights.update(metadata.get("weights", {}))
            except Exception:
                pass

        names = {
            "random_forest": "random_forest.joblib",
            "extra_trees": "extra_trees.joblib",
            "naive_bayes": "naive_bayes.joblib",
            "decision_tree": "decision_tree.joblib",
        }

        for key, filename in names.items():
            path = self.model_dir / filename
            if path.exists():
                try:
                    model = joblib.load(path)
                    self.models[key] = model
                except Exception:
                    continue

        if self.models:
            first = next(iter(self.models.values()))
            self.classes_ = getattr(first, "classes_", None)
            if not self.feature_names:
                self.feature_names = list(getattr(first, "feature_names_in_", DEFAULT_FEATURES))

    def predict(self, symptoms: List[str], answers: Dict[str, str], ui_language: str = "en") -> PredictionOutput:
        if np is not None and self.models and self.feature_names and self.classes_ is not None:
            return self._predict_with_exported_models(symptoms, answers)
        return self._predict_with_rules(symptoms, answers)

    def _predict_with_exported_models(self, symptoms: List[str], answers: Dict[str, str]) -> PredictionOutput:
        vector = np.zeros((1, len(self.feature_names)), dtype=float)
        symptom_set = set(symptoms)
        for idx, feature in enumerate(self.feature_names):
            if feature in symptom_set:
                vector[0, idx] = 1.0

        probs = None
        total_weight = 0
        for key, model in self.models.items():
            try:
                model_probs = model.predict_proba(vector)[0]
            except Exception:
                continue
            weight = int(self.weights.get(key, 1))
            probs = model_probs * weight if probs is None else probs + model_probs * weight
            total_weight += weight

        if probs is None or total_weight == 0:
            return self._predict_with_rules(symptoms, answers)

        probs = probs / total_weight
        sorted_idx = np.argsort(probs)[::-1]
        top = [(str(self.classes_[i]), float(probs[i])) for i in sorted_idx[:3]]
        best_disease, confidence = top[0]
        ats = int(SELECTED_DISEASES.get(best_disease, 4))
        possible_conditions = [
            {
                "name": disease,
                "why": f"model confidence {prob:.0%}",
                "severity": ATS_LABELS.get(int(SELECTED_DISEASES.get(disease, 4)), "Semi-Urgent"),
                "image": self._guess_image(disease),
            }
            for disease, prob in top
        ]
        triage = self._ats_to_triage(ats, confidence, answers)
        return PredictionOutput(
            disease=best_disease,
            confidence=confidence,
            ats_level=ats,
            ats_label=ATS_LABELS[ats],
            advice=self._advice_for_ats(ats, answers),
            possible_conditions=possible_conditions,
            triage_level=triage,
        )

    def _predict_with_rules(self, symptoms: List[str], answers: Dict[str, str]) -> PredictionOutput:
        symptom_set = set(symptoms)
        pain_scale = int(answers.get("pain_scale", 3))
        red_breath = answers.get("red_breathing_now") == "yes"
        red_chest = answers.get("red_chest_pain_now") == "yes"
        red_bleed = answers.get("red_heavy_bleeding") == "yes"
        red_passed_out = answers.get("red_passed_out") == "yes"

        scored: List[Tuple[float, Dict[str, object]]] = []
        for profile in PROFILE_RULES:
            profile_symptoms = set(profile["symptoms"])
            overlap = len(profile_symptoms & symptom_set)
            if overlap == 0:
                continue
            base = overlap / max(len(profile_symptoms), 1)
            # boost if explicit symptom cluster is more complete
            if profile["ats"] <= 2 and (red_breath or red_chest or red_bleed or red_passed_out):
                base += 0.35
            if pain_scale >= 8 and profile["ats"] <= 3:
                base += 0.15
            if pain_scale <= 3 and profile["ats"] >= 4:
                base += 0.05
            scored.append((base, profile))

        if not scored:
            fallback = {
                "name": "viral infection",
                "ats": 5 if pain_scale <= 4 else 4,
                "why": "matched with general symptom pattern",
                "severity": "Non-Urgent" if pain_scale <= 4 else "Semi-Urgent",
                "image": "assets/images/default_condition.png",
            }
            possible = [fallback]
            best_disease = fallback["name"]
            confidence = 0.35
            ats = int(fallback["ats"])
        else:
            scored.sort(key=lambda item: item[0], reverse=True)
            top_profiles = scored[:3]
            best_score, best_profile = top_profiles[0]
            best_disease = str(best_profile["name"])
            confidence = min(0.95, max(0.35, best_score))
            ats = int(best_profile["ats"])
            possible = [
                {
                    "name": str(profile["name"]),
                    "why": str(profile["why"]),
                    "severity": ATS_LABELS.get(int(profile["ats"]), "Semi-Urgent"),
                    "image": str(profile["image"]),
                }
                for _, profile in top_profiles
            ]

        # Escalate based on red flags and pain scale.
        if red_bleed or red_passed_out:
            ats = 1
            best_disease = "sepsis" if "fever" in symptom_set else best_disease
            confidence = max(confidence, 0.85)
        elif red_breath and red_chest:
            ats = min(ats, 1)
            best_disease = "heart attack" if "chest_pain" in symptom_set else best_disease
            confidence = max(confidence, 0.82)
        elif red_breath or red_chest or pain_scale >= 8:
            ats = min(ats, 2 if red_breath or red_chest else 3)
            confidence = max(confidence, 0.72)
        elif pain_scale >= 6:
            ats = min(ats, 3)
            confidence = max(confidence, 0.6)

        triage = self._ats_to_triage(ats, confidence, answers)
        return PredictionOutput(
            disease=best_disease,
            confidence=confidence,
            ats_level=ats,
            ats_label=ATS_LABELS[ats],
            advice=self._advice_for_ats(ats, answers),
            possible_conditions=possible,
            triage_level=triage,
        )

    def _guess_image(self, disease: str) -> str:
        disease_l = disease.lower()
        if any(term in disease_l for term in ["skin", "eczema", "dermatitis", "scabies", "psoriasis", "acne"]):
            return "assets/images/skin.png"
        if any(term in disease_l for term in ["pneumonia", "asthma", "respiratory", "bronch", "copd"]):
            return "assets/images/respiratory.png"
        if any(term in disease_l for term in ["gastr", "append", "gastro", "food poisoning", "pancreatitis"]):
            return "assets/images/stomach.png"
        if any(term in disease_l for term in ["flu", "viral", "sepsis", "meningitis"]):
            return "assets/images/fever.png"
        return "assets/images/default_condition.png"

    def _ats_to_triage(self, ats: int, confidence: float, answers: Dict[str, str]) -> str:
        if ats <= 1:
            return "critical"
        if ats == 2:
            return "critical"
        if ats == 3:
            return "high"
        if ats == 4:
            return "moderate"
        return "mild"

    def _advice_for_ats(self, ats: int, answers: Dict[str, str]) -> str:
        if answers.get("red_heavy_bleeding") == "yes" or answers.get("red_passed_out") == "yes":
            return "Get urgent help now"
        if ats <= 1:
            return "Get urgent help now"
        return ATS_ADVICE.get(ats, "Consult a healthcare provider")


def build_result_payload(nlp_output: Dict, answers: Dict, ui_language: str = "en") -> Dict:
    adapter = NotebookMLAdapter()
    prediction = adapter.predict(nlp_output.get("symptoms", []), answers, ui_language=ui_language)
    return {
        "nlp": nlp_output,
        "result": {
            "predicted_disease": prediction.disease,
            "confidence": prediction.confidence,
            "ats_level": prediction.ats_level,
            "ats_label": prediction.ats_label,
            "triage_level": prediction.triage_level,
            "pain_scale": int(answers.get("pain_scale", 3)),
            "advice": prediction.advice,
            "possible_conditions": prediction.possible_conditions,
        },
    }
