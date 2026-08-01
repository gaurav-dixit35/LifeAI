from __future__ import annotations

from typing import Any


def build_compact_lead(topic: str, emotional_tone: str, personality_mode: str) -> str:
    if topic == "health":
        return "This sounds like a day-to-day health issue, so start with the simplest safe fix."
    if topic == "tech":
        return "This looks like a practical tech issue, so the answer is troubleshooting, not overthinking."
    if topic == "home":
        return "This looks like an everyday practical problem."
    if topic == "schedule":
        return "This looks like a timing problem that can still be recovered."
    if topic == "study":
        return "This looks like a study-structure problem more than a motivation failure."
    if topic == "productivity":
        return "This looks like a focus and friction problem, which means a simpler next move will help more than more pressure."
    if topic == "food":
        return "This looks like a routine and consistency problem, not something that needs an extreme reset."
    if emotional_tone == "stressed":
        return "This looks manageable, but you need a calmer next move."
    if emotional_tone == "low":
        return "This sounds heavy, so keep the next step simple."
    if topic == "career":
        return "This looks like a career decision problem, not a personal failure."
    if topic == "relationship":
        return "This looks like a relationship repair or boundary problem."
    if topic == "money":
        return "This looks like a practical money pressure problem."
    if topic == "stress":
        return "This looks like overload more than inability."
    if personality_mode == "friend":
        return "You do not need to solve everything at once."
    return "Here is the clearest next move."


def build_empathy_bridge(topic: str, emotional_tone: str, personality_mode: str) -> str:
    if emotional_tone == "stressed":
        return "Your message sounds loaded, which usually means your mind is trying to solve too much at once."
    if emotional_tone == "low":
        return "This sounds emotionally heavy, so the problem is not only the situation itself but also the weight it is putting on you."
    if emotional_tone == "frustrated":
        return "There is a lot of activation in this, which usually means something important feels crossed, unfair, or unresolved."
    if topic == "relationship":
        return "Relationship problems hit hard because they affect emotion, trust, and identity at the same time."
    if topic == "money":
        return "Money stress can make every option feel more dangerous than it really is, which is why calm structure matters here."
    if topic == "career":
        return "Career pressure is rarely just about work. It often touches security, self-respect, and future identity all at once."
    if topic == "study":
        return "Study pressure often mixes workload, self-expectation, and fear about the future, so clear structure matters."
    if topic == "productivity":
        return "When life feels scattered, the problem is often too much friction and not enough structure."
    if personality_mode == "friend":
        return "I am with you in this, and I am going to keep the advice practical and kind."
    return "I am treating this like a real human problem, not just text to analyze."


def build_profile_note(summary: str) -> str:
    if not summary or summary == "No established personal pattern yet.":
        return "There is not enough long-term history yet, so I am focusing mostly on the current situation."
    return summary


def build_pattern_notes(pattern_signals: list[dict[str, str]]) -> str:
    if not pattern_signals:
        return "No major recurring pattern is strong enough yet. This conversation is being treated mostly as a standalone decision."
    lines = [
        f"- {signal.get('title', 'Pattern')}: {signal.get('detail', '')}"
        for signal in pattern_signals[:2]
    ]
    return "\n".join(lines)


def build_decision_frame(topic: str, situation_details: list[str]) -> str:
    if topic == "career":
        return "Judge the choice by runway, growth, self-respect, and how sustainable the current path is over the next three months."
    if topic == "relationship":
        return "Judge the next move by honesty, emotional safety, and whether the relationship can support repair instead of repeating the same injury."
    if topic == "money":
        return "Judge the decision by stability first, then flexibility, then long-term improvement. Survival pressure should be handled before optimization."
    if topic == "stress":
        return "Judge the situation by what truly requires action now versus what only feels urgent because your system is overloaded."
    if topic == "study":
        return "Judge the plan by whether it helps you actually complete focused work, not by how ambitious it sounds."
    if topic == "productivity":
        return "Judge the next move by whether it reduces friction and helps you start sooner."
    if "decision" in situation_details:
        return "Judge the options by reversibility, information gained, and emotional cost rather than by trying to predict the whole future."
    return "Judge the next step by how much clarity, calm, and real-world feedback it creates."


def build_next_best_step(topic: str, situation_details: list[str]) -> str:
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            return "Write the staying plan and the leaving plan side by side, then compare risk, energy, and financial runway."
        if "interview" in situation_details:
            return "Prepare three proof-based stories that show competence, growth, and fit for the role."
        return "Write down your top two career options and score them on stability, growth, and energy."
    if topic == "relationship":
        if "fight" in situation_details:
            return "Draft a calm repair message before speaking again so the next conversation starts cleanly."
        if "trust" in situation_details:
            return "Write the specific evidence and behavior changes you would need before trust can feel real again."
        return "Decide the one honest conversation or boundary that would create the most clarity."
    if topic == "money":
        if "debt" in situation_details:
            return "List minimum obligations, urgent deadlines, and one action that buys you more breathing room this week."
        if "rent" in situation_details:
            return "Map the rent deadline, available cash, and the fastest stabilizing move you can make today."
        return "Turn the money problem into visible numbers before making any emotional decision."
    if topic == "stress":
        if "can't sleep" in situation_details:
            return "Protect tonight's recovery first, because tired thinking will distort tomorrow's decisions."
        if "burnout" in situation_details:
            return "Remove one draining obligation and reduce the day to one meaningful task plus recovery."
        return "Lower the pressure in your body first, then choose the one issue that actually needs action today."
    if topic == "study":
        return "Choose the exact topic or task for your next focused study block and start there."
    if topic == "productivity":
        return "Pick one real task, remove the biggest distraction, and start a short focus block before re-evaluating."
    if topic == "food":
        return "Plan the next balanced meal or snack you can actually follow through on today."
    if "decision" in situation_details:
        return "Write the top two options and one low-risk experiment that gives you more information."
    return "Write the real problem in one or two plain sentences so you can stop solving it vaguely."


