from __future__ import annotations

from typing import Dict

from src.services.nlp_service import process_user_input
from src.services.ml_service import build_result_payload


def run_initial_assessment(raw_text: str, ui_language: str = "en") -> Dict:
    """
    Called by MainWindow after the user types, speaks, or selects pictures.
    Returns original text, English meaning, symptoms, and follow-up questions.
    """
    return process_user_input(raw_text, ui_language=ui_language)


def run_final_assessment(nlp_output: Dict, answers: Dict, ui_language: str = "en") -> Dict:
    """
    Called after the question flow. Combines NLP output + follow-up answers
    with the ML/rule triage adapter used by the Windows app result page.
    """
    return build_result_payload(nlp_output, answers, ui_language=ui_language)
