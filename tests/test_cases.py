from main import run_pipeline
from nlp.language_detector import detect_language

# ---------------------------------------------------------------------------
# COMPREHENSIVE TEST SUITE
# Format: (label, input_text, expected_present, expected_negated)
#
# Categories:
#   A  - Basic English
#   B  - English synonym mapping
#   C  - English spelling correction
#   D  - English negation (simple)
#   E  - English negation (complex / "but" transitions)
#   F  - Basic Kriol
#   G  - Kriol negation
#   H  - Kriol synonym / body-part combos
#   I  - Mixed Kriol + English
#   J  - Intensifiers & time words (should not affect symptom detection)
#   K  - Multi-symptom sentences
#   L  - Edge cases (empty-ish, repeated symptoms, double negation)
# ---------------------------------------------------------------------------

TEST_CASES = [

    # ── A: Basic English ────────────────────────────────────────────────────
    ("A01", "I have fever and cough",
     ["cough", "fever"], []),

    ("A02", "I have a headache",
     ["headache"], []),

    ("A03", "I am experiencing chest pain",
     ["chest pain"], []),

    ("A04", "I have shortness of breath",
     ["shortness of breath"], []),

    ("A05", "I have nausea and vomiting",
     ["nausea", "vomiting"], []),

    ("A06", "I have diarrhoea",
     ["diarrhoea"], []),

    ("A07", "I have abdominal pain",
     ["abdominal pain"], []),

    ("A08", "I have a sore throat",
     ["sore throat"], []),

    # ── B: English synonym mapping ──────────────────────────────────────────
    ("B01", "I have a high temperature and sore throat",
     ["fever", "sore throat"], []),

    ("B02", "I feel dizzy and have stomach ache",
     ["abdominal pain", "dizziness"], []),

    ("B03", "I am light headed and feel sick",
     ["dizziness", "nausea"], []),

    ("B04", "I have trouble breathing and chest pain",
     ["chest pain", "shortness of breath"], []),

    ("B05", "I have been throwing up since this morning",
     ["vomiting"], []),

    ("B06", "I feel like vomiting and I have a temperature",
     ["fever", "nausea"], []),

    ("B07", "I have tummy pain and I am coughing",
     ["abdominal pain", "cough"], []),

    ("B08", "My throat is very sore and I have a temp",
     ["fever", "sore throat"], []),

    # ── C: Spelling correction ──────────────────────────────────────────────
    ("C01", "I have diziness and headche",
     ["dizziness", "headache"], []),

    ("C02", "I have fver and cogh",
     ["cough", "fever"], []),

    ("C03", "I have stomack pain and nausau",
     ["abdominal pain", "nausea"], []),

    ("C04", "I have shortnss of breth",
     ["shortness of breath"], []),

    ("C05", "I have dirrhoea and vomitin",
     ["diarrhoea", "vomiting"], []),

    # ── D: Simple English negation ──────────────────────────────────────────
    ("D01", "I don't have fever",
     [], ["fever"]),

    ("D02", "I have no chest pain and no shortness of breath",
     [], ["chest pain", "shortness of breath"]),

    ("D03", "I do not have nausea",
     [], ["nausea"]),

    ("D04", "I have never had dizziness",
     [], ["dizziness"]),

    ("D05", "Without fever",
     [], ["fever"]),

    ("D06", "I have no headache",
     [], ["headache"]),

    ("D07", "I have no vomiting and no diarrhoea",
     [], ["diarrhoea", "vomiting"]),

    # ── E: Complex negation with "but" transitions ──────────────────────────
    ("E01", "I have headache but no vomiting",
     ["headache"], ["vomiting"]),

    ("E02", "I do not have chest pain but I am coughing",
     ["cough"], ["chest pain"]),

    ("E03", "I have no fever but I have a bad cough",
     ["cough"], ["fever"]),

    ("E04", "I have headache but I don't have nausea",
     ["headache"], ["nausea"]),

    ("E05", "I do not have any fever or cough but I do have a headache",
     ["headache"], ["cough", "fever"]),

    ("E06", "Without fever but experiencing dizziness",
     ["dizziness"], ["fever"]),

    ("E07", "No shortness of breath but I have abdominal pain and nausea",
     ["abdominal pain", "nausea"], ["shortness of breath"]),

    ("E08", "I don't have chest pain however I do have a sore throat and cough",
     ["cough", "sore throat"], ["chest pain"]),

    # ── F: Basic Kriol ──────────────────────────────────────────────────────
    ("F01", "mi garr hedache",
     ["headache"], []),

    ("F02", "mi garr hot-bodi",
     ["fever"], []),

    ("F03", "mi garr kof",
     ["cough"], []),

    ("F04", "mi garr disi",
     ["dizziness"], []),

    ("F05", "mi garr hedache en kof",
     ["cough", "headache"], []),

    ("F06", "mi garr hot-bodi en mi garr hedache",
     ["fever", "headache"], []),

    ("F07", "mi garr beli sowa",
     ["abdominal pain"], []),

    ("F08", "mi garr sowa trot",
     ["sore throat"], []),

    # ── G: Kriol negation ───────────────────────────────────────────────────
    ("G01", "mi nat garr fiva",
     [], ["fever"]),

    ("G02", "mi nat garr kof",
     [], ["cough"]),

    ("G03", "mi nat garr hedache",
     [], ["headache"]),

    ("G04", "mi nat garr fiva bat mi garr hedache",
     ["headache"], ["fever"]),

    ("G05", "mi nat garr kof bat mi garr hot-bodi",
     ["fever"], ["cough"]),

    ("G06", "mi nomo garr disi",
     [], ["dizziness"]),

    ("G07", "Mi hed sik en mi fil wek, bat mi no gat beli sik.",
     ["fatigue", "headache"], ["nausea"]),

    ("G08", "Mi hed sik en mi fil laik spyu, en mi fil wek tu, bat mi no spyu en mi no gat beli sik en mi no gat fiba.",
     ["fatigue", "headache", "nausea"], ["fever", "vomiting"]),

    ("G09", "Mi bodi i sore en mi fil dizzi en mi kan slip gud, bat mi no gat kol en mi no kof en mi noz i no ran.",
     ["dizziness", "fatigue", "insomnia"], ["cough", "runny nose"]),

    # ── H: Kriol body-part + symptom combos ─────────────────────────────────
    ("H01", "mi garr hedache en mi belly sore",
     ["abdominal pain", "headache"], []),

    ("H02", "mi garr hot-bodi en cof",
     ["cough", "fever"], []),

    ("H03", "mi garr ches pein",
     ["chest pain"], []),

    ("H04", "mi garr traubul breeding",
     ["shortness of breath"], []),

    ("H05", "mi garr sowa trot en kof",
     ["cough", "sore throat"], []),

    ("H06", "mi garr beli pein en mi spew",
     ["abdominal pain", "vomiting"], []),

    # ── I: Mixed Kriol + English ─────────────────────────────────────────────
    ("I01", "mi have headache and kof",
     ["cough", "headache"], []),

    ("I02", "I garr fever en headache",
     ["fever", "headache"], []),

    ("I03", "mi nat have fever but I have cough",
     ["cough"], ["fever"]),

    ("I04", "mi feel dizzy en have stomach pain",
     ["abdominal pain", "dizziness"], []),

    # ── J: Intensifiers and time words (should not create false symptoms) ────
    ("J01", "mi bigwan garr hedache",
     ["headache"], []),

    ("J02", "mi garr lil kof nau",
     ["cough"], []),

    ("J03", "mi tumas sik tudei",
     [], []),

    ("J04", "mi garr hedache langtaim",
     ["headache"], []),

    # ── K: Multi-symptom ────────────────────────────────────────────────────
    ("K01", "I have fever, cough, headache and nausea",
     ["cough", "fever", "headache", "nausea"], []),

    ("K02", "I have chest pain, shortness of breath and dizziness",
     ["chest pain", "dizziness", "shortness of breath"], []),

    ("K03", "mi garr hot-bodi en hedache en kof en disi",
     ["cough", "dizziness", "fever", "headache"], []),

    ("K04", "I have abdominal pain, nausea, vomiting and diarrhoea",
     ["abdominal pain", "diarrhoea", "nausea", "vomiting"], []),

    # ── L: Edge cases ───────────────────────────────────────────────────────
    ("L01", "I have fever and fever",         # duplicate symptom
     ["fever"], []),

    ("L02", "I do not have fever and I do not have cough",
     [], ["cough", "fever"]),

    ("L03", "I have no fever no cough and no headache",
     [], ["cough", "fever", "headache"]),

    ("L04", "I have sore throat but no sore throat",   # contradictory — present-wins
     ["sore throat"], []),

    # ── N: Expanded Symptoms ────────────────────────────────────────────────
    ("N01", "I have back pain",
     ["back pain"], []),

    ("N02", "I have ear pain",
     ["ear pain"], []),

    ("N03", "I have eye pain",
     ["eye pain"], []),

    ("N04", "I have a toothache",
     ["toothache"], []),

    ("N05", "My leg is swollen",
     ["swelling"], []),

    ("N06", "I feel itchy all over my body",
     ["itching"], []),

    ("N07", "I have muscle pain",
     ["muscle pain"], []),

    ("N08", "I am bleeding",
     ["bleeding"], []),

    ("N09", "I have been sweating a lot",
     ["sweating"], []),

    ("N10", "I am shivering and I have fever",
     ["fever", "shivering"], []),

    ("N11", "I have no appetite",
     ["loss of appetite"], []),

    ("N12", "mi garr bak pein en iya sore",
     ["back pain", "ear pain"], []),

    ("N13", "mi bodi itji en mi no garr bak pein",
     ["itching"], ["back pain"]),

    # ── P: Kriol Phase-2 Vocabulary ─────────────────────────────────────────
    # Tests Kriol dictionary entries added in Phase 2 (swelin, joinpein,
    # sholdapein, maselpein, aisore, titpein)
    ("P01", "mi garr swelin en joinpein",
     ["joint pain", "swelling"], []),

    ("P02", "mi garr sholdapein en maselpein",
     ["muscle pain", "shoulder pain"], []),

    ("P03", "mi garr swelin en no garr joinpein",
     ["swelling"], ["joint pain"]),

    ("P04", "mi no garr swelin",
     [], ["swelling"]),

    # ── Q: Synonym Mapping — Expanded Symptoms ──────────────────────────────
    # Tests that synonym entries for Phase-2 symptoms resolve correctly
    ("Q01", "my joints ache and my eyes are sore",
     ["eye pain", "joint pain"], []),

    ("Q02", "I have blood coming out and I have fever",
     ["bleeding", "fever"], []),

    ("Q03", "I have excessive sweating and I am shivering",
     ["shivering", "sweating"], []),

    # ── R: Negation — Expanded Symptoms ─────────────────────────────────────
    # Tests complex negation ("but no ...") and Kriol negation over Phase-2
    # symptom vocabulary
    ("R01", "I have shoulder pain but no swelling",
     ["shoulder pain"], ["swelling"]),

    ("R02", "mi garr aisore bat mi no garr titpein",
     ["eye pain"], ["toothache"]),

]

