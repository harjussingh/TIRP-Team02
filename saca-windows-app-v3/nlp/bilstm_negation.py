"""
Bi-LSTM Negation Classifier
-----------------------------
A lightweight Bidirectional LSTM that learns negation scope from synthetically
generated training data.  It supplements (not replaces) the rule-based
negation detector in negation_detector.py.

Architecture
------------
Input  : Fixed-length token sequence (MAX_LEN=32).
         Symptom tokens are wrapped with special [SYM_S] / [SYM_E] markers
         so the model knows exactly which span to classify.
Encoder: Embedding(vocab, 64) → BiLSTM(64, layers=2) → mean-pool
Head   : Dropout(0.3) → Linear(128, 1) → Sigmoid
Output : P(negated | context, symptom) ∈ [0, 1]

Training data
-------------
~2 400 synthetic (sentence, symptom, label) triples covering:
  • Simple present         "I have {s}"
  • Simple negation        "I do not have {s}", "no {s}", "without {s}"
  • Scope-reset present    "no {s2} but I have {s}"  → {s} is PRESENT
  • Scope-reset negation   "I have {s2} but no {s}"  → {s} is NEGATED
  • Double negation        "not without {s}"          → {s} is PRESENT
  • Kriol patterns         "mi garr {s}", "mi no garr {s}"
  • Medical phrasing       "patient denies {s}", "no evidence of {s}"

Singleton pattern
-----------------
Model is trained once on first import and cached in memory.
Weights are also saved to models/bilstm_negation.pt so subsequent
process starts skip retraining (~0.1 s load vs ~2 s train).

Public API
----------
    bilstm_is_negated(sentence: str, symptom: str) -> float
        Returns probability that `symptom` is negated in `sentence`.
        Typical threshold: 0.50 (soft) or 0.80 (high-confidence override).
"""

from __future__ import annotations

