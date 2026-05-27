from __future__ import annotations

"""
SACA ML TFLite Service
======================
Use this file as: src/services/ml_tflite_service.py

What it does:
- Loads models/ml/model.tflite, models/ml/model_meta.json, models/ml/symptom_vocab.json
- Keeps the symptom vocabulary exactly as the model expects, including index 0 = "None"
- Converts NLP / picture / typing symptoms into a (1, 234) multi-hot vector
- Runs the local TFLite model offline
- Returns confidence, needs_follow_up, severity, and suggested symptoms
- Has a safe fallback so the app still runs if TensorFlow/TFLite is missing
"""

from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence
import json
import re

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "ml"


# Converts common UI/NLP names into exact vocab names.
COMMON_SYMPTOM_MAP: Dict[str, str] = {
    "none": "None",
    "nil": "None",
    "no symptom": "None",

    # fever / cough / head
    "headache": "headache",
    "head ache": "headache",
    "head pain": "headache",
    "hedake": "headache",
    "hedache": "headache",
    "mild headache": "mild_headache",
    "bad headache": "severe_headache",
    "big headache": "severe_headache",
    "severe headache": "severe_headache",
    "sudden headache": "sudden_severe_headache",
    "fever": "fever",
    "fiba": "fever",
    "fiwa": "fever",
    "fiva": "fever",
    "body hot": "fever",
    "hot body": "fever",
    "hot-bodi": "fever",
    "hotbodi": "fever",
    "mild fever": "mild_fever",
    "high fever": "high_fever",
    "cough": "cough",
    "kof": "cough",
    "koff": "cough",
    "mild cough": "mild_cough",
    "productive cough": "productive_cough",
    "runny nose": "runny_nose",
    "blocked nose": "nasal_congestion",
    "congestion": "congestion",

    # breathing / chest
    "breathing_problem": "difficulty_breathing",
    "breathing problem": "difficulty_breathing",
    "breathing trouble": "difficulty_breathing",
    "trouble breathing": "difficulty_breathing",
    "brithin trabul": "difficulty_breathing",
    "hard to breathe": "difficulty_breathing",
    "difficulty breathing": "difficulty_breathing",
    "cannot breathe": "severe_difficulty_breathing",
    "can't breathe": "severe_difficulty_breathing",
    "not breathing": "not_breathing",
    "shortness of breath": "shortness_of_breath",
    "short breath": "shortness_of_breath",
    "shortness_of_breath": "shortness_of_breath",
    "severe shortness of breath": "severe_shortness_of_breath",
    "severe difficulty breathing": "severe_difficulty_breathing",
    "wheezing": "wheezing",
    "severe wheezing": "severe_wheezing",
    "chest pain": "chest_pain",
    "chest_pain": "chest_pain",
    "jes pein": "chest_pain",
    "chest tightness": "chest_tightness",
    "chest tight": "chest_tightness",
    "severe chest pain": "severe_chest_pain",
    "bad chest pain": "severe_chest_pain",
    "sudden chest pain": "sudden_chest_pain",
    "crushing chest pain": "crushing_chest_pain",
    "coughing blood": "coughing_blood",
    "kof blood": "coughing_blood",

    # stomach / bowel
    "stomach pain": "abdominal_pain",
    "stomach ache": "abdominal_discomfort",
    "belly pain": "abdominal_pain",
    "beli pein": "abdominal_pain",
    "abdominal pain": "abdominal_pain",
    "abdominal_pain": "abdominal_pain",
    "severe abdominal pain": "severe_abdominal_pain",
    "sudden severe abdominal pain": "sudden_severe_abdominal_pain",
    "upper abdominal pain": "upper_abdominal_pain",
    "right upper abdominal pain": "right_upper_abdominal_pain",
    "nausea": "nausea",
    "vomit": "vomiting",
    "vomiting": "vomiting",
    "spyu": "vomiting",
    "spew": "vomiting",
    "vomiting blood": "vomiting_blood",
    "diarrhoea": "diarrhea",
    "diarrhea": "diarrhea",
    "runny tummy": "diarrhea",
    "ranishit": "diarrhea",

    # body / neuro / skin
    "body pain": "body_aches",
    "body ache": "body_aches",
    "body aches": "body_aches",
    "body_ache": "body_aches",
    "body_pain": "body_aches",
    "bodi pein": "body_aches",
    "muscle pain": "joint_pain",
    "joint pain": "joint_pain",
    "pain": "pain",
    "mild pain": "mild_pain",
    "dizzy": "dizziness",
    "dizziness": "dizziness",
    "dizi": "dizziness",
    "severe dizziness": "severe_dizziness",
    "weak": "weakness",
    "weakness": "weakness",
    "tired": "fatigue",
    "taid": "fatigue",
    "fatigue": "fatigue",
    "very tired": "fatigue",
    "rash": "rash",
    "skin problem": "skin_rash",
    "skin rash": "skin_rash",
    "skin redness": "skin_redness",
    "itching": "itching",
    "sore throat": "sore_throat",
    "sore_throat": "sore_throat",
    "throat pain": "sore_throat",
    "throt pein": "sore_throat",
    "sowa trot": "sore_throat",

    # emergency / neuro
    "confusion": "confusion",
    "confused": "confusion",
    "unresponsive": "unresponsive",
    "fainting": "fainting",
    "fainted": "fainting",
    "collapse": "collapse",
    "collapsed": "collapse",
    "poldaun": "collapse",
    "seizure": "seizure",
    "continuous seizure": "continuous_seizure",
    "slurred speech": "slurred_speech",
    "cannot speak": "speech_difficulty",
    "unable to speak": "unable_to_speak_full_sentences",
    "facial drooping": "facial_drooping",
}

