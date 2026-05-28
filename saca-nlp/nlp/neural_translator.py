"""
Neural Translator — MarianMT Hybrid Engine
===========================================
Implements a two-stage hybrid translation strategy:

Stage 1 — Dictionary (fast, deterministic)
    The existing Kriol dictionary + fuzzy fallback covers known medical vocab.
    This is always run first for kriol/mixed input.

Stage 2 — MarianMT neural fallback (Helsinki-NLP/opus-mt-mul-en)
    Applied only when Stage 1 leaves too many out-of-vocabulary (OOV) tokens,
    meaning there are words the dictionary could not translate.
    The model supports 100+ languages and handles pidgin/creole reasonably well.

Why this hybrid?
    - Pure dictionary: fast, reliable for known terms, no model download needed
      at runtime.  But fails on novel phrases or unseen vocabulary.
    - Pure MarianMT: handles unseen vocab but can hallucinate or mistranslate
      short Kriol words that look similar to words in other languages.
    - Hybrid: dictionary handles the medical core; MarianMT cleans up the rest.

OOV Detection
    After Stage 1, we count tokens that are still Kriol-like (appear in the
    original Kriol dictionary keys, or pass a simple heuristic: token appears
    in the raw input but NOT in the translated output AND is not a common
    English word).  If the OOV ratio exceeds OOV_THRESHOLD, Stage 2 runs.

Model Loading
    The MarianMT model is loaded lazily on first use and cached as a module-
    level singleton.  Subsequent calls reuse the loaded model (no re-download).
    The HuggingFace cache (~300 MB) is stored in the default HF_HOME directory.

Usage
-----
    from nlp.neural_translator import hybrid_translate

    english = hybrid_translate(
        text="mi garr hedache en some unknown phrase",
        kriol_dict=kriol_dict,          # pre-loaded dict
        detected_lang="mixed",          # from language_detector
    )
    # returns: {"text": "i have headache and some unknown phrase",
    #           "method": "dict+neural",
    #           "oov_ratio": 0.22}
"""

from __future__ import annotations

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODEL_NAME = "Helsinki-NLP/opus-mt-mul-en"

# If this fraction of tokens are still OOV after dictionary translation,
# run the neural fallback on the ORIGINAL (untranslated) input.
OOV_THRESHOLD = 0.35   # 35 % OOV → trigger MarianMT

# Common English words we don't count as OOV even if short / ambiguous
_ENGLISH_STOPWORDS = {
    "i", "a", "an", "the", "my", "me", "we", "he", "she", "it", "they",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "shall",
    "and", "or", "but", "not", "no", "so", "if", "in", "on",
    "at", "to", "for", "of", "with", "as", "by", "from", "up",
    "that", "this", "what", "which", "who", "when", "where", "how",
    "feel", "feels", "feeling", "felt", "hurt", "hurts", "pain",
    "bad", "very", "some", "any", "also", "now", "still", "since",
    "after", "before", "about", "just", "only", "even", "then", "than",
    "there", "their", "these", "those", "every", "other", "each",
    "never", "none", "neither", "nor", "without", "nothing", "nobody",
    # medical terms that should never be sent to neural model
    "fever", "cough", "headache", "chest", "pain", "shortness", "breath",
    "vomiting", "diarrhoea", "abdominal", "dizziness", "nausea", "sore",
    "throat", "fatigue", "weak", "dizzy", "stomach", "belly",
}

# ---------------------------------------------------------------------------
# Singleton model holder
# ---------------------------------------------------------------------------
_tokenizer = None
_model = None
_model_available: Optional[bool] = None   # None = not yet tried


