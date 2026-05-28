"""
BioClinicalBERT Semantic Symptom Extractor
-------------------------------------------
Uses emilyalsentzer/Bio_ClinicalBERT to detect symptoms via semantic
similarity rather than exact phrase matching. This catches novel clinical
descriptions that the PhraseMatcher + synonym dictionary cannot handle
(e.g. "pyrexia" → fever, "emesis" → vomiting, "myalgia" → muscle pain).

Strategy:
1. Split input text into clauses (by punctuation and conjunctions).
2. Encode each clause and each symptom DESCRIPTION (rich multi-phrase anchor)
   with Bio_ClinicalBERT (mean-pool over last hidden states).
3. For each clause, compute cosine similarity against all symptom anchors.
4. Accept a detection only if:
   a. The best-matching symptom scores >= SIMILARITY_THRESHOLD, AND
   b. Its score beats the second-best by >= MARGIN_GAP.
   This top-1 argmax + margin approach eliminates false positives caused by
   the dense clustering of medical terms in the base model's embedding space.

Architecture note:
   The base Bio_ClinicalBERT encoder (emilyalsentzer/Bio_ClinicalBERT) is a
   masked language model pre-trained on clinical notes. When used as a raw
   sentence encoder via mean-pooling, all 27 symptom names cluster within
   cosine distance 0.75–0.88 of each other, making threshold-only detection
   unreliable. The rich anchor descriptions + margin gap strategy improves
   precision significantly. Full fine-tuning on a labelled symptom dataset
   would further improve recall.

Singleton pattern: model and symptom embeddings are loaded once per process.
"""

import re
from typing import List, Tuple, Optional
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_NAME = "emilyalsentzer/Bio_ClinicalBERT"

# Minimum cosine similarity for the BEST-matching symptom to be accepted.
# 0.90 — set high to avoid false positives from closely-clustered medical terms.
# Calibration data (10 novel medical synonyms) shows wrong-winner scores peak at
# ~0.905 (emesis→nausea) and ~0.865 (arthralgia→shoulder pain). Setting the bar
# at 0.90 suppresses most wrong-winner false positives while still catching very
# clear cases like "loose watery bowel movements" → diarrhoea (0.911).
SIMILARITY_THRESHOLD = 0.91

# The winning symptom must also beat the second-best by this margin.
# Calibration shows correct-winner margin gaps range 0.001–0.026, so 0.01
# is sufficient to eliminate ties while accepting genuine near-miss wins.
MARGIN_GAP = 0.01

# Rich multi-phrase anchor descriptions for each canonical symptom.
# Using verbose descriptions spreads the embedding vectors further apart
# in the BioClinicalBERT embedding space, improving discrimination.
SYMPTOM_DESCRIPTIONS = {
    "fever":               "high fever elevated body temperature pyrexia febrile hot feeling chills feverish",
    "cough":               "coughing dry cough chesty cough persistent cough respiratory cough tussis",
    "headache":            "headache head pain cephalgia migraine throbbing head pressure in head",
    "chest pain":          "chest pain thoracic pain cardiac pain angina chest tightness sternum pain",
    "shortness of breath": "shortness of breath dyspnoea breathlessness difficulty breathing unable to breathe",
    "vomiting":            "vomiting throwing up emesis being sick regurgitation projectile vomiting",
    "diarrhoea":           "diarrhoea loose watery stools frequent bowel movements gastroenteritis stomach bug",
    "abdominal pain":      "abdominal pain stomach ache belly pain gastric pain intestinal cramps lower abdomen",
    "dizziness":           "dizziness lightheadedness vertigo spinning sensation unsteady balance problems",
    "sore throat":         "sore throat pharyngeal pain throat pain difficulty swallowing painful swallowing",
    "nausea":              "nausea nauseated feeling queasy feeling sick wanting to vomit unsettled stomach",
    "fatigue":             "fatigue exhaustion extreme tiredness weakness lethargy no energy feeling drained",
    "insomnia":            "insomnia cannot sleep sleeplessness sleep disturbance waking at night poor sleep",
    "runny nose":          "runny nose nasal discharge rhinorrhoea congestion sniffling stuffy nose blocked nose",
    "back pain":           "back pain lumbar pain spinal pain lower back ache backache dorsal pain",
    "ear pain":            "ear pain earache otalgia ear infection ear discomfort painful ear",
    "eye pain":            "eye pain ocular pain sore eyes eye discomfort painful eye ophthalmia",
    "toothache":           "toothache dental pain tooth pain sore teeth dental abscess tooth ache",
    "swelling":            "swelling oedema swollen limbs fluid retention puffy swollen tissue inflammation",
    "itching":             "itching pruritus itchy skin skin irritation rash scratching urticaria",
    "muscle pain":         "muscle pain myalgia sore muscles muscle ache muscle cramps muscle soreness",
    "bleeding":            "bleeding haemorrhage blood loss losing blood haemostasis blood coming out",
    "sweating":            "sweating diaphoresis night sweats profuse sweating hyperhidrosis excessive perspiration",
    "shivering":           "shivering chills rigor trembling shaking feeling cold body shakes",
    "loss of appetite":    "loss of appetite anorexia not hungry cannot eat off food reduced appetite",
    "joint pain":          "joint pain arthralgia sore joints articular pain knee pain ankle pain hip pain",
    "shoulder pain":       "shoulder pain sore shoulder rotator cuff pain glenohumeral pain shoulder ache",
}