TEXT_PHRASE_TO_SYMPTOM: Dict[str, str] = {
    # emergency phrases first
    "not breathing": "not_breathing",
    "cannot breathe": "severe_difficulty_breathing",
    "can't breathe": "severe_difficulty_breathing",
    "very hard to breathe": "severe_difficulty_breathing",
    "severe shortness of breath": "severe_shortness_of_breath",
    "severe chest pain": "severe_chest_pain",
    "crushing chest pain": "crushing_chest_pain",
    "sudden severe chest pain": "sudden_severe_chest_pain",
    "coughing blood": "coughing_blood",
    "vomiting blood": "vomiting_blood",
    "passed out": "fainting",
    "fainted": "fainting",
    "collapse": "collapse",
    "collapsed": "collapse",
    "unresponsive": "unresponsive",
    "confused": "confusion",
    "slurred speech": "slurred_speech",
    "face droop": "facial_drooping",
    "facial drooping": "facial_drooping",

    # normal symptom phrases
    "headache": "headache",
    "head ache": "headache",
    "hot body": "fever",
    "body hot": "fever",
    "fever": "fever",
    "cough": "cough",
    "runny nose": "runny_nose",
    "sore throat": "sore_throat",
    "throat pain": "sore_throat",
    "stomach pain": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "abdominal pain": "abdominal_pain",
    "vomit": "vomiting",
    "vomiting": "vomiting",
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "body ache": "body_aches",
    "body aches": "body_aches",
    "body pain": "body_aches",
    "tired": "fatigue",
    "fatigue": "fatigue",
    "dizzy": "dizziness",
    "rash": "rash",
    "skin problem": "skin_rash",
    "chest pain": "chest_pain",
    "breathing problem": "difficulty_breathing",
    "shortness of breath": "shortness_of_breath",

    # Kriol-style phrases
    "mi garr kof": "cough",
    "kof": "cough",
    "fiba": "fever",
    "fiwa": "fever",
    "hot bodi": "fever",
    "hedake": "headache",
    "hedache": "headache",
    "beli pein": "abdominal_pain",
    "spyu": "vomiting",
    "dizi": "dizziness",
    "bodi pein": "body_aches",
    "taid": "fatigue",
    "throt pein": "sore_throat",
    "jes pein": "chest_pain",
    "brithin trabul": "difficulty_breathing",
}

RED_FLAG_SYMPTOMS = {
    "unresponsive",
    "not_breathing",
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


@dataclass
class MLAssessment:
    confidence: float
    needs_follow_up_score: float
    needs_follow_up: bool
    severity: str
    suggested_symptoms: List[str]
    input_symptoms: List[str]
    model_available: bool
    raw_outputs: Dict[str, object]


class SacaTFLiteModel:
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or DEFAULT_MODEL_DIR
        self.model_path = self.model_dir / "model.tflite"
        self.meta_path = self.model_dir / "model_meta.json"
        self.vocab_path = self.model_dir / "symptom_vocab.json"

        self.meta = self._load_json(self.meta_path, default={})
        self.vocab: List[str] = [str(v) for v in self._load_json(self.vocab_path, default=[])]

        # Important: keep the "None" token at index 0.
        # The model expects input_shape [1, 234], where 234 matches symptom_vocab.json.
        self.input_size = int((self.meta.get("input_shape") or [1, len(self.vocab) or 234])[1])
        if not self.vocab:
            self.vocab = ["None"] + sorted(set(COMMON_SYMPTOM_MAP.values()) - {"None"})
        self.vocab_to_index = {symptom: idx for idx, symptom in enumerate(self.vocab)}

        self.output_order = list(self.meta.get("output_order") or [
            "confidence", "needs_follow_up", "severity", "suggested_symptoms"
        ])
        self.severity_order = list(self.meta.get("severity_order") or ["MILD", "MODERATE", "NEEDS_REST"])

        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.model_available = False
        self._load_interpreter()

    def _load_json(self, path: Path, default):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"SACA ML: could not read {path}: {exc}")
        return default

    def _load_interpreter(self) -> None:
        if not self.model_path.exists() or np is None:
            return

        Interpreter = None
        try:
            from tflite_runtime.interpreter import Interpreter as RuntimeInterpreter  # type: ignore
            Interpreter = RuntimeInterpreter
        except Exception:
            try:
                from tensorflow.lite import Interpreter as TensorFlowInterpreter  # type: ignore
                Interpreter = TensorFlowInterpreter
            except Exception:
                Interpreter = None

        if Interpreter is None:
            return

        try:
            self.interpreter = Interpreter(model_path=str(self.model_path))
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.model_available = True
        except Exception as exc:
            print(f"SACA ML: TFLite model load failed, fallback will be used: {exc}")
            self.interpreter = None
            self.model_available = False

    def normalise_symptom(self, symptom: str) -> str:
        original = (symptom or "").strip()
        if not original:
            return ""

        key = original.lower().replace("-", " ").replace("_", " ")
        key = re.sub(r"\s+", " ", key).strip()

        if key in COMMON_SYMPTOM_MAP:
            return COMMON_SYMPTOM_MAP[key]

        underscore = key.replace(" ", "_")
        if underscore in self.vocab_to_index:
            return underscore

        # Fuzzy match only against real vocabulary tokens, not None.
        choices = [v for v in self.vocab if v.lower() != "none"]
        close = get_close_matches(underscore, choices, n=1, cutoff=0.86)
        if close:
            return close[0]
        return underscore

    def symptoms_to_vocab(self, symptoms: Iterable[str], extra_text: str = "") -> List[str]:
        found: List[str] = []

        for symptom in symptoms or []:
            mapped = self.normalise_symptom(str(symptom))
            if mapped and mapped in self.vocab_to_index and mapped.lower() != "none" and mapped not in found:
                found.append(mapped)

        text = (extra_text or "").lower()
        text = text.replace("_", " ").replace("-", " ")
        text = re.sub(r"\s+", " ", text).strip()

        for phrase, vocab_symptom in sorted(TEXT_PHRASE_TO_SYMPTOM.items(), key=lambda x: len(x[0]), reverse=True):
            if phrase in text and vocab_symptom in self.vocab_to_index and vocab_symptom not in found:
                found.append(vocab_symptom)

        return found

    def make_vector(self, symptoms: Iterable[str]) -> "np.ndarray":
        if np is None:
            raise RuntimeError("numpy is not installed")

        vector = np.zeros((1, self.input_size), dtype=np.float32)
        clean_symptoms = [s for s in symptoms if s and str(s).lower() != "none"]

        if not clean_symptoms and "None" in self.vocab_to_index and self.vocab_to_index["None"] < self.input_size:
            vector[0, self.vocab_to_index["None"]] = 1.0
            return vector

        for symptom in clean_symptoms:
            idx = self.vocab_to_index.get(str(symptom))
            if idx is not None and 0 <= idx < self.input_size:
                vector[0, idx] = 1.0
        return vector

    def predict(self, symptoms: Iterable[str], extra_text: str = "") -> MLAssessment:
        ml_symptoms = self.symptoms_to_vocab(symptoms, extra_text=extra_text)

        if not self.model_available or self.interpreter is None or self.input_details is None:
            return self._fallback_predict(ml_symptoms)

        try:
            vector = self.make_vector(ml_symptoms)
            self.interpreter.set_tensor(self.input_details[0]["index"], vector)
            self.interpreter.invoke()

            outputs = []
            for detail in self.output_details or []:
                outputs.append(self.interpreter.get_tensor(detail["index"]))

            parsed = self._parse_outputs(outputs)
            parsed.input_symptoms = ml_symptoms
            parsed.model_available = True
            return parsed
        except Exception as exc:
            print(f"SACA ML: inference failed, fallback will be used: {exc}")
            return self._fallback_predict(ml_symptoms)

    def _parse_outputs(self, outputs: Sequence[object]) -> MLAssessment:
        mapped: Dict[str, object] = {}
        for idx, name in enumerate(self.output_order):
            if idx < len(outputs):
                mapped[name] = outputs[idx]

        confidence = self._scalar(mapped.get("confidence"), default=0.55)
        needs_follow_up_score = self._scalar(mapped.get("needs_follow_up"), default=0.0)
        severity = self._severity_from_output(mapped.get("severity"))
        suggestions = self._suggestions_from_output(mapped.get("suggested_symptoms"))

        needs_follow_up = needs_follow_up_score >= 0.5
        if not needs_follow_up:
            suggestions = []

        return MLAssessment(
            confidence=float(confidence),
            needs_follow_up_score=float(needs_follow_up_score),
            needs_follow_up=bool(needs_follow_up),
            severity=severity,
            suggested_symptoms=suggestions,
            input_symptoms=[],
            model_available=True,
            raw_outputs={key: self._safe_preview(value) for key, value in mapped.items()},
        )

    def _scalar(self, value, default: float) -> float:
        try:
            if value is None or np is None:
                return default
            arr = np.array(value).astype(float).reshape(-1)
            if arr.size == 0:
                return default
            if arr.size == 1:
                return float(arr[0])
            return float(arr.max())
        except Exception:
            return default

    def _severity_from_output(self, value) -> str:
        try:
            if value is None or np is None:
                return "MILD"
            arr = np.array(value).reshape(-1)
            if arr.size == 1:
                idx = int(round(float(arr[0])))
            else:
                idx = int(np.argmax(arr))
            if 0 <= idx < len(self.severity_order):
                return str(self.severity_order[idx]).upper()
        except Exception:
            pass
        return "MILD"

    def _suggestions_from_output(self, value, top_n: int = 4) -> List[str]:
        if value is None or np is None:
            return []
        try:
            arr = np.array(value).reshape(-1)
            suggestions: List[str] = []

            # Case A: vector of scores over the whole vocab.
            if arr.size == len(self.vocab):
                scores = arr.astype(float)
                for idx in np.argsort(scores)[::-1]:
                    if idx >= len(self.vocab):
                        continue
                    symptom = self.vocab[int(idx)]
                    score = float(scores[int(idx)])
                    if symptom.lower() == "none":
                        continue
                    if score <= 0.05:
                        break
                    if symptom not in suggestions:
                        suggestions.append(symptom)
                    if len(suggestions) >= top_n:
                        break
                return suggestions

            # Case B: small array of suggested indices.
            if arr.size <= 20:
                for raw in arr:
                    try:
                        idx = int(round(float(raw)))
                    except Exception:
                        continue
                    if 0 <= idx < len(self.vocab):
                        symptom = self.vocab[idx]
                        if symptom.lower() != "none" and symptom not in suggestions:
                            suggestions.append(symptom)
                    if len(suggestions) >= top_n:
                        break
            return suggestions
        except Exception:
            return []

    def _safe_preview(self, value):
        try:
            if np is None:
                return str(value)
            arr = np.array(value)
            if arr.size <= 12:
                return arr.tolist()
            return {"shape": list(arr.shape), "preview": arr.reshape(-1)[:10].tolist()}
        except Exception:
            return str(value)

    def _fallback_predict(self, symptoms: List[str]) -> MLAssessment:
        symptom_set = set(symptoms)
        severity = "MILD"
        confidence = 0.55

        if symptom_set & RED_FLAG_SYMPTOMS:
            severity = "MODERATE"
            confidence = 0.84
        elif symptom_set & {"difficulty_breathing", "shortness_of_breath", "chest_pain", "severe_headache", "high_fever"}:
            severity = "MODERATE"
            confidence = 0.72
        elif symptom_set & {"fever", "cough", "headache", "body_aches", "sore_throat", "fatigue", "runny_nose"}:
            severity = "NEEDS_REST"
            confidence = 0.68

        # Fallback suggestions are symptom-related, not the same for every disease.
        suggestions = []
        if symptom_set & {"cough", "fever", "sore_throat", "runny_nose", "body_aches"}:
            suggestions = ["difficulty_breathing", "chest_pain", "high_fever"]
        elif symptom_set & {"abdominal_pain", "vomiting", "diarrhea", "nausea"}:
            suggestions = ["severe_abdominal_pain", "vomiting", "diarrhea", "fever"]
        elif symptom_set & {"chest_pain", "difficulty_breathing", "shortness_of_breath"}:
            suggestions = ["severe_chest_pain", "severe_difficulty_breathing", "dizziness", "collapse"]
        elif symptom_set & {"headache", "dizziness", "weakness"}:
            suggestions = ["severe_headache", "vision_changes", "confusion", "vomiting"]
        elif symptom_set & {"rash", "skin_rash", "itching", "skin_redness"}:
            suggestions = ["spreading_redness", "fever", "skin_warmth", "pain"]
        else:
            suggestions = ["fever", "cough", "difficulty_breathing"]

        suggestions = [s for s in suggestions if s not in symptom_set and s in self.vocab_to_index][:3]
        needs_follow_up = len(suggestions) > 0

        return MLAssessment(
            confidence=confidence,
            needs_follow_up_score=0.72 if needs_follow_up else 0.20,
            needs_follow_up=needs_follow_up,
            severity=severity,
            suggested_symptoms=suggestions,
            input_symptoms=symptoms,
            model_available=False,
            raw_outputs={"fallback": True},
        )


_ENGINE: Optional[SacaTFLiteModel] = None


def get_ml_engine() -> SacaTFLiteModel:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = SacaTFLiteModel()
    return _ENGINE


def assess_symptoms(symptoms: Iterable[str], extra_text: str = "") -> MLAssessment:
    return get_ml_engine().predict(symptoms, extra_text=extra_text)
