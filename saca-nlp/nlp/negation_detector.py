from typing import Dict, List, Tuple
import re

from nlp.bilstm_negation import bilstm_is_negated, OVERRIDE_THRESHOLD


NEGATION_WORDS = {"no", "not", "without", "never", "none", "neither", "nor", "nobody", "nothing", "deny", "denies", "lack", "absent"}
NEGATION_PHRASES = [
    r"\b(do not|does not|did not|have not|has not|had not|will not|would not|cannot|could not|should not)\b",
    r"\bno\s+\w+\s+(of|about|with)\b",
]
# Words that reset negation scope — a symptom after these is NOT negated
SCOPE_RESET_WORDS = {"but", "however", "although", "though", "yet", "except", "while", "whereas"}
WINDOW_SIZE = 6  # tokens to look back before the symptom


def is_negated(tokens: List[str], symptom_start_idx: int) -> bool:
    """
    Check if a symptom at the given token index is negated.
    Works purely on token indices — no fragile character-position slicing.
    Scope-reset words (but, however, although...) break the negation window
    so symptoms after 'but' are not incorrectly negated.

    Args:
        tokens: List of words in the text
        symptom_start_idx: Starting index of symptom in tokens

    Returns:
        True if symptom is negated, False otherwise
    """
    # Slice the window of tokens that appear before the symptom
    start_window = max(0, symptom_start_idx - WINDOW_SIZE)
    previous_tokens = tokens[start_window:symptom_start_idx]

    # Trim window at the last scope-reset word (e.g. "but")
    # so negation before "but" doesn't bleed into symptoms after "but"
    for j in range(len(previous_tokens) - 1, -1, -1):
        if previous_tokens[j] in SCOPE_RESET_WORDS:
            previous_tokens = previous_tokens[j + 1:]
            break

    window_text = " ".join(previous_tokens)

    # 1. Direct negation word in window
    if any(token in NEGATION_WORDS for token in previous_tokens):
        return True

    # 2. Negation phrases in window text
    for pattern in NEGATION_PHRASES:
        if re.search(pattern, window_text):
            return True

    # 3. Split-negation: "do/does/did/have ... not" within window
    if re.search(r'\b(do|does|did|have|has|had|will|would|can|could|should)\s+not\b', window_text):
        return True

    return False


def detect_negations(text: str, symptoms: List[str]) -> Tuple[List[str], List[str]]:
    """
    Rule-based negation detector.

    For each detected symptom phrase, checks whether a negation word/phrase
    appears within the previous WINDOW_SIZE tokens.

    Returns:
        Tuple of (present_symptoms, negated_symptoms)
    """
    tokens = text.split()
    negated = []
    present = []

    for symptom in symptoms:
        symptom_tokens = symptom.split()
        symptom_len = len(symptom_tokens)

        occurrences = []  # list of (index, is_negated) for every occurrence

        for i in range(len(tokens) - symptom_len + 1):
            if tokens[i:i + symptom_len] == symptom_tokens:
                occurrences.append((i, is_negated(tokens, i)))

        if not occurrences:
            continue

        # If ANY occurrence is present (not negated), symptom is present.
        # Only mark as negated if ALL occurrences are negated.
        # This handles "I feel like vomiting but I am not vomiting" correctly:
        # the first occurrence is present → symptom is present overall.
        any_present = any(not neg for _, neg in occurrences)
        any_negated = any(neg for _, neg in occurrences)

        if any_present:
            present.append(symptom)
        elif any_negated:
            negated.append(symptom)

    return present, negated