# Negation words — if a clause contains one of these, BERT detections in
# that clause are treated as negated (mirrors rule-based logic).
NEGATION_WORDS = {
    "no", "not", "without", "never", "none", "neither", "nor",
    "cannot", "can't", "don't", "doesn't", "didn't", "haven't",
    "hasn't", "hadn't", "won't", "wouldn't", "deny", "denies",
    "lack", "absent"
}

# Scope-reset words — after these, negation in previous clause does not carry.
SCOPE_RESET_WORDS = {"but", "however", "although", "though", "yet", "except"}


# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------
_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModel] = None
_symptom_embeddings: Optional[dict] = None   # {symptom: tensor}
_last_symptom_list: Optional[list] = None


def _get_model():
    """Lazy-load tokenizer and model (once per process)."""
    global _tokenizer, _model
    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModel.from_pretrained(MODEL_NAME)
        _model.eval()
    return _tokenizer, _model


def _mean_pool(token_embeddings: torch.Tensor,
               attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean-pool token embeddings, ignoring padding tokens."""
    mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    summed = torch.sum(token_embeddings * mask_expanded, dim=1)
    counts = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
    return summed / counts


@torch.no_grad()
def _encode(texts: List[str]) -> torch.Tensor:
    """Encode a list of strings → normalised sentence embeddings [N, hidden]."""
    tokenizer, model = _get_model()
    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=128,
        return_tensors="pt"
    )
    outputs = model(**encoded)
    embeddings = _mean_pool(outputs.last_hidden_state, encoded["attention_mask"])
    return F.normalize(embeddings, p=2, dim=1)


def _build_symptom_embeddings(symptoms: List[str]) -> dict:
    """
    Compute and cache symptom embeddings using rich descriptive anchor phrases.
    Re-computed if symptom list changes.

    Each symptom is represented by its SYMPTOM_DESCRIPTIONS entry (verbose multi-
    phrase text) rather than its bare name. This spreads the 27 symptom vectors
    further apart in the embedding space, reducing false positive collisions.
    Falls back to the symptom name if no description is defined.
    """
    global _symptom_embeddings, _last_symptom_list
    if _symptom_embeddings is None or symptoms != _last_symptom_list:
        anchors = [SYMPTOM_DESCRIPTIONS.get(sym, sym) for sym in symptoms]
        embs = _encode(anchors)
        _symptom_embeddings = {sym: embs[i] for i, sym in enumerate(symptoms)}
        _last_symptom_list = list(symptoms)
    return _symptom_embeddings


# ---------------------------------------------------------------------------
# Clause splitting
# ---------------------------------------------------------------------------
def _split_clauses(text: str) -> List[Tuple[str, bool]]:
    """
    Split text into (clause_text, is_negated) tuples.

    Splits on: commas, semicolons, 'and', 'but', 'or', 'however'.
    Tracks scope-reset words so post-'but' clauses reset the negation state.

    Returns list of (clause, is_negated).
    """
    # Split on clause boundaries
    raw_clauses = re.split(r'[,;]|\b(and|but|however|although|though|yet|except)\b', text)
    clauses = [c.strip() for c in raw_clauses if c and c.strip()]

    results: List[Tuple[str, bool]] = []
    negated_scope = False  # whether the *previous* scope-reset reset negation

    for clause in clauses:
        words = clause.lower().split()

        # Check if this clause starts a new scope (after 'but' etc.)
        if words and words[0] in SCOPE_RESET_WORDS:
            negated_scope = False   # new scope — start fresh
            words = words[1:]       # drop the reset word itself

        # Determine if this clause is locally negated
        is_negated = any(w in NEGATION_WORDS for w in words)
        results.append((clause, is_negated))

    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def bert_extract_symptoms(
    text: str,
    symptoms: List[str],
    already_found: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Semantic symptom extraction using Bio_ClinicalBERT.

    Detects symptoms in *text* that are NOT already in *already_found*
    by computing cosine similarity between clause embeddings and symptom
    embeddings.

    Args:
        text:          Translated + synonym-mapped text.
        symptoms:      Full canonical symptom list.
        already_found: Symptoms already detected by PhraseMatcher (excluded
                       from search to avoid duplicates, but used for context).

    Returns:
        Tuple of (new_present, new_negated) — symptoms found ONLY by BERT.
    """
    symptom_embs = _build_symptom_embeddings(symptoms)
    clauses = _split_clauses(text)

    # Symptoms still to find (PhraseMatcher didn't get them)
    remaining = [s for s in symptoms if s not in already_found]
    if not remaining:
        return [], []

    new_present: List[str] = []
    new_negated: List[str] = []
    found_set = set()

    for clause_text, clause_is_negated in clauses:
        if not clause_text.strip():
            continue

        # Encode this clause
        clause_emb = _encode([clause_text])[0]  # shape: [hidden]

        # Compute similarity against all remaining (unfound) symptoms at once
        remaining_unfound = [s for s in remaining if s not in found_set]
        if not remaining_unfound:
            break

        sims = [
            (float(torch.dot(clause_emb, symptom_embs[sym])), sym)
            for sym in remaining_unfound
        ]
        sims.sort(reverse=True)

        best_score, best_sym = sims[0]
        second_score = sims[1][0] if len(sims) > 1 else 0.0

        # Accept detection only if:
        #   1. Best score meets threshold (base similarity bar)
        #   2. Best score beats second-best by MARGIN_GAP (discrimination check)
        # This prevents accepting a detection when multiple symptoms cluster
        # at similar similarity scores — a key failure mode of the base model.
        if best_score >= SIMILARITY_THRESHOLD and (best_score - second_score) >= MARGIN_GAP:
            found_set.add(best_sym)
            if clause_is_negated:
                new_negated.append(best_sym)
            else:
                new_present.append(best_sym)

    return new_present, new_negated
