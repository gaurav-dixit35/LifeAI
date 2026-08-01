from __future__ import annotations

from typing import Any


def apply_quality_guardrails(analysis: dict[str, Any], user_message: str) -> dict[str, Any]:
    topic = str(analysis.get("_topic", "general"))
    situation_details = list(analysis.get("_situation_details", []))
    lowered = user_message.lower()

    if analysis.get("conversation_mode") == "casual":
        return analysis

    if not analysis.get("suggestions"):
        analysis["suggestions"] = [
            "Keep the next step small and practical.",
            "Choose the easiest useful action you can do today.",
        ]

    if not analysis.get("action_plan"):
        analysis["action_plan"] = [
            "Name the real problem in one sentence.",
            "Pick one low-risk step you can do today.",
            "Review what changed after that step.",
        ]

    if not analysis.get("immediate_actions"):
        analysis["immediate_actions"] = analysis["action_plan"][:2]

    if not analysis.get("next_best_step"):
        analysis["next_best_step"] = analysis["action_plan"][0]

    if topic == "general":
        analysis["decision_lens"] = (
            "Treat this like a practical daily-life question first: identify the exact friction, choose one simple action, and only then decide whether you need a bigger plan."
        )
        analysis["follow_up_question"] = (
            "What outcome do you want most here: a quick fix, a better routine, a calmer decision, or a long-term plan?"
        )
        analysis["problem_summary"] = (
            "Here is the grounded read: this sounds like a real daily-life problem that needs a practical answer, even if it does not fit a narrow category yet."
        )
        if not situation_details:
            analysis["core_issue"] = (
                "The real difficulty is that the problem is still broad, so the best move is to define the exact friction point before trying to solve everything at once."
            )

    if any(phrase in lowered for phrase in ["everyday", "daily life", "routine", "habit", "practical"]) and topic == "general":
        analysis["suggestions"] = [
            "Start with the smallest repeatable improvement, not the perfect system.",
            "Remove one friction point before adding a new habit.",
            "Track whether the change actually makes the next day easier.",
        ]

    if topic in {"study", "productivity"}:
        analysis["follow_up_question"] = "What is the exact part that keeps breaking down: focus, energy, time planning, or consistency?"
        analysis["response_strategy"] = "Turn the problem into one realistic system change instead of a motivation speech."

    if topic == "food":
        analysis["follow_up_question"] = "Is your main goal here energy, health, weight control, or a routine you can actually maintain?"
        analysis["response_strategy"] = "Keep the answer practical, sustainable, and easy to follow in ordinary life."

    return analysis