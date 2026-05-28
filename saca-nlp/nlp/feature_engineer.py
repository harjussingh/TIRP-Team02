"""
Feature Engineering Module
---------------------------
Converts the structured output of run_pipeline() into a flat feature vector
ready for the ML severity-prediction module.

Feature groups
--------------
1. Symptom presence flags  (27 binary features, one per canonical symptom)
   symptom_present_<name>  = 1 if symptom is present, 0 otherwise

2. Symptom negation flags  (27 binary features)
   symptom_negated_<name>  = 1 if symptom was explicitly negated, 0 otherwise

3. Aggregate symptom counts
   symptom_count           = number of present symptoms
   negated_count           = number of negated symptoms
   has_negations           = 1 if any negations exist, 0 otherwise

4. Weighted severity score
   severity_score          = sum of per-symptom severity weights for PRESENT
                             symptoms (weights sourced from clinical triage
                             literature — higher = more urgent)
   max_severity            = weight of the single most severe present symptom
   severity_category       = "low" / "medium" / "high" / "emergency"

5. Linguistic / pipeline metadata
   detected_language       = 0 (english) / 1 (kriol) / 2 (mixed)
   language_confidence     = float [0, 1]
   oov_ratio               = fraction of words not in Kriol dictionary
   input_length            = token count of cleaned input
   translation_applied     = 1 if Kriol → English translation ran, 0 otherwise
   bert_suggestions_count  = number of BERT advisory suggestions (present)

6. Symptom embedding (768-dim)
   embedding_<0..767>      = mean of BioClinicalBERT embeddings of present
                             symptom names; zero vector if no symptoms present.
                             This gives the ML module a dense semantic
                             representation of the symptom combination.

Output
------
Returns a dict with all features. Keys are stable strings so downstream
models can be retrained without schema changes.

Public API
----------
    engineer_features(pipeline_result: dict) -> dict
"""

from __future__ import annotations

import re
from typing import Dict, List

import torch
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# Symptom severity weights (clinical triage scale 1–10)
# Sources: CTAS (Canadian Triage & Acuity Scale) and
#          ATS (Australasian Triage Scale) symptom urgency mappings.
# ---------------------------------------------------------------------------
SEVERITY_WEIGHTS: Dict[str, float] = {
    # Emergency / immediately life-threatening
    "shortness of breath":  9.5,
    "chest pain":           9.5,
    "bleeding":             9.0,

    # High urgency
    "fever":                7.5,
    "vomiting":             6.5,
    "diarrhoea":            6.0,
    "dizziness":            6.0,
    "abdominal pain":       6.5,
    "shivering":            6.0,
    "sweating":             5.5,
    "swelling":             5.5,
    "fatigue":              5.0,
    "loss of appetite":     5.0,

    # Moderate
    "headache":             5.0,
    "nausea":               5.0,
    "cough":                4.5,
    "sore throat":          4.0,
    "back pain":            4.5,
    "muscle pain":          4.5,
    "joint pain":           4.5,
    "shoulder pain":        4.0,

    # Low urgency
    "runny nose":           3.0,
    "ear pain":             3.5,
    "eye pain":             3.5,
    "toothache":            3.0,
    "itching":              2.5,
    "insomnia":             2.5,
}

# Severity category thresholds (sum of weights for present symptoms)
_CAT_EMERGENCY = 18.0
_CAT_HIGH      = 10.0
_CAT_MEDIUM    =  5.0


# ---------------------------------------------------------------------------
# Language encoding
# ---------------------------------------------------------------------------
_LANG_ENCODE = {"english": 0, "kriol": 1, "mixed": 2}