import json
import os
import random
import re
from typing import Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_MODEL_DIR = os.path.join(_ROOT, "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "bilstm_negation.pt")
_VOCAB_PATH = os.path.join(_MODEL_DIR, "bilstm_vocab.json")

# ---------------------------------------------------------------------------
# Hyper-parameters
# ---------------------------------------------------------------------------
MAX_LEN = 32          # tokens per training / inference window
EMB_DIM = 64
HIDDEN_DIM = 64
NUM_LAYERS = 2
DROPOUT = 0.30
EPOCHS = 20
LR = 1e-3
BATCH_SIZE = 64
OVERRIDE_THRESHOLD = 0.82   # Bi-LSTM must reach this to override rules

# Special tokens
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"
SYM_S = "<SYM_S>"   # symptom span start
SYM_E = "<SYM_E>"   # symptom span end

# ---------------------------------------------------------------------------
# Canonical symptoms (used in synthetic data generation)
# ---------------------------------------------------------------------------
_SYMPTOMS = [
    "fever", "cough", "headache", "chest pain", "shortness of breath",
    "vomiting", "diarrhoea", "abdominal pain", "dizziness", "sore throat",
    "nausea", "fatigue", "insomnia", "runny nose", "back pain", "ear pain",
    "eye pain", "toothache", "swelling", "itching", "muscle pain",
    "bleeding", "sweating", "shivering", "loss of appetite",
    "joint pain", "shoulder pain",
]


# ---------------------------------------------------------------------------
# Synthetic training data
# ---------------------------------------------------------------------------

def _pick_other(sym: str) -> str:
    """Return a random symptom that is NOT sym."""
    others = [s for s in _SYMPTOMS if s != sym]
    return random.choice(others)


def generate_training_data() -> List[Tuple[str, str, int]]:
    """
    Generate (sentence, symptom, label) triples.
    label=0 → present, label=1 → negated.
    """
    random.seed(42)
    data: List[Tuple[str, str, int]] = []

    # ── PRESENT templates (label = 0) ─────────────────────────────────────
    present_templates = [
        "I have {s}",
        "I am experiencing {s}",
        "I feel {s}",
        "I suffer from {s}",
        "I have been having {s}",
        "I developed {s}",
        "I still have {s}",
        "I noticed {s}",
        "I am having {s}",
        "patient has {s}",
        "patient reports {s}",
        "patient complains of {s}",
        "she has {s}",
        "he has {s}",
        "they have {s}",
        "I woke up with {s}",
        "started experiencing {s}",
        "I have had {s} for three days",
        "I have had {s} since yesterday",
        "I am dealing with {s}",
        # scope-reset: {s2} negated but {s} is present
        "no {s2} but I have {s}",
        "no {s2} however I do have {s}",
        "I don't have {s2} but I have {s}",
        "I don't have {s2} but I do have {s}",
        "without {s2} but with {s}",
        "I have {s2} but also {s}",
        "I had {s2} but now I have {s}",
        "{s2} is gone but {s} remains",
        "no {s2} although I do have {s}",
        "patient denies {s2} but reports {s}",
        # multi-symptom with target present
        "I have {s} and {s2}",
        "I have {s2} and {s}",
        "I have {s} as well as {s2}",
        # Kriol present
        "mi garr {s}",
        "mi fil {s}",
        "mi garr {s} en {s2}",
        "bat mi garr {s}",
        # double negation → present
        "not without {s}",
        "I cannot deny having {s}",
    ]

    for template in present_templates:
        for s in _SYMPTOMS:
            s2 = _pick_other(s)
            sentence = template.format(s=s, s2=s2)
            data.append((sentence, s, 0))

    # ── NEGATED templates (label = 1) ──────────────────────────────────────
    negated_templates = [
        "I do not have {s}",
        "I don't have {s}",
        "no {s}",
        "I have no {s}",
        "I am not experiencing {s}",
        "I am not having {s}",
        "I never had {s}",
        "without {s}",
        "I lack {s}",
        "I deny {s}",
        "patient denies {s}",
        "no evidence of {s}",
        "no signs of {s}",
        "no history of {s}",
        "I haven't had {s}",
        "I had no {s}",
        "there is no {s}",
        "no complaint of {s}",
        "not complaining of {s}",
        "she does not have {s}",
        "he does not have {s}",
        "they do not have {s}",
        "I don't notice {s}",
        "I have not noticed {s}",
        "absent {s}",
        "{s} absent",
        "{s} is absent",
        "{s} is not present",
        "{s} not present",
        # scope-reset: target {s} negated after 'but'
        "I have {s2} but no {s}",
        "I have {s2} but not {s}",
        "I have {s2} however I do not have {s}",
        "I feel {s2} but I don't have {s}",
        "{s2} is present but {s} is not",
        "I have {s2} but I am not experiencing {s}",
        "I have {s2} but without {s}",
        # Kriol negated
        "mi no garr {s}",
        "mi nomo garr {s}",
        "mi nat garr {s}",
        "mi no fil {s}",
        "mi no garr {s} bat mi garr {s2}",
    ]

    for template in negated_templates:
        for s in _SYMPTOMS:
            s2 = _pick_other(s)
            sentence = template.format(s=s, s2=s2)
            data.append((sentence, s, 1))

    random.shuffle(data)
    return data


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

def build_vocab(data: List[Tuple[str, str, int]]) -> Dict[str, int]:
    """Build word → index vocabulary from all sentences + special tokens."""
    vocab: Dict[str, int] = {PAD_TOKEN: 0, UNK_TOKEN: 1, SYM_S: 2, SYM_E: 3}
    for sentence, symptom, _ in data:
        for word in sentence.lower().split():
            if word not in vocab:
                vocab[word] = len(vocab)
        for word in symptom.lower().split():
            if word not in vocab:
                vocab[word] = len(vocab)
    return vocab


def encode(sentence: str, symptom: str, vocab: Dict[str, int]) -> List[int]:
    """
    Encode a (sentence, symptom) pair as a fixed-length integer sequence.

    The symptom span is wrapped with SYM_S / SYM_E markers so the model
    knows exactly which region to assess for negation.
    """
    s_lower = sentence.lower()
    sym_lower = symptom.lower()

    # Insert markers around symptom span (first occurrence)
    marked = s_lower.replace(sym_lower, f"{SYM_S} {sym_lower} {SYM_E}", 1)
    tokens = marked.split()

    # Convert to indices
    indices = [vocab.get(t, vocab[UNK_TOKEN]) for t in tokens]

    # Truncate or pad to MAX_LEN
    if len(indices) >= MAX_LEN:
        indices = indices[:MAX_LEN]
    else:
        indices += [vocab[PAD_TOKEN]] * (MAX_LEN - len(indices))

    return indices


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class BiLSTMNegation(nn.Module):
    """
    Bidirectional LSTM negation classifier.

    Reads a context window (symptom wrapped in SYM_S/SYM_E markers) and
    outputs P(negated) ∈ [0, 1].
    """

    def __init__(self, vocab_size: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, EMB_DIM, padding_idx=0)
        self.bilstm = nn.LSTM(
            input_size=EMB_DIM,
            hidden_size=HIDDEN_DIM,
            num_layers=NUM_LAYERS,
            batch_first=True,
            bidirectional=True,
            dropout=DROPOUT if NUM_LAYERS > 1 else 0.0,
        )
        self.dropout = nn.Dropout(DROPOUT)
        self.classifier = nn.Linear(HIDDEN_DIM * 2, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (batch, MAX_LEN) → (batch,) logits"""
        emb = self.embedding(x)                  # (B, L, EMB)
        out, _ = self.bilstm(emb)                # (B, L, 2*H)
        pooled = out.mean(dim=1)                 # (B, 2*H)
        pooled = self.dropout(pooled)
        return self.classifier(pooled).squeeze(-1)  # (B,)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def _train_model(
    data: List[Tuple[str, str, int]],
    vocab: Dict[str, int],
) -> BiLSTMNegation:
    """Train the BiLSTM on synthetic data and return the trained model."""
    # Encode all examples
    X = torch.tensor(
        [encode(s, sym, vocab) for s, sym, _ in data], dtype=torch.long
    )
    y = torch.tensor([label for _, _, label in data], dtype=torch.float)

    # 90 / 10 train / val split
    n = len(data)
    split = int(n * 0.9)
    X_tr, X_val = X[:split], X[split:]
    y_tr, y_val = y[:split], y[split:]

    model = BiLSTMNegation(len(vocab))
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    loss_fn = nn.BCEWithLogitsLoss()

    best_val_loss = float("inf")
    best_state: Optional[dict] = None

    for epoch in range(EPOCHS):
        model.train()
        # Mini-batch training
        perm = torch.randperm(len(X_tr))
        X_tr, y_tr = X_tr[perm], y_tr[perm]

        for start in range(0, len(X_tr), BATCH_SIZE):
            xb = X_tr[start:start + BATCH_SIZE]
            yb = y_tr[start:start + BATCH_SIZE]
            optimizer.zero_grad()
            logits = model(xb)
            loss = loss_fn(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        # Validation
        model.eval()
        with torch.no_grad():
            val_logits = model(X_val)
            val_loss = loss_fn(val_logits, y_val).item()
            val_preds = (torch.sigmoid(val_logits) > 0.5).float()
            val_acc = (val_preds == y_val).float().mean().item()

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

        if (epoch + 1) % 5 == 0:
            print(f"  [BiLSTM] epoch {epoch+1:>2}/{EPOCHS}  "
                  f"val_loss={val_loss:.4f}  val_acc={val_acc:.1%}")

    if best_state is not None:
        model.load_state_dict(best_state)

    model.eval()
    return model


# ---------------------------------------------------------------------------
# Singleton — load or train once per process
# ---------------------------------------------------------------------------

_model: Optional[BiLSTMNegation] = None
_vocab: Optional[Dict[str, int]] = None


def _get_model() -> Tuple[BiLSTMNegation, Dict[str, int]]:
    """Return (model, vocab), training or loading from disk as needed."""
    global _model, _vocab

    if _model is not None and _vocab is not None:
        return _model, _vocab

    os.makedirs(_MODEL_DIR, exist_ok=True)

    # Try loading saved weights
    if os.path.exists(_MODEL_PATH) and os.path.exists(_VOCAB_PATH):
        with open(_VOCAB_PATH) as f:
            vocab = json.load(f)
        model = BiLSTMNegation(len(vocab))
        model.load_state_dict(
            torch.load(_MODEL_PATH, map_location="cpu", weights_only=True)
        )
        model.eval()
        _model, _vocab = model, vocab
        return _model, _vocab

    # Train from scratch
    print("[BiLSTM] Training negation model on synthetic data...")
    data = generate_training_data()
    vocab = build_vocab(data)
    model = _train_model(data, vocab)
    print(f"[BiLSTM] Training complete. Vocab size: {len(vocab)}")

    # Save for future runs
    torch.save(model.state_dict(), _MODEL_PATH)
    with open(_VOCAB_PATH, "w") as f:
        json.dump(vocab, f)
    print(f"[BiLSTM] Model saved to {_MODEL_PATH}")

    _model, _vocab = model, vocab
    return _model, _vocab


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@torch.no_grad()
def bilstm_is_negated(sentence: str, symptom: str) -> float:
    """
    Return the probability that `symptom` is negated in `sentence`.

    Values above OVERRIDE_THRESHOLD (0.82) indicate high-confidence negation
    and can be used to override rule-based decisions.

    Args:
        sentence: The (preprocessed, synonym-mapped) input text.
        symptom:  A canonical symptom string (must appear in sentence).

    Returns:
        Float in [0, 1] — probability of negation.
        Returns 0.5 (uncertain) if the symptom string is not found in the
        sentence so no marker can be inserted.
    """
    model, vocab = _get_model()

    # Guard: symptom must be present in sentence for markers to work
    if symptom.lower() not in sentence.lower():
        return 0.5  # uncertain

    indices = encode(sentence, symptom, vocab)
    x = torch.tensor([indices], dtype=torch.long)  # (1, MAX_LEN)
    logit = model(x)
    return float(torch.sigmoid(logit).item())
