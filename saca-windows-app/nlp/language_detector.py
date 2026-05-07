"""
Language Detector — TF-IDF + Logistic Regression
==================================================
Classifies input text as one of:
    "english"  — pure English
    "kriol"    — pure Bislama/Kriol
    "mixed"    — mixture of English and Kriol

Architecture:
    - TF-IDF vectorizer with character n-grams (2–4)
      Character n-grams capture Kriol phonetic patterns without needing
      tokenisation (e.g. "garr", "beli", "hedache", "fiwa")
    - Logistic Regression with L2 regularisation
    - Soft-probability output so callers can inspect confidence

The model is trained entirely from the embedded TRAINING_DATA list below
(no external files needed).  Call `get_detector()` to get a singleton
LanguageDetector that is fitted once and reused.
"""

from __future__ import annotations

import re
from typing import Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# ---------------------------------------------------------------------------
# Training corpus
# Each tuple: (text, label)  — label ∈ {"english", "kriol", "mixed"}
# ---------------------------------------------------------------------------
TRAINING_DATA: list[tuple[str, str]] = [

    # ── ENGLISH ──────────────────────────────────────────────────────────────
    ("I have a headache and fever", "english"),
    ("I am experiencing chest pain", "english"),
    ("I have shortness of breath", "english"),
    ("My throat is very sore", "english"),
    ("I feel dizzy and nauseous", "english"),
    ("I have been vomiting since yesterday", "english"),
    ("I have diarrhoea and abdominal pain", "english"),
    ("I have a cough and sore throat", "english"),
    ("I do not have a fever", "english"),
    ("I have no chest pain", "english"),
    ("I am feeling very weak and tired", "english"),
    ("My head hurts badly", "english"),
    ("I have a high temperature", "english"),
    ("I have trouble breathing", "english"),
    ("No vomiting but I do have nausea", "english"),
    ("I feel sick to my stomach", "english"),
    ("I have been having dizziness all day", "english"),
    ("My stomach hurts and I feel nauseous", "english"),
    ("I have a bad headache and feel tired", "english"),
    ("There is no fever but I have a cough", "english"),
    ("I am not feeling well", "english"),
    ("I have pain in my chest", "english"),
    ("Shortness of breath and coughing", "english"),
    ("No diarrhoea but stomach pain is present", "english"),
    ("I feel feverish and have body aches", "english"),
    ("My temperature is high and I have chills", "english"),
    ("I have been coughing for three days", "english"),
    ("The sore throat started yesterday", "english"),
    ("I do not have vomiting or nausea", "english"),
    ("Headache without fever", "english"),
    ("I feel lightheaded and weak", "english"),
    ("I have abdominal cramps and diarrhoea", "english"),
    ("No shortness of breath at this time", "english"),
    ("I have had chest tightness since morning", "english"),
    ("My head is spinning and I feel sick", "english"),

    # ── KRIOL ────────────────────────────────────────────────────────────────
    ("mi garr hedache", "kriol"),
    ("mi garr fiva", "kriol"),
    ("mi nat garr kof", "kriol"),
    ("mi garr hot-bodi en kof", "kriol"),
    ("mi garr beli sik", "kriol"),
    ("mi nat garr fiva bat mi garr hedache", "kriol"),
    ("mi garr sowa trot", "kriol"),
    ("mi garr traubul breeding", "kriol"),
    ("mi garr ches pein", "kriol"),
    ("mi garr disi en headek", "kriol"),
    ("mi nomo garr disi", "kriol"),
    ("mi garr kof en sowa trot", "kriol"),
    ("yu garr fiwa nau", "kriol"),
    ("mi nat garr ranishit", "kriol"),
    ("mi garr trowing-ap en beli pein", "kriol"),
    ("mi hed sik bigwan", "kriol"),
    ("mi beli sik lilbit", "kriol"),
    ("mi nat garr chak-ap", "kriol"),
    ("mi garr laitheded en disi", "kriol"),
    ("mi garr stomak pein en kof", "kriol"),
    ("mi garr het pein en hotbodi", "kriol"),
    ("mi nat garr ches pein bat mi garr kof", "kriol"),
    ("mi garr fiwa en trowing-ap", "kriol"),
    ("yu nat garr sowa trot", "kriol"),
    ("mi garr hedake en beli pein", "kriol"),
    ("mi nat garr bret prablem", "kriol"),
    ("mi garr gidibat en hedache", "kriol"),
    ("mi nat garr fiva bat mi garr sik", "kriol"),
    ("mi garr ranishit en stomak pein", "kriol"),
    ("mi hed en beli sik tumas", "kriol"),
    ("mi nomo garr trowing-ap", "kriol"),
    ("mi nat garr het pein", "kriol"),
    ("mi garr cof en hotbodi", "kriol"),
    ("mi garr bigwan hedache nau", "kriol"),
    ("mi fil wek en mi garr sowa trot", "kriol"),

    # ── MIXED ────────────────────────────────────────────────────────────────
    ("mi have fever and headache", "mixed"),
    ("I garr kof en sore throat", "mixed"),
    ("mi feel sick and I garr beli pein", "mixed"),
    ("I have hedache and mi garr hotbodi", "mixed"),
    ("mi experiencing chest pain", "mixed"),
    ("I have sowa trot en cough", "mixed"),
    ("mi not have fever but I have kof", "mixed"),
    ("I garr traubul breeding and chest pain", "mixed"),
    ("mi have dizziness and garr headache", "mixed"),
    ("I feel wek and mi garr fiva", "mixed"),
    ("mi hed sik en I have nausea", "mixed"),
    ("I have stomak pain and vomiting", "mixed"),
    ("mi nat have chest pain but I garr kof", "mixed"),
    ("I experiencing beli sik and fever", "mixed"),
    ("mi garr sore throat and I have cough", "mixed"),
    ("I feel gidibat and mi have headache", "mixed"),
    ("mi have shortness of breath en kof", "mixed"),
    ("I have fiwa and mi garr sowa trot", "mixed"),
    ("mi not garr fever but I feel sick", "mixed"),
    ("I have hedache en mi garr beli pein", "mixed"),
    ("Mi hed sik en mi fil wek, bat mi no gat beli sik", "mixed"),
    ("I garr fever and I have kof", "mixed"),
    ("mi have chest pain and shortness of breath", "mixed"),
    ("I feel dizzy en mi garr hotbodi", "mixed"),
    ("mi have diarrhoea and garr stomak pein", "mixed"),
    ("I experiencing sowa trot and fever", "mixed"),
    ("mi nat have vomiting but I have nausea", "mixed"),
    ("I garr ches pein and sore throat", "mixed"),
    ("mi feel weak and I have fiwa", "mixed"),
    ("I have beli pein en abdominal cramps", "mixed"),
]