# ---------------------------------------------------------------------------
# Symptom embedding (reuse BioClinicalBERT via bert_extractor singleton)
# ---------------------------------------------------------------------------
def _get_symptom_embedding(symptom_names: List[str]) -> List[float]:
    """
    Return the mean BioClinicalBERT embedding (768-dim) of the given symptom
    names.  Returns a zero vector if the list is empty.

    Reuses the already-loaded model from bert_extractor to avoid double-loading.
    """
    if not symptom_names:
        return [0.0] * 768

    from nlp.bert_extractor import _encode as bert_encode
    embs = bert_encode(symptom_names)          # (N, 768) normalised
    mean_emb = embs.mean(dim=0)                # (768,)
    mean_emb = F.normalize(mean_emb, p=2, dim=0)
    return mean_emb.tolist()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def engineer_features(pipeline_result: dict) -> dict:
    """
    Convert a run_pipeline() result dict into a flat ML feature dict.

    Args:
        pipeline_result: The dict returned by main.run_pipeline().

    Returns:
        A flat dict of feature_name → value.  All keys are always present
        (zero / default values used when data is absent) so the downstream
        model always receives a fixed-length input.
    """
    present:  List[str] = pipeline_result.get("symptoms_present", [])
    negated:  List[str] = pipeline_result.get("symptoms_negated", [])
    all_syms: List[str] = list(SEVERITY_WEIGHTS.keys())  # stable 27-symptom order

    features: dict = {}

    # ── 1. Per-symptom presence & negation flags ───────────────────────────
    for sym in all_syms:
        safe = sym.replace(" ", "_")
        features[f"symptom_present_{safe}"] = int(sym in present)
        features[f"symptom_negated_{safe}"] = int(sym in negated)

    # ── 2. Aggregate counts ────────────────────────────────────────────────
    features["symptom_count"]  = len(present)
    features["negated_count"]  = len(negated)
    features["has_negations"]  = int(len(negated) > 0)

    # ── 3. Severity scoring ────────────────────────────────────────────────
    weights = [SEVERITY_WEIGHTS.get(s, 3.0) for s in present]
    total_severity = sum(weights)
    max_severity   = max(weights, default=0.0)

    if total_severity >= _CAT_EMERGENCY:
        severity_category = "emergency"
    elif total_severity >= _CAT_HIGH:
        severity_category = "high"
    elif total_severity >= _CAT_MEDIUM:
        severity_category = "medium"
    else:
        severity_category = "low"

    features["severity_score"]    = round(total_severity, 2)
    features["max_severity"]      = round(max_severity, 2)
    features["severity_category"] = severity_category

    # ── 4. Linguistic / pipeline metadata ─────────────────────────────────
    lang_raw = pipeline_result.get("detected_language", "english")
    features["detected_language"]    = _LANG_ENCODE.get(lang_raw, 0)
    features["language_confidence"]  = round(
        float(pipeline_result.get("language_confidence", 1.0)), 4
    )
    features["oov_ratio"]            = round(
        float(pipeline_result.get("oov_ratio", 0.0)), 4
    )

    cleaned_text: str = pipeline_result.get("cleaned_text", "")
    features["input_length"] = len(cleaned_text.split())

    method = pipeline_result.get("translation_method", "passthrough")
    features["translation_applied"] = int(method != "passthrough")

    bert_hints = pipeline_result.get("bert_suggestions", {}).get("present", [])
    features["bert_suggestions_count"] = len(bert_hints)

    # ── 5. Symptom embedding (768-dim) ─────────────────────────────────────
    embedding = _get_symptom_embedding(present)
    for i, val in enumerate(embedding):
        features[f"embedding_{i}"] = round(val, 6)

    return features


# ---------------------------------------------------------------------------
# Human-readable summary (for debugging / supervisor demo)
# ---------------------------------------------------------------------------
def summarise_features(features: dict) -> str:
    """Return a compact multi-line summary of the most important features."""
    lang_map = {0: "english", 1: "kriol", 2: "mixed"}
    lines = [
        "── Feature Engineering Summary ──────────────────────────",
        f"  Present symptoms   : {features['symptom_count']}",
        f"  Negated symptoms   : {features['negated_count']}",
        f"  Severity score     : {features['severity_score']}  "
        f"(max single: {features['max_severity']})",
        f"  Severity category  : {features['severity_category'].upper()}",
        f"  Language           : {lang_map.get(features['detected_language'], '?')} "
        f"({features['language_confidence']:.0%} confidence)",
        f"  OOV ratio          : {features['oov_ratio']:.1%}",
        f"  Input length       : {features['input_length']} tokens",
        f"  Translation applied: {'yes' if features['translation_applied'] else 'no'}",
        f"  BERT suggestions   : {features['bert_suggestions_count']}",
        f"  Embedding          : 768-dim vector (first 4: "
        f"[{features['embedding_0']:.3f}, {features['embedding_1']:.3f}, "
        f"{features['embedding_2']:.3f}, {features['embedding_3']:.3f} …])",
        "─────────────────────────────────────────────────────────",
    ]

    # Show which symptoms are flagged
    all_syms = list(SEVERITY_WEIGHTS.keys())
    present_flags = [s for s in all_syms
                     if features.get(f"symptom_present_{s.replace(' ','_')}")]
    negated_flags = [s for s in all_syms
                     if features.get(f"symptom_negated_{s.replace(' ','_')}")]
    if present_flags:
        lines.append(f"  Present flags      : {present_flags}")
    if negated_flags:
        lines.append(f"  Negated flags      : {negated_flags}")

    return "\n".join(lines)