# ---------------------------------------------------------------------------
# Category O — BERT Advisory Suggestions
# Format: (label, input_text, expected_bert_present)
# These inputs contain novel clinical descriptions NOT in the synonym
# dictionary. The PhraseMatcher pipeline returns nothing; the BERT advisory
# layer should surface the correct symptom in bert_suggestions["present"].
# Tested separately because bert_suggestions is advisory-only.
# ---------------------------------------------------------------------------
BERT_CASES: list[tuple[str, str, list]] = [
    # O01: "loose watery bowel movements" is now in synonyms.json so the
    # PhraseMatcher catches diarrhoea directly — BERT finds nothing new.
    # This case now validates that BERT correctly returns [] when the
    # PhraseMatcher already handled the symptom (no double-counting).
    ("O01", "I have loose watery bowel movements", []),
]


# ---------------------------------------------------------------------------
# Category M — Language Detection
# Format: (label, input_text, expected_language)
# Tested separately from symptom cases
# ---------------------------------------------------------------------------
LANGUAGE_DETECTION_CASES: list[tuple[str, str, str]] = [
    # Pure English
    ("M01", "I have a headache and fever",                   "english"),
    ("M02", "I am experiencing chest pain",                  "english"),
    ("M03", "I have shortness of breath",                    "english"),
    ("M04", "I do not have a fever",                         "english"),
    ("M05", "My throat is very sore and I have a cough",     "english"),
    ("M06", "I feel dizzy and nauseous",                     "english"),
    ("M07", "No vomiting but I have nausea",                 "english"),
    ("M08", "I have been coughing for three days",           "english"),

    # Pure Kriol
    ("M09",  "mi garr hedache",                              "kriol"),
    ("M10",  "mi garr fiva en kof",                          "kriol"),
    ("M11",  "mi nat garr fiva bat mi garr hedache",         "kriol"),
    ("M12",  "mi garr hot-bodi en mi garr sowa trot",        "kriol"),
    ("M13",  "mi nomo garr disi",                            "kriol"),
    ("M14",  "mi garr traubul breeding",                     "kriol"),
    ("M15",  "mi garr beli pein en mi spew",                 "kriol"),
    ("M16",  "mi hed en beli sik tumas",                     "kriol"),

    # Mixed
    ("M17", "mi have fever and headache",                    "mixed"),
    ("M18", "I garr kof en sore throat",                     "mixed"),
    ("M19", "mi feel sick and I have beli pein",             "mixed"),
    ("M20", "I have hedache and mi garr hotbodi",            "mixed"),
    ("M21", "mi not have fever but I have kof",              "mixed"),
    ("M22", "I feel wek and mi garr fiva",                   "mixed"),
    ("M23", "Mi hed sik en mi fil wek, bat mi no gat beli sik", "mixed"),
    ("M24", "I have fiwa and mi garr sowa trot",             "mixed"),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

CATEGORIES = {
    "A": "Basic English",
    "B": "Synonym Mapping",
    "C": "Spelling Correction",
    "D": "Simple Negation",
    "E": "Complex Negation (but/however)",
    "F": "Basic Kriol",
    "G": "Kriol Negation",
    "H": "Kriol Body-Part Combos",
    "I": "Mixed Kriol + English",
    "J": "Intensifiers / Time Words",
    "K": "Multi-Symptom",
    "L": "Edge Cases",
    "M": "Language Detection",
    "N": "Expanded Symptoms",
    "O": "BERT Advisory Suggestions",
    "P": "Kriol Phase-2 Vocabulary",
    "Q": "Synonym Expanded Symptoms",
    "R": "Negation Expanded Symptoms",
}


def run_tests(show_all: bool = False):
    """
    Run all test cases and print a per-category and overall accuracy report.

    Args:
        show_all: If True, print every test including passes.
                  If False (default), only print failures.
    """
    results_by_category = {k: {"pass": 0, "fail": 0} for k in CATEGORIES}
    failures = []
    correct = 0
    total = len(TEST_CASES)

    for label, text, exp_present, exp_negated in TEST_CASES:
        category = label[0]
        result = run_pipeline(text)
        got_present = sorted(result["symptoms_present"])
        got_negated = sorted(result["symptoms_negated"])
        exp_p = sorted(exp_present)
        exp_n = sorted(exp_negated)

        passed = (got_present == exp_p) and (got_negated == exp_n)
        if passed:
            correct += 1
            results_by_category[category]["pass"] += 1
        else:
            results_by_category[category]["fail"] += 1
            failures.append((label, text, exp_p, exp_n, got_present, got_negated))

    # ── Category summary ────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("CATEGORY BREAKDOWN")
    print("=" * 70)
    for cat, name in CATEGORIES.items():
        p = results_by_category[cat]["pass"]
        f = results_by_category[cat]["fail"]
        t = p + f
        if t == 0:
            continue
        bar = ("█" * p) + ("░" * f)
        pct = (p / t) * 100
        print(f"  {cat} | {name:<35} {p:>2}/{t}  {pct:5.1f}%  [{bar}]")

    # ── Failures detail ─────────────────────────────────────────────────────
    if failures:
        print("\n" + "=" * 70)
        print("FAILURES")
        print("=" * 70)
        for label, text, exp_p, exp_n, got_p, got_n in failures:
            print(f"\n  [{label}] {text}")
            if got_p != exp_p:
                print(f"    Present  got={got_p}")
                print(f"             exp={exp_p}")
            if got_n != exp_n:
                print(f"    Negated  got={got_n}")
                print(f"             exp={exp_n}")

    # ── Language Detection (Category M) ────────────────────────────────────
    lang_correct = 0
    lang_failures = []
    for label, text, expected_lang in LANGUAGE_DETECTION_CASES:
        got_lang, confidence = detect_language(text)
        if got_lang == expected_lang:
            lang_correct += 1
            results_by_category["M"]["pass"] += 1
        else:
            results_by_category["M"]["fail"] += 1
            lang_failures.append((label, text, expected_lang, got_lang, confidence))

    lang_total = len(LANGUAGE_DETECTION_CASES)
    p = lang_correct
    f = lang_total - lang_correct
    bar = ("█" * p) + ("░" * f)
    pct = (p / lang_total) * 100
    print(f"  M | {'Language Detection':<35} {p:>2}/{lang_total}  {pct:5.1f}%  [{bar}]")

    if lang_failures:
        print("\n" + "=" * 70)
        print("LANGUAGE DETECTION FAILURES")
        print("=" * 70)
        for label, text, exp, got, conf in lang_failures:
            print(f"  [{label}] {text!r}")
            print(f"    expected={exp}  got={got}  confidence={conf:.3f}")

    # ── BERT Advisory Suggestions (Category O) ──────────────────────────────
    bert_correct = 0
    bert_failures = []
    for label, text, expected_bert in BERT_CASES:
        result = run_pipeline(text)
        got_bert = sorted(result["bert_suggestions"]["present"])
        exp_b = sorted(expected_bert)
        if got_bert == exp_b:
            bert_correct += 1
            results_by_category["O"]["pass"] += 1
        else:
            results_by_category["O"]["fail"] += 1
            bert_failures.append((label, text, exp_b, got_bert))

    bert_total = len(BERT_CASES)
    p = bert_correct
    f = bert_total - bert_correct
    bar = ("\u2588" * p) + ("\u2591" * f)
    pct = (p / bert_total) * 100 if bert_total > 0 else 0.0
    print(f"  O | {'BERT Advisory Suggestions':<35} {p:>2}/{bert_total}  {pct:5.1f}%  [{bar}]")

    if bert_failures:
        print("\n" + "=" * 70)
        print("BERT ADVISORY FAILURES")
        print("=" * 70)
        for label, text, exp, got in bert_failures:
            print(f"  [{label}] {text!r}")
            print(f"    expected={exp}  got={got}")

    # ── Overall ─────────────────────────────────────────────────────────────
    total_all = total + lang_total + bert_total
    correct_all = correct + lang_correct + bert_correct
    accuracy = (correct_all / total_all) * 100
    print("\n" + "=" * 70)
    print(f"OVERALL:  {correct_all}/{total_all} passed  ->  Accuracy: {accuracy:.1f}%")
    print(f"  Symptom cases:  {correct}/{total}")
    print(f"  Language cases: {lang_correct}/{lang_total}")
    print(f"  BERT cases:     {bert_correct}/{bert_total}")
    print("=" * 70 + "\n")
    return accuracy


if __name__ == "__main__":
    run_tests()