def _preprocess(text: str) -> str:
    """Lowercase and normalise punctuation for consistent n-gram extraction."""
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class LanguageDetector:
    """
    TF-IDF char n-gram + Logistic Regression language classifier.

    Usage
    -----
    detector = LanguageDetector()
    label, confidence = detector.predict("mi garr hedache")
    # → ("kriol", 0.97)
    """

    LABELS = ("english", "kriol", "mixed")

    def __init__(self) -> None:
        self._pipeline = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",   # char n-grams with word boundaries
                    ngram_range=(2, 4),   # 2-, 3-, 4-char n-grams
                    min_df=1,
                    sublinear_tf=True,    # log(1+tf) smoothing
                    strip_accents="unicode",
                    lowercase=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=5.0,
                    max_iter=500,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ])
        self._fitted = False

    # ------------------------------------------------------------------
    def fit(self, data: list[tuple[str, str]] | None = None) -> "LanguageDetector":
        """
        Train on *data* (list of (text, label) tuples).
        Defaults to the embedded TRAINING_DATA corpus.
        """
        if data is None:
            data = TRAINING_DATA
        texts = [_preprocess(t) for t, _ in data]
        labels = [l for _, l in data]
        self._pipeline.fit(texts, labels)
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict language label and return (label, confidence).

        Parameters
        ----------
        text : str
            Raw input (Kriol, English, or mixed)

        Returns
        -------
        label : str
            One of "english", "kriol", "mixed"
        confidence : float
            Probability assigned to the predicted class (0–1)
        """
        if not self._fitted:
            self.fit()
        cleaned = _preprocess(text)
        proba = self._pipeline.predict_proba([cleaned])[0]
        classes = self._pipeline.classes_
        idx = proba.argmax()
        return str(classes[idx]), float(proba[idx])

    # ------------------------------------------------------------------
    def predict_all(self, text: str) -> dict[str, float]:
        """
        Return probability for every class as a dict.

        Example
        -------
        {"english": 0.02, "kriol": 0.95, "mixed": 0.03}
        """
        if not self._fitted:
            self.fit()
        cleaned = _preprocess(text)
        proba = self._pipeline.predict_proba([cleaned])[0]
        return {str(cls): float(p) for cls, p in zip(self._pipeline.classes_, proba)}


# ---------------------------------------------------------------------------
# Singleton — fitted once, reused across calls
# ---------------------------------------------------------------------------
_detector_instance: LanguageDetector | None = None


def get_detector() -> LanguageDetector:
    """Return the singleton LanguageDetector, fitting it on first call."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector().fit()
    return _detector_instance


def detect_language(text: str) -> Tuple[str, float]:
    """
    Convenience function — detect language of *text*.

    Returns
    -------
    (label, confidence) where label ∈ {"english", "kriol", "mixed"}
    """
    return get_detector().predict(text)
