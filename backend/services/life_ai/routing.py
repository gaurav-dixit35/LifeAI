from __future__ import annotations

from typing import Any

CASUAL_PHRASES = {
    "hi",
    "hello",
    "hey",
    "hii",
    "yo",
    "good morning",
    "good evening",
    "good night",
    "how are you",
    "what's up",
    "whats up",
    "thanks",
    "thank you",
    "who are you",
    "what can you do",
}

QUESTION_STARTERS = (
    "what ",
    "how ",
    "why ",
    "when ",
    "where ",
    "which ",
    "who ",
    "can ",
    "could ",
    "should ",
    "would ",
    "is ",
    "are ",
    "do ",
    "does ",
    "did ",
    "will ",
)

PROBLEM_MARKERS = [
    "help",
    "advice",
    "problem",
    "issue",
    "confused",
    "worried",
    "afraid",
    "scared",
    "hurt",
    "pain",
    "stress",
    "stressed",
    "anxious",
    "panic",
    "overwhelmed",
    "sad",
    "lost",
    "hopeless",
    "lonely",
    "trapped",
    "career",
    "job",
    "work",
    "relationship",
    "friend",
    "family",
    "partner",
    "fight",
    "money",
    "debt",
    "rent",
    "decision",
    "should i",
    "do not know what to do",
    "don't know what to do",
    "cannot sleep",
    "can't sleep",
    "burnout",
    "argued",
    "pressure",
    "struggling",
    "suffering",
    "need guidance",
    "routine",
    "charging",
    "battery",
    "study",
    "productivity",
    "schedule",
]

REFLECTIVE_CUES = [
    "i feel",
    "i am feeling",
    "i'm feeling",
    "i do not know",
    "i don't know",
    "i am stuck",
    "i'm stuck",
    "i am not sure",
    "i'm not sure",
    "what should i do",
    "how do i",
]


def normalize_personality_mode(personality_mode: str) -> str:
    return "life"


def classify_conversation_mode(lowered: str) -> str:
    stripped = lowered.strip()
    if stripped in CASUAL_PHRASES:
        return "casual"
    if len(lowered.split()) <= 6 and any(phrase in lowered for phrase in CASUAL_PHRASES) and not any(
        marker in lowered for marker in PROBLEM_MARKERS
    ):
        return "casual"
    if any(marker in lowered for marker in PROBLEM_MARKERS):
        return "problem_solving"
    if any(cue in lowered for cue in REFLECTIVE_CUES):
        return "problem_solving"
    if "?" in lowered or stripped.startswith(QUESTION_STARTERS):
        return "problem_solving"
    if len(lowered.split()) >= 8:
        return "problem_solving"
    return "casual"


def detect_casual_kind(lowered: str) -> str:
    if any(phrase in lowered for phrase in ["hi", "hello", "hey", "good morning", "good evening", "good night"]):
        return "greeting"
    if any(phrase in lowered for phrase in ["how are you", "what's up", "whats up"]):
        return "check_in"
    if any(phrase in lowered for phrase in ["bye", "goodbye", "see you", "take care"]):
        return "goodbye"
    if any(phrase in lowered for phrase in ["thanks", "thank you", "thx"]):
        return "gratitude"
    if any(phrase in lowered for phrase in ["who are you", "what can you do"]):
        return "identity"
    return "general_chat"


def needs_clarification(lowered: str, topic: str, situation_details: list[str]) -> bool:
    if len(lowered.split()) >= 16:
        return False
    if "?" in lowered or lowered.startswith(
        ("what ", "how ", "why ", "when ", "where ", "which ", "can ", "should ", "is ", "are ", "do ")
    ):
        return False
    if topic == "general":
        return len(lowered.split()) <= 5
    if topic in {"health", "tech", "home", "schedule", "productivity", "food", "study"}:
        return False
    if topic in {"career", "relationship", "money", "stress"} and not situation_details:
        return True
    return False


def detect_emotional_tone(lowered: str) -> str:
    if any(word in lowered for word in ["headache", "fever", "cold", "cough", "pain", "allergy"]):
        return "concerned"
    if any(word in lowered for word in ["stress", "anxious", "panic", "overwhelmed"]):
        return "stressed"
    if any(word in lowered for word in ["sad", "lost", "hopeless", "empty"]):
        return "low"
    if any(word in lowered for word in ["angry", "fight", "frustrated", "resent"]):
        return "frustrated"
    if any(word in lowered for word in ["excited", "hopeful", "motivated"]):
        return "hopeful"
    return "reflective"