def detect_negations_hybrid(
    text: str,
    symptoms: List[str],
) -> Tuple[List[str], List[str]]:
    """
    Hybrid negation detector: rule-based first, Bi-LSTM override on high
    confidence disagreement.

    Decision logic per symptom
    --------------------------
    1. Run rule-based classifier  →  rule_negated (bool)
    2. Run Bi-LSTM classifier     →  lstm_prob    (float, 0=present, 1=negated)
    3. If lstm_prob >= OVERRIDE_THRESHOLD (0.82) AND rules say PRESENT
           → override to NEGATED   (LSTM caught negation rules missed)
       If lstm_prob <= (1 - OVERRIDE_THRESHOLD) AND rules say NEGATED
           → override to PRESENT   (LSTM confident it is present)
       Otherwise keep rule-based decision.

    This ensures existing test accuracy is preserved (rules handle all
    standard patterns at 100%) while LSTM catches genuinely novel negation
    structures the window/scope rules would miss.

    Args:
        text:     Preprocessed + synonym-mapped text.
        symptoms: List of canonical symptom strings detected in `text`.

    Returns:
        Tuple of (present_symptoms, negated_symptoms).
    """
    tokens = text.split()
    present: List[str] = []
    negated: List[str] = []

    for symptom in symptoms:
        symptom_tokens = symptom.split()
        symptom_len = len(symptom_tokens)

        occurrences = []  # (token_index, rule_is_negated)
        for i in range(len(tokens) - symptom_len + 1):
            if tokens[i:i + symptom_len] == symptom_tokens:
                occurrences.append((i, is_negated(tokens, i)))

        if not occurrences:
            continue

        # Rule-based decision (same logic as detect_negations)
        any_rule_present = any(not neg for _, neg in occurrences)
        any_rule_negated = any(neg for _, neg in occurrences)
        rule_says_negated = (not any_rule_present) and any_rule_negated

        # Bi-LSTM: run on a LOCAL context window around each occurrence.
        # Crucially, the post-symptom context is clipped at the first
        # scope-reset word so negations in a LATER clause do not bleed
        # into the current symptom's assessment.
        # The LSTM ONLY overrides when the rule-based pre-context window
        # contains NO negation words — i.e., the rules are completely blind
        # but the LSTM detects implied negation from broader context.
        # When negation words ARE present, the rules already handle scope
        # correctly and the LSTM (trained on simple synthetic data) is not
        # reliable enough to contradict them.
        CONTEXT_RADIUS = 8  # tokens on each side of the symptom
        lstm_prob = 0.5     # default: uncertain (no override)

        for occ_idx, _ in occurrences:
            # Pre-symptom context (up to CONTEXT_RADIUS tokens back)
            pre_start = max(0, occ_idx - CONTEXT_RADIUS)
            pre_ctx = tokens[pre_start:occ_idx]

            # Only consult LSTM if no explicit negation word appears
            # in the pre-context window — i.e., rules are "flying blind"
            pre_has_neg = any(t in NEGATION_WORDS for t in pre_ctx)
            if pre_has_neg:
                continue  # Rules handle this occurrence; skip LSTM

            # Post-symptom context — stop at first scope-reset OR negation word.
            # A negation word appearing AFTER the symptom belongs to a later
            # clause and must not pollute this symptom's context window.
            post_ctx: List[str] = []
            for t in tokens[occ_idx + symptom_len:
                             occ_idx + symptom_len + CONTEXT_RADIUS]:
                if t.lower() in SCOPE_RESET_WORDS or t.lower() in NEGATION_WORDS:
                    break
                post_ctx.append(t)

            local_ctx = " ".join(
                pre_ctx + tokens[occ_idx:occ_idx + symptom_len] + post_ctx
            )
            p = bilstm_is_negated(local_ctx, symptom)
            # Keep the most extreme probability across occurrences
            if abs(p - 0.5) > abs(lstm_prob - 0.5):
                lstm_prob = p

        # Reconcile
        if rule_says_negated:
            if lstm_prob <= (1.0 - OVERRIDE_THRESHOLD):
                # High-confidence LSTM says PRESENT — override rule
                present.append(symptom)
            else:
                negated.append(symptom)
        else:
            if lstm_prob >= OVERRIDE_THRESHOLD:
                # High-confidence LSTM says NEGATED — override rule
                negated.append(symptom)
            else:
                present.append(symptom)

    return present, negated


def build_result(input_text: str, cleaned_text: str, mapped_text: str,
                 extracted_symptoms: List[str], present: List[str], negated: List[str]) -> Dict:
    """Build the final structured output."""
    return {
        "input_text": input_text,
        "cleaned_text": cleaned_text,
        "mapped_text": mapped_text,
        "extracted_symptoms": extracted_symptoms,
        "symptoms_present": present,
        "symptoms_negated": negated
    }