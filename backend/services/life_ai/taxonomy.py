from __future__ import annotations

TOPIC_MAP = {
    "health": [
        "headache", "back pain", "neck pain", "fever", "cold", "cough", "allergy", "hair fall", "skin", "medicine",
        "doctor", "sleep disturbance", "sleep", "insomnia", "tired", "fatigue", "waking up tired", "hydration", "dehydrated",
    ],
    "tech": [
        "phone", "battery", "internet", "password", "laptop", "screen", "charger", "bluetooth", "printer", "storage", "file",
        "message", "autocorrect", "app", "software", "update", "network", "signal", "charging", "overheating",
    ],
    "home": [
        "shirt", "sandal", "punctured", "water bottle", "tea", "coffee", "electricity", "fan", "gas cylinder", "milk", "fridge",
        "clothes", "laundry", "water shortage", "bathroom", "tap", "sink", "toilet", "room messy", "mosquito", "noise", "neighbors",
    ],
    "schedule": [
        "keys", "alarm", "overslept", "late", "wallet", "bus", "train", "umbrella", "traffic", "fuel", "parking", "meeting",
        "documents", "appointment", "routine", "schedule", "time management", "calendar", "late for class",
    ],
    "study": [
        "study", "exam", "revision", "syllabus", "focus while studying", "assignment", "class test", "college work",
    ],
    "productivity": [
        "productive", "productivity", "procrastination", "procrastinating", "distraction", "wasting time", "discipline", "habit", "routine",
    ],
    "food": [
        "diet", "food", "meal", "hungry", "eating", "breakfast", "lunch", "dinner", "junk food", "weight gain",
    ],
    "career": ["career", "job", "interview", "rejection", "promotion", "resume", "cv"],
    "relationship": ["friend", "relationship", "partner", "family", "fight", "trust", "breakup"],
    "money": ["money", "finance", "debt", "rent", "savings", "expenses", "payment", "atm", "card", "upi", "budget"],
    "stress": ["stress", "anxious", "panic", "overwhelmed", "burnout", "mental pressure"],
}

DETAIL_MAP = {
    "switch job": ["switch", "quit", "leave my job", "change job"],
    "leave job": ["resign", "leave work"],
    "interview": ["interview", "interviews"],
    "fight": ["fight", "argument", "argued"],
    "trust": ["trust", "betrayed", "lying", "cheated"],
    "debt": ["debt", "loan", "credit card"],
    "rent": ["rent", "landlord", "house payment"],
    "can't sleep": ["can't sleep", "cannot sleep", "insomnia", "not sleeping"],
    "burnout": ["burnout", "burned out", "exhausted"],
    "decision": ["decision", "choose", "choice"],
    "headache": ["headache", "migraine"],
    "screen time": ["screen time", "mobile usage", "long screen"],
    "fever": ["fever"],
    "internet issue": ["internet not working", "internet", "weak signal", "network weak", "call drop"],
    "battery issue": ["battery draining", "battery", "heats while charging", "phone heats"],
    "password issue": ["password", "upi pin"],
    "device issue": ["laptop hanging", "charger not working", "screen cracked", "app crashing", "software bugs", "storage full", "bluetooth not connecting", "printer not working"],
    "leakage": ["leakage", "clogged sink", "broken tap", "toilet flush", "water shortage"],
    "late issue": ["overslept", "got late", "missed bus", "missed train", "traffic jam", "late for meeting"],
    "study block": ["can't focus", "not able to study", "revision plan"],
    "routine reset": ["daily routine", "routine", "sleep schedule", "waking up tired"],
}


def topic_key(lowered: str) -> str:
    for label in ["health", "study", "productivity", "food", "tech", "home", "schedule", "career", "relationship", "money", "stress"]:
        if any(word in lowered for word in TOPIC_MAP[label]):
            return label
    return "general"


def extract_situation_details(lowered: str) -> list[str]:
    details: list[str] = []
    for label, phrases in DETAIL_MAP.items():
        if any(phrase in lowered for phrase in phrases):
            details.append(label)
    return details