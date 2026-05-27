#!/usr/bin/env python3
"""
Test model.tflite locally with preset or custom symptom scenarios.

Uses the same files as the SACA Android/Windows apps:
  - model.tflite
  - model_meta.json
  - symptom_vocab.json

Install deps (from this folder):
  pip install numpy tensorflow
  # or: pip install numpy tflite-runtime

Examples:
  python test.py              # run all 7 app demo scenarios (same model as mobile/desktop)
  python test.py --list       # show copy-paste strings for Android / Windows
  python test.py --scenario demo_1_mild_cold
  python test.py --symptoms "mild fever, cough, runny nose, sore throat"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

try:
    import numpy as np
except ImportError:
    print("Missing numpy. Run: pip install numpy tensorflow", file=sys.stderr)
    sys.exit(1)


DIR = Path(__file__).resolve().parent
MODEL_PATH = DIR / "model.tflite"
META_PATH = DIR / "model_meta.json"
VOCAB_PATH = DIR / "symptom_vocab.json"

FOLLOW_UP_THRESHOLD = 0.5  # same as ml_tflite_service.py / Android TFLiteInferenceEngine

# Subset of app symptom aliases (enough for demo scenarios + CLI typing)
COMMON_SYMPTOM_MAP: Dict[str, str] = {
    "none": "None",
    "fever": "fever",
    "mild fever": "mild_fever",
    "high fever": "high_fever",
    "cough": "cough",
    "mild cough": "mild_cough",
    "productive cough": "productive_cough",
    "runny nose": "runny_nose",
    "sore throat": "sore_throat",
    "fatigue": "fatigue",
    "body aches": "body_aches",
    "headache": "headache",
    "mild headache": "mild_headache",
    "nausea": "nausea",
    "vomiting": "vomiting",
    "vomit": "vomiting",
    "diarrhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "abdominal pain": "abdominal_pain",
    "stomach pain": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "chest pain": "chest_pain",
    "crushing chest pain": "crushing_chest_pain",
    "severe chest pain": "severe_chest_pain",
    "shortness of breath": "shortness_of_breath",
    "difficulty breathing": "difficulty_breathing",
    "severe difficulty breathing": "severe_difficulty_breathing",
    "not breathing": "not_breathing",
    "dizziness": "dizziness",
    "sweating": "sweating",
    "confusion": "confusion",
    "collapse": "collapse",
    "loss of consciousness": "loss_of_consciousness",
    "cyanosis": "cyanosis",
}


@dataclass
class Scenario:
    id: str
    title: str
    symptoms: List[str]
    app_input: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.app_input:
            self.app_input = ", ".join(self.symptoms)


def _scenario(
    id: str,
    title: str,
    app_input: str,
    notes: str = "",
) -> Scenario:
    symptoms = [s.strip() for s in app_input.split(",") if s.strip()]
    return Scenario(id=id, title=title, symptoms=symptoms, app_input=app_input, notes=notes)


# Seven copy-paste inputs for Android / Windows (same model.tflite as this script).
APP_DEMO_SCENARIOS: List[Scenario] = [
    _scenario(
        "demo_1_mild_cold",
        "1 — Mild cold (best professor demo)",
        "mild fever, cough, runny nose, sore throat",
        "Type or speak exactly this in the app. Expect MILD severity; may ask follow-up.",
    ),
    _scenario(
        "demo_2_sparse_cough",
        "2 — Sparse input (follow-up likely)",
        "fever, cough",
        "Only two symptoms — good to show needs_follow_up and suggested symptoms.",
    ),
    _scenario(
        "demo_3_stomach",
        "3 — Stomach / GI",
        "abdominal pain, vomiting, diarrhea, nausea",
        "GI bundle for Windows typing or Android voice.",
    ),
    _scenario(
        "demo_4_chest_urgent",
        "4 — Urgent chest (not a cold)",
        "crushing chest pain, shortness of breath, sweating, nausea",
        "Higher-urgency pattern; compare severity vs demo 1.",
    ),
    _scenario(
        "demo_5_breathing",
        "5 — Breathing + chest",
        "cough, difficulty breathing, chest pain, fatigue",
        "Respiratory escalation; works with app phrase map.",
    ),
    _scenario(
        "demo_6_flu_like",
        "6 — Flu-like with body aches",
        "fever, cough, body aches, fatigue",
        "Common presentation; four clear tokens.",
    ),
    _scenario(
        "demo_7_headache",
        "7 — Headache / dizziness",
        "headache, dizziness, nausea",
        "Neuro-style cluster; three symptoms.",
    ),
]

# Alias used by CLI
SCENARIOS = APP_DEMO_SCENARIOS


@dataclass
class TFLiteResult:
    mapped_symptoms: List[str]
    confidence: float
    needs_follow_up_score: float
    needs_follow_up: bool
    severity: str
    suggested_symptoms: List[str]
    raw_outputs: Dict[str, object]


class TFLiteTester:
    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or DIR
        self.model_path = self.model_dir / "model.tflite"
        self.meta_path = self.model_dir / "model_meta.json"
        self.vocab_path = self.model_dir / "symptom_vocab.json"

        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        self.vocab: List[str] = json.loads(self.vocab_path.read_text(encoding="utf-8"))
        self.vocab_to_index = {s: i for i, s in enumerate(self.vocab)}

        shape = self.meta.get("input_shape") or [1, len(self.vocab)]
        self.input_size = int(shape[1])
        self.output_order = list(
            self.meta.get("output_order")
            or ["confidence", "needs_follow_up", "severity", "suggested_symptoms"]
        )
        self.severity_order = list(
            self.meta.get("severity_order") or ["MILD", "MODERATE", "NEEDS_REST"]
        )

        self.interpreter = self._load_interpreter()

    def _load_interpreter(self):
        Interpreter = None
        load_errors: List[str] = []

        for loader in (
            lambda: __import__(
                "tflite_runtime.interpreter", fromlist=["Interpreter"]
            ).Interpreter,
            lambda: __import__(
                "tensorflow.lite.python.interpreter", fromlist=["Interpreter"]
            ).Interpreter,
            lambda: __import__(
                "tensorflow.lite", fromlist=["Interpreter"]
            ).Interpreter,
        ):
            try:
                Interpreter = loader()
                break
            except Exception as exc:
                load_errors.append(str(exc))

        if Interpreter is None:
            raise RuntimeError(
                "Could not load a TFLite interpreter. Install one of:\n"
                "  pip install numpy tensorflow\n"
                "  pip install numpy tflite-runtime\n"
                f"Details: {' | '.join(load_errors[:2])}"
            )

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        interpreter = Interpreter(model_path=str(self.model_path))
        interpreter.allocate_tensors()
        return interpreter

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

        choices = [v for v in self.vocab if v.lower() != "none"]
        close = get_close_matches(underscore, choices, n=1, cutoff=0.86)
        return close[0] if close else underscore

    def symptoms_to_vocab(self, symptoms: Iterable[str]) -> List[str]:
        found: List[str] = []
        for symptom in symptoms:
            mapped = self.normalise_symptom(str(symptom))
            if (
                mapped
                and mapped in self.vocab_to_index
                and mapped.lower() != "none"
                and mapped not in found
            ):
                found.append(mapped)
        return found

    def make_vector(self, vocab_symptoms: List[str]) -> np.ndarray:
        vector = np.zeros((1, self.input_size), dtype=np.float32)
        if not vocab_symptoms and "None" in self.vocab_to_index:
            idx = self.vocab_to_index["None"]
            if idx < self.input_size:
                vector[0, idx] = 1.0
            return vector

        for symptom in vocab_symptoms:
            idx = self.vocab_to_index.get(symptom)
            if idx is not None and 0 <= idx < self.input_size:
                vector[0, idx] = 1.0
        return vector

    def predict(self, symptoms: Iterable[str]) -> TFLiteResult:
        mapped = self.symptoms_to_vocab(symptoms)
        vector = self.make_vector(mapped)

        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()

        self.interpreter.set_tensor(input_details[0]["index"], vector)
        self.interpreter.invoke()

        outputs = [self.interpreter.get_tensor(d["index"]) for d in output_details]
        parsed = self._parse_outputs(outputs)
        parsed.mapped_symptoms = mapped
        return parsed

    def _parse_outputs(self, outputs: Sequence[object]) -> TFLiteResult:
        mapped: Dict[str, object] = {}
        for idx, name in enumerate(self.output_order):
            if idx < len(outputs):
                mapped[name] = outputs[idx]

        confidence = self._scalar(mapped.get("confidence"), 0.55)
        needs_score = self._scalar(mapped.get("needs_follow_up"), 0.0)
        severity = self._severity(mapped.get("severity"))
        suggestions = self._suggestions(mapped.get("suggested_symptoms"))
        needs_follow_up = needs_score >= FOLLOW_UP_THRESHOLD
        if not needs_follow_up:
            suggestions = []

        return TFLiteResult(
            mapped_symptoms=[],
            confidence=confidence,
            needs_follow_up_score=needs_score,
            needs_follow_up=needs_follow_up,
            severity=severity,
            suggested_symptoms=suggestions,
            raw_outputs={k: self._preview(v) for k, v in mapped.items()},
        )

    def _scalar(self, value, default: float) -> float:
        try:
            arr = np.array(value).astype(float).reshape(-1)
            if arr.size == 0:
                return default
            return float(arr[0]) if arr.size == 1 else float(arr.max())
        except Exception:
            return default

    def _severity(self, value) -> str:
        try:
            arr = np.array(value).reshape(-1)
            idx = int(round(float(arr[0]))) if arr.size == 1 else int(np.argmax(arr))
            if 0 <= idx < len(self.severity_order):
                return str(self.severity_order[idx]).upper()
        except Exception:
            pass
        return "MILD"

    def _suggestions(self, value, top_n: int = 4) -> List[str]:
        if value is None:
            return []
        try:
            arr = np.array(value).reshape(-1)
            out: List[str] = []

            if arr.size == len(self.vocab):
                for idx in np.argsort(arr.astype(float))[::-1]:
                    symptom = self.vocab[int(idx)]
                    score = float(arr[int(idx)])
                    if symptom.lower() == "none" or score <= 0.05:
                        if score <= 0.05:
                            break
                        continue
                    if symptom not in out:
                        out.append(symptom)
                    if len(out) >= top_n:
                        break
                return out

            for raw in arr[:20]:
                idx = int(round(float(raw)))
                if 0 <= idx < len(self.vocab):
                    symptom = self.vocab[idx]
                    if symptom.lower() != "none" and symptom not in out:
                        out.append(symptom)
                if len(out) >= top_n:
                    break
            return out
        except Exception:
            return []

    def _preview(self, value):
        arr = np.array(value)
        if arr.size <= 12:
            return arr.tolist()
        return {"shape": list(arr.shape), "preview": arr.reshape(-1)[:10].tolist()}


def _confidence_label(confidence: float) -> str:
    if confidence >= 0.70:
        return "High"
    if confidence >= 0.45:
        return "Medium"
    return "Low"


def print_app_cheatsheet() -> None:
    print("SACA app demo inputs (copy into Android / Windows):\n")
    for i, s in enumerate(APP_DEMO_SCENARIOS, start=1):
        print(f"  {i}. {s.title}")
        print(f"     {s.app_input}\n")
    print("Run locally:  python test.py\n")


def print_result(scenario: Scenario, result: TFLiteResult) -> None:
    print("=" * 72)
    print(f"Scenario: {scenario.id} — {scenario.title}")
    if scenario.notes:
        print(f"Notes:    {scenario.notes}")
    print(f"App text: {scenario.app_input or '(none)'}")
    print(f"Mapped:   {result.mapped_symptoms or ['(None token only)']}")
    print("-" * 72)
    print(f"  confidence          {result.confidence:.3f}  ({_confidence_label(result.confidence)})")
    print(f"  needs_follow_up     {result.needs_follow_up_score:.3f}  -> {result.needs_follow_up}")
    print(f"  severity            {result.severity}")
    if result.needs_follow_up and result.suggested_symptoms:
        print(f"  suggested_symptoms  {', '.join(result.suggested_symptoms)}")
    elif result.needs_follow_up:
        print("  suggested_symptoms  (none above threshold)")
    else:
        print("  suggested_symptoms  (hidden — follow-up not needed)")
    print()


def run_scenario(tester: TFLiteTester, scenario: Scenario) -> TFLiteResult:
    result = tester.predict(scenario.symptoms)
    print_result(scenario, result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test SACA model.tflite scenarios")
    parser.add_argument("--list", action="store_true", help="List preset scenario ids")
    parser.add_argument("--all", action="store_true", help="Run all preset scenarios")
    parser.add_argument("--scenario", type=str, help="Run one preset by id (e.g. mild_cold)")
    parser.add_argument(
        "--symptoms",
        type=str,
        help='Custom comma-separated symptoms, e.g. "fever, cough, chest pain"',
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=DIR,
        help="Folder containing model.tflite, model_meta.json, symptom_vocab.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list:
        print_app_cheatsheet()
        print("Scenario ids (for --scenario):\n")
        for s in SCENARIOS:
            print(f"  {s.id}")
            if s.notes:
                print(f"    -> {s.notes}")
        return 0

    try:
        tester = TFLiteTester(model_dir=args.model_dir)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.symptoms:
        custom = Scenario(
            "custom",
            "Custom input",
            [s.strip() for s in args.symptoms.split(",") if s.strip()],
        )
        run_scenario(tester, custom)
        return 0

    if args.scenario:
        match = next((s for s in SCENARIOS if s.id == args.scenario), None)
        if not match:
            print(f"Unknown scenario '{args.scenario}'. Use --list.", file=sys.stderr)
            return 1
        run_scenario(tester, match)
        return 0

    if args.all or not (args.scenario or args.symptoms):
        print_app_cheatsheet()
        print("Running all 7 app demo scenarios against model.tflite:\n")
        for s in APP_DEMO_SCENARIOS:
            run_scenario(tester, s)
        print("Copy any 'App text' line above into mobile/desktop and compare results.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