def build_tailored_solution(topic: str, situation_details: list[str], personality_mode: str) -> str:
    tone_prefix = "The most useful answer here is to stop trying to solve everything at once and focus on the real lever."
    if personality_mode == "friend":
        tone_prefix = "Take a breath first. The best answer here is simpler than the panic makes it seem."
    if topic == "health":
        if "headache" in situation_details:
            return (
                f"{tone_prefix} treat this like a practical body signal: step away from the likely trigger, hydrate, and rest a little. "
                "If it stays high or comes with stronger symptoms, get medical help."
            )
        return (
            f"{tone_prefix} start with the simplest safe relief step, reduce the likely trigger, and watch whether the symptom settles or escalates."
        )
    if topic == "tech":
        if "internet issue" in situation_details:
            return (
                f"{tone_prefix} check connection basics first, restart the network path once, and switch to a backup network if urgent work is blocked."
            )
        if "password issue" in situation_details:
            return (
                f"{tone_prefix} use the proper recovery method instead of repeated guesses, then store the reset safely once you regain access."
            )
        return (
            f"{tone_prefix} identify the exact failing point, try the most likely fix first, and protect important work with a backup before deeper troubleshooting."
        )
    if topic == "home":
        return (
            f"{tone_prefix} fix the immediate inconvenience first, use the safest temporary workaround, and then arrange the proper repair if it can repeat or cause damage."
        )
    if topic == "schedule":
        return (
            f"{tone_prefix} recover the next important step quickly, inform anyone affected if needed, and then fix the one weak point that caused the delay."
        )
    if topic == "study":
        return (
            f"{tone_prefix} stop measuring yourself by the full syllabus right now. Choose the highest-priority topic, study it in one focused block, and let consistency beat panic."
        )
    if topic == "productivity":
        return (
            f"{tone_prefix} reduce the number of active goals, remove the biggest distraction, and make the next task so small that starting feels easier than avoiding it."
        )
    if topic == "food":
        return (
            f"{tone_prefix} make the next meal practical and balanced, then build a simple repeatable eating pattern instead of trying to fix everything with extreme rules."
        )
    if topic == "career":
        if "switch job" in situation_details or "leave job" in situation_details:
            return (
                f"{tone_prefix} stop asking only whether you feel bad right now. Build a side-by-side comparison of staying versus leaving: "
                "financial runway, growth, emotional cost, and what each option looks like in 90 days. "
                "If staying gives only fear and no path, leaving deserves serious weight. If leaving is mainly an escape fantasy, test alternatives first."
            )
        if "interview" in situation_details:
            return (
                f"{tone_prefix} narrow the problem to preparation. Write three strong stories that prove competence, impact, and adaptability. "
                "Practice them out loud until your nervous system stops treating the interview like a verdict on your worth."
            )
        return (
            f"{tone_prefix} define three criteria for your next career move, rank your current options against them, and choose the option that improves both stability and direction instead of only reducing discomfort."
        )
    if topic == "relationship":
        if "fight" in situation_details:
            return (
                f"{tone_prefix} do not restart the conversation in the same emotional state. Write what hurt, what you own, and what you need next. "
                "Then have one calm conversation focused on repair, not replay."
            )
        if "trust" in situation_details:
            return (
                f"{tone_prefix} stop asking whether you wish trust existed and ask what evidence would prove it. "
                "If the other person cannot meet clear conditions over time, the answer is already forming."
            )
        return (
            f"{tone_prefix} prepare one honest, non-accusatory conversation with a clear boundary and a clear ask. Relationships improve when the message gets cleaner, not louder."
        )
    if topic == "money":
        if "debt" in situation_details:
            return (
                f"{tone_prefix} break the problem into three layers: what must be paid now, what can be negotiated, and what change prevents repeat pressure next month. "
                "That sequence creates breathing room and restores control."
            )
        if "rent" in situation_details:
            return (
                f"{tone_prefix} prioritize the housing deadline first, map every available source of cash or support, and make the fastest stabilizing move before trying to solve the entire financial picture."
            )
        return (
            f"{tone_prefix} convert the problem into a visible cash map, identify the largest constraint, and act on the one change that most improves short-term stability."
        )
    if topic == "stress":
        if "can't sleep" in situation_details:
            return (
                f"{tone_prefix} treat recovery as part of the solution. Reduce unnecessary inputs, protect sleep, and postpone major decisions until your body is less activated."
            )
        if "burnout" in situation_details:
            return (
                f"{tone_prefix} remove at least one draining obligation, lower the expectation that everything must be handled at once, and rebuild from recovery plus one meaningful priority."
            )
        return (
            f"{tone_prefix} reduce the number of active problems, regulate your nervous system first, and then solve one concrete issue from a calmer state."
        )
    if "decision" in situation_details:
        return (
            f"{tone_prefix} define the top two options, name the real fear inside each one, and run one low-risk experiment that gives you information instead of forcing a blind final decision."
        )
    return (
        f"{tone_prefix} simplify the problem, choose the next action that creates clarity, and avoid trying to solve every future consequence in one sitting."
    )


def compose_clarifying_reply(analysis: dict[str, Any]) -> str:
    return (
        "I can help, but I need one detail first.\n\n"
        f"{analysis['follow_up_question']}\n\n"
        f"For now: {analysis['next_best_step']}"
    )