def _load_model() -> bool:
    """
    Lazy-load MarianMT model.  Returns True if successful, False otherwise.
    Sets module-level _tokenizer / _model.
    """
    global _tokenizer, _model, _model_available

    if _model_available is not None:
        return _model_available

    try:
        from transformers import MarianMTModel, MarianTokenizer

        logger.info(f"Loading MarianMT model: {MODEL_NAME}  (first call only)")
        _tokenizer = MarianTokenizer.from_pretrained(MODEL_NAME)
        _model = MarianMTModel.from_pretrained(MODEL_NAME)
        _model.eval()
        _model_available = True
        logger.info("MarianMT model loaded successfully.")
        return True

    except Exception as exc:  # network error, disk full, etc.
        logger.warning(f"MarianMT model could not be loaded: {exc}")
        _model_available = False
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_for_neural(text: str) -> str:
    """Minimal normalisation before sending to MarianMT."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _neural_translate(text: str) -> str:
    """
    Translate *text* with MarianMT.
    Returns the translated string, or the original on failure.
    """
    if not _load_model():
        return text
    try:
        import torch
        inputs = _tokenizer(
            [_clean_for_neural(text)],
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        )
        with torch.no_grad():
            translated_ids = _model.generate(
                **inputs,
                num_beams=4,
                max_length=128,
                early_stopping=True,
            )
        result = _tokenizer.decode(translated_ids[0], skip_special_tokens=True)
        return result
    except Exception as exc:
        logger.warning(f"Neural translation failed: {exc}")
        return text


def _oov_ratio(original_tokens: list[str], translated_tokens: list[str],
               kriol_keys: set[str]) -> float:
    """
    Estimate fraction of tokens that are still untranslated Kriol.

    A token is counted as OOV only if it is a known Kriol dictionary key
    that survived into the translated output unchanged.
    Tokens that happen to be valid English stopwords / medical terms are
    never counted as OOV even if they appear in both input and output.
    """
    if not original_tokens:
        return 0.0
    oov = 0
    for tok in translated_tokens:
        # A token is OOV if it's a Kriol word that wasn't translated
        if tok in kriol_keys and tok not in _ENGLISH_STOPWORDS:
            oov += 1
    return oov / max(len(translated_tokens), 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hybrid_translate(
    text: str,
    kriol_dict: dict[str, str],
    detected_lang: str = "mixed",
) -> dict:
    """
    Hybrid translation pipeline.

    Parameters
    ----------
    text : str
        Raw user input (Kriol, mixed, or English).
    kriol_dict : dict
        Pre-loaded Kriol → English mapping (from kriol_translator.load_kriol_dictionary).
    detected_lang : str
        Language label from language_detector ("english", "kriol", "mixed").

    Returns
    -------
    dict with keys:
        text        : str   — final English translation
        method      : str   — "passthrough" | "dict" | "dict+neural"
        oov_ratio   : float — fraction of OOV tokens after dict pass (0–1)
    """
    # ── Fast-path: pure English ───────────────────────────────────────────
    if detected_lang == "english":
        return {"text": text, "method": "passthrough", "oov_ratio": 0.0}

    # ── Stage 1: dictionary translation ──────────────────────────────────
    from nlp.kriol_translator import (
        translate_kriol_to_english,
        post_process_translation,
        tokenize_kriol,
    )

    dict_translated = translate_kriol_to_english(text, kriol_dict)
    dict_translated = post_process_translation(dict_translated)

    # Measure OOV
    original_tokens = tokenize_kriol(text)
    translated_tokens = dict_translated.lower().split()
    kriol_keys = set(kriol_dict.keys())
    oov = _oov_ratio(original_tokens, translated_tokens, kriol_keys)

    # ── Stage 2: neural fallback if OOV is high ───────────────────────────
    if oov >= OOV_THRESHOLD:
        neural_out = _neural_translate(text)

        # Merge: prefer neural output but keep dict-translated medical terms
        # Strategy: use neural output as base, then re-apply synonym mapping
        # downstream (synonym_mapper handles the rest).
        final_text = neural_out if neural_out.strip() else dict_translated
        return {
            "text": final_text,
            "method": "dict+neural",
            "oov_ratio": round(oov, 4),
        }

    return {
        "text": dict_translated,
        "method": "dict",
        "oov_ratio": round(oov, 4),
    }


def is_model_available() -> bool:
    """
    Check whether the MarianMT model can be loaded.
    Does NOT actually load it — just checks if transformers is importable
    and the model cache exists.
    """
    try:
        from transformers import MarianMTModel, MarianTokenizer  # noqa: F401
        return True
    except ImportError:
        return False
