import json
from pathlib import Path
from typing import List

import spacy
from spacy.matcher import PhraseMatcher


def load_symptoms(filepath: str = "data/symptoms.json") -> List[str]:
    """Load canonical symptom list from JSON."""
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class SymptomExtractor:
    def __init__(self, symptoms: List[str]):
        self.symptoms = symptoms
        self.nlp = spacy.blank("en")
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        patterns = [self.nlp.make_doc(symptom) for symptom in symptoms]
        self.matcher.add("SYMPTOMS", patterns)

    def extract_symptoms(self, text: str) -> List[str]:
        """Return a unique list of symptoms found in the text."""
        doc = self.nlp(text)
        matches = self.matcher(doc)

        found = []
        for _, start, end in matches:
            symptom_text = doc[start:end].text.lower()
            if symptom_text not in found:
                found.append(symptom_text)

        return found