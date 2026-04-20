from typing import Dict
from src.services.nlp_service import process_user_input
from src.services.ml_service import classify_case


def run_initial_assessment(raw_text: str, ui_language: str) -> Dict:
    return process_user_input(raw_text, ui_language)


def run_final_assessment(nlp_output: Dict, answers: Dict) -> Dict:
    result = classify_case(nlp_output, answers)
    return {
        "nlp": nlp_output,
        "result": result,
    }