from typing import Dict, List
from copy import deepcopy


RED_FLAG_QUESTIONS: List[Dict] = [
    {
        "id": "red_breathing_now",
        "text": "Trouble breathing now?",
        "options": ["yes", "no"],
        "priority": 1,
    },
    {
        "id": "red_chest_pain_now",
        "text": "Chest pain now?",
        "options": ["yes", "no"],
        "priority": 1,
    },
    {
        "id": "red_heavy_bleeding",
        "text": "Bleeding a lot?",
        "options": ["yes", "no"],
        "priority": 1,
    },
    {
        "id": "red_passed_out",
        "text": "Passed out or hard to wake?",
        "options": ["yes", "no"],
        "priority": 1,
    },
]


GENERAL_QUESTIONS: List[Dict] = [
    {
        "id": "where_problem",
        "text": "Where is the problem?",
        "options": ["head", "chest", "stomach", "skin", "throat", "whole body"],
        "priority": 1,
    },
    {
        "id": "when_started",
        "text": "When did it start?",
        "options": ["today", "yesterday", "2-3 days", "many days", "not sure"],
        "priority": 2,
    },
    {
        "id": "getting_worse",
        "text": "Is it getting worse?",
        "options": ["yes", "no", "not sure"],
        "priority": 3,
    },
]


QUESTION_BANK: Dict[str, List[Dict]] = {
    "fever": [
        {
            "id": "fever_now",
            "text": "Do you still have fever now?",
            "options": ["yes", "no", "not sure"],
            "priority": 1,
        },
        {
            "id": "fever_cough",
            "text": "Do you also have cough?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "fever_rash",
            "text": "Do you also have rash?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "fever_drink_water",
            "text": "Can you drink water?",
            "options": ["yes", "no"],
            "priority": 4,
        },
    ],
    "cough": [
        {
            "id": "cough_type",
            "text": "Is the cough dry or wet?",
            "options": ["dry", "wet", "not sure"],
            "priority": 1,
        },
        {
            "id": "cough_breathing",
            "text": "Is it hard to breathe?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "cough_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "cough_days",
            "text": "How many days have you had the cough?",
            "options": ["1 day", "2-3 days", "4-7 days", "more than 7 days"],
            "priority": 4,
        },
    ],
    "breathing_problem": [
        {
            "id": "breathing_now",
            "text": "Is it hard to breathe right now?",
            "options": ["yes", "no"],
            "priority": 1,
        },
        {
            "id": "breathing_chest_pain",
            "text": "Do you also have chest pain?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "breathing_worse",
            "text": "Is the breathing getting worse?",
            "options": ["yes", "no"],
            "priority": 3,
        },
    ],
    "chest_pain": [
        {
            "id": "chest_pain_now",
            "text": "Do you have chest pain now?",
            "options": ["yes", "no"],
            "priority": 1,
        },
        {
            "id": "chest_pain_breathing",
            "text": "Is it hard to breathe?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "chest_pain_sudden",
            "text": "Did the pain start suddenly?",
            "options": ["yes", "no", "not sure"],
            "priority": 3,
        },
    ],
    "vomiting": [
        {
            "id": "vomiting_today",
            "text": "How many times did you vomit today?",
            "options": ["1-2", "3-5", "more than 5", "not sure"],
            "priority": 1,
        },
        {
            "id": "vomiting_keep_water",
            "text": "Can you keep water down?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "vomiting_stomach_pain",
            "text": "Do you also have stomach pain?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "vomiting_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 4,
        },
    ],
    "diarrhea": [
        {
            "id": "diarrhea_today",
            "text": "How many times today?",
            "options": ["1-2", "3-5", "more than 5", "not sure"],
            "priority": 1,
        },
        {
            "id": "diarrhea_water",
            "text": "Can you drink water?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "diarrhea_stomach_pain",
            "text": "Do you also have stomach pain?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "diarrhea_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 4,
        },
    ],
    "rash": [
        {
            "id": "rash_itchy",
            "text": "Is the rash itchy?",
            "options": ["yes", "no"],
            "priority": 1,
        },
        {
            "id": "rash_spreading",
            "text": "Is it spreading?",
            "options": ["yes", "no", "not sure"],
            "priority": 2,
        },
        {
            "id": "rash_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "rash_swelling",
            "text": "Is there swelling?",
            "options": ["yes", "no"],
            "priority": 4,
        },
    ],
    "pain": [
        {
            "id": "pain_where",
            "text": "Where is the pain?",
            "options": ["head", "chest", "stomach", "arm/leg", "whole body"],
            "priority": 1,
        },
        {
            "id": "pain_sudden",
            "text": "Did the pain start suddenly?",
            "options": ["yes", "no", "not sure"],
            "priority": 2,
        },
        {
            "id": "pain_worse",
            "text": "Is the pain getting worse?",
            "options": ["yes", "no"],
            "priority": 3,
        },
    ],
    "headache": [
        {
            "id": "headache_strong",
            "text": "Is the headache strong?",
            "options": ["yes", "no", "not sure"],
            "priority": 1,
        },
        {
            "id": "headache_vomiting",
            "text": "Do you also feel sick or vomit?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "headache_light",
            "text": "Does bright light bother you?",
            "options": ["yes", "no"],
            "priority": 3,
        },
        {
            "id": "headache_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 4,
        },
    ],
    "sore_throat": [
        {
            "id": "throat_swallow",
            "text": "Is it hard to swallow?",
            "options": ["yes", "no"],
            "priority": 1,
        },
        {
            "id": "throat_fever",
            "text": "Do you also have fever?",
            "options": ["yes", "no"],
            "priority": 2,
        },
        {
            "id": "throat_cough",
            "text": "Do you also have cough?",
            "options": ["yes", "no"],
            "priority": 3,
        },
    ],
}


QUESTION_TEXT_KRIOL = {
    "red_breathing_now": "Yu garr trabul blong brith nau?",
    "red_chest_pain_now": "Yu garr jes pein nau?",
    "red_heavy_bleeding": "Blad i kamat tumas?",
    "red_passed_out": "Yu foldaon o ad fo weigap?",

    "where_problem": "Wea na trabul?",
    "when_started": "Wen im stat?",
    "getting_worse": "Im kam moa nogud?",

    "fever_now": "Yu stil garr fiba nau?",
    "fever_cough": "Yu garr kof tu?",
    "fever_rash": "Yu garr rash tu?",
    "fever_drink_water": "Yu ken dringgim woda?",

    "cough_type": "Kof im drai o wet?",
    "cough_breathing": "Im ad fo brith?",
    "cough_fever": "Yu garr fiba tu?",
    "cough_days": "Haumeni dei yu bin garr kof?",

    "breathing_now": "Im ad fo brith nau?",
    "breathing_chest_pain": "Yu garr jes pein tu?",
    "breathing_worse": "Brithin i kam moa nogud?",

    "chest_pain_now": "Yu garr jes pein nau?",
    "chest_pain_breathing": "Im ad fo brith?",
    "chest_pain_sudden": "Pein bin stat kwikwan?",

    "vomiting_today": "Haumeni taim yu bin spyu tudei?",
    "vomiting_keep_water": "Yu ken kipim woda daun?",
    "vomiting_stomach_pain": "Yu garr beli pein tu?",
    "vomiting_fever": "Yu garr fiba tu?",

    "diarrhea_today": "Haumeni taim tudei?",
    "diarrhea_water": "Yu ken dringgim woda?",
    "diarrhea_stomach_pain": "Yu garr beli pein tu?",
    "diarrhea_fever": "Yu garr fiba tu?",

    "rash_itchy": "Rash i itji?",
    "rash_spreading": "Im spredin?",
    "rash_fever": "Yu garr fiba tu?",
    "rash_swelling": "Swelin deya?",

    "pain_where": "Wea na pein?",
    "pain_sudden": "Pein bin stat kwikwan?",
    "pain_worse": "Pein i kam moa nogud?",

    "headache_strong": "Hedake im strongbala?",
    "headache_vomiting": "Yu fil sik o spyu?",
    "headache_light": "Lait i wori yu?",
    "headache_fever": "Yu garr fiba tu?",

    "throat_swallow": "Im ad fo swalow?",
    "throat_fever": "Yu garr fiba tu?",
    "throat_cough": "Yu garr kof tu?"
}


OPTION_TEXT_KRIOL = {
    "yes": "yes",
    "no": "no",
    "not sure": "nomo shua",
    "today": "tudei",
    "yesterday": "yestadei",
    "2-3 days": "2-3 dei",
    "many days": "planti dei",
    "1 day": "1 dei",
    "4-7 days": "4-7 dei",
    "more than 7 days": "moa than 7 dei",
    "dry": "drai",
    "wet": "wet",
    "head": "hed",
    "chest": "jes",
    "stomach": "beli",
    "skin": "skin",
    "throat": "throt",
    "whole body": "hol bodi",
    "arm/leg": "am o leg",
    "1-2": "1-2",
    "3-5": "3-5",
    "more than 5": "moa than 5"
}


def _localize_question(question: Dict, language_code: str) -> Dict:
    localized = deepcopy(question)

    if language_code != "kriol":
        return localized

    qid = question.get("id", "")
    localized["text"] = QUESTION_TEXT_KRIOL.get(qid, question["text"])

    localized_options = []
    for option in question.get("options", []):
        localized_options.append(OPTION_TEXT_KRIOL.get(str(option).lower(), option))

    localized["options"] = localized_options
    return localized


def get_red_flag_questions(language_code: str = "en") -> List[Dict]:
    return [_localize_question(q, language_code) for q in RED_FLAG_QUESTIONS]


def select_followup_questions(symptoms: List[str], max_questions: int = 5, language_code: str = "en") -> List[Dict]:
    selected: List[Dict] = []
    seen_ids = set()

    for q in GENERAL_QUESTIONS:
        if q["id"] not in seen_ids and len(selected) < max_questions:
            selected.append(q)
            seen_ids.add(q["id"])

    for symptom in symptoms:
        for q in QUESTION_BANK.get(symptom, []):
            if q["id"] not in seen_ids and len(selected) < max_questions:
                selected.append(q)
                seen_ids.add(q["id"])

    selected.sort(key=lambda x: x.get("priority", 99))
    selected = selected[:max_questions]

    return [_localize_question(q, language_code) for q in selected]