from __future__ import annotations

import json
from typing import Any

from config import settings
from services.confidence_engine import ConfidenceEngine
from services.life_ai import (
    apply_quality_guardrails,
    build_action_plan,
    build_avoid_now,
    build_compact_lead,
    build_decision_frame,
    build_decision_lens,
    build_empathy_bridge,
    build_follow_up_question,
    build_hidden_risks,
    build_immediate_actions,
    build_long_term_actions,
    build_next_best_step,
    build_pattern_notes,
    build_personalized_guidance_note,
    build_profile_note,
    build_response_strategy,
    build_safety_notes,
    build_short_term_actions,
    build_suggestions,
    build_tailored_solution,
    build_when_to_seek_support,
    classify_conversation_mode,
    compose_clarifying_reply,
    detect_casual_kind,
    detect_emotional_tone,
    detect_needs,
    extract_situation_details,
    infer_strengths,
    needs_clarification,
    normalize_personality_mode,
    recommendation_for,
    topic_key,
    urgency_label,
)
from services.risk_engine import RiskEngine


class LLMService:
    def __init__(self) -> None:
        self.risk_engine = RiskEngine()
        self.confidence_engine = ConfidenceEngine()

    def _normalize_personality_mode(self, personality_mode: str) -> str:
        return normalize_personality_mode(personality_mode)

    async def generate_analysis(
        self,
        *,
        user_message: str,
        context: str,
        personality_mode: str,
        pattern_signals: list[dict[str, str]],
        user_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        personality_mode = self._normalize_personality_mode(personality_mode)
        baseline = self._build_local_analysis(
            user_message=user_message,
            personality_mode=personality_mode,
            pattern_signals=pattern_signals,
            user_profile=user_profile or {},
        )

        if settings.ENABLE_EXTERNAL_LLM and settings.HUGGINGFACE_API_KEY:
            try:
                if baseline.get("conversation_mode") == "casual":
                    external_analysis = await self._call_huggingface_casual(
                        user_message=user_message,
                        context=context,
                        personality_mode=personality_mode,
                        baseline=baseline,
                        user_profile=user_profile or {},
                    )
                else:
                    external_analysis = await self._call_huggingface(
                        user_message=user_message,
                        context=context,
                        personality_mode=personality_mode,
                        pattern_signals=pattern_signals,
                        baseline=baseline,
                        user_profile=user_profile or {},
                    )
                return self._merge_analysis(baseline, external_analysis)
            except Exception:
                pass

        return baseline

    def _build_local_analysis(
        self,
        *,
        user_message: str,
        personality_mode: str,
        pattern_signals: list[dict[str, str]],
        user_profile: dict[str, Any],
    ) -> dict[str, Any]:
        lowered = user_message.lower()
        conversation_mode = self._classify_conversation_mode(lowered)
        casual_kind = self._detect_casual_kind(lowered)

        if conversation_mode == "casual":
            return self._build_casual_analysis(
                user_message=user_message,
                personality_mode=personality_mode,
                casual_kind=casual_kind,
            )

        emotional_tone = self._detect_emotional_tone(lowered)
        risk_level = self.risk_engine.score(user_message)
        urgency_label = self._urgency_label(risk_level)
        recommendation = self._recommendation_for(risk_level)
        topic = self._topic_key(lowered)
        situation_details = self._extract_situation_details(lowered)
        detected_needs = self._detect_needs(lowered, topic, situation_details, risk_level)
        response_strategy = self._build_response_strategy(topic, detected_needs, urgency_label)
        decision_lens = self._build_decision_lens(topic, situation_details, risk_level)
        suggestions = self._build_suggestions(lowered, personality_mode, topic, situation_details)
        action_plan = self._build_action_plan(lowered, topic, situation_details)
        immediate_actions = self._build_immediate_actions(topic, situation_details, risk_level)
        short_term_actions = self._build_short_term_actions(topic, situation_details)
        long_term_actions = self._build_long_term_actions(topic, situation_details)
        avoid_now = self._build_avoid_now(topic, situation_details, risk_level)
        safety_notes = self._build_safety_notes(risk_level)
        when_to_seek_support = self._build_when_to_seek_support(topic, risk_level, situation_details)
        strengths = self._infer_strengths(lowered)
        hidden_risk_factors = self._build_hidden_risks(lowered, risk_level)
        core_issue = self._build_core_issue(lowered, topic, situation_details)
        next_best_step = self._build_next_best_step(topic, situation_details)
        continuity_note = str(user_profile.get("continuity_note", ""))
        personalization_note = self._build_personalized_guidance_note(user_profile, topic)
        unresolved_threads = list(user_profile.get("unresolved_threads", []))[:3]
        progress_signals = list(user_profile.get("progress_signals", []))[:3]
        follow_up_question = self._build_follow_up_question(topic, situation_details, detected_needs, lowered)
        tools = [
            {
                "name": "Decision journal",
                "description": "Write what happened, what you feel, and your next move.",
                "required": True,
            },
            {
                "name": "Mood check-in",
                "description": "Rate your emotional state before and after decisions.",
                "required": True,
            },
            {
                "name": "Support circle",
                "description": "Reach out to one trusted person when decisions feel heavy.",
                "required": False,
            },
        ]
        reflection_prompt = "What would a calmer version of you want to notice before making the next decision?"
        confidence_score = self.confidence_engine.score(
            message=user_message,
            conversation_mode=conversation_mode,
            risk_level=risk_level,
            action_plan=action_plan,
            safety_notes=safety_notes,
            pattern_signals=pattern_signals,
            follow_up_question=follow_up_question,
        )

        summary = self._build_summary(
            lowered=lowered,
            topic=topic,
            emotional_tone=emotional_tone,
            personality_mode=personality_mode,
            situation_details=situation_details,
        )

        analysis = {
            "conversation_mode": "problem_solving",
            "problem_summary": summary,
            "core_issue": core_issue,
            "emotional_tone": emotional_tone,
            "urgency_label": urgency_label,
            "response_strategy": response_strategy,
            "risk_level": risk_level,
            "confidence_score": confidence_score,
            "recommendation": recommendation,
            "detected_needs": detected_needs,
            "strengths": strengths,
            "hidden_risk_factors": hidden_risk_factors,
            "decision_lens": decision_lens,
            "suggestions": suggestions,
            "action_plan": action_plan,
            "immediate_actions": immediate_actions,
            "short_term_actions": short_term_actions,
            "long_term_actions": long_term_actions,
            "avoid_now": avoid_now,
            "next_best_step": next_best_step,
            "follow_up_question": follow_up_question,
            "reflection_prompt": reflection_prompt,
            "pattern_signals": pattern_signals,
            "tools": tools,
            "safety_notes": safety_notes,
            "when_to_seek_support": when_to_seek_support,
            "personalization_note": personalization_note,
            "continuity_note": continuity_note,
            "unresolved_threads": unresolved_threads,
            "progress_signals": progress_signals,
            "_topic": topic,
            "_situation_details": situation_details,
            "_original_message": user_message,
            "_user_profile_summary": user_profile.get("summary", ""),
            "_needs_clarification": self._needs_clarification(lowered, topic, situation_details),
        }
        return self._apply_quality_guardrails(analysis, user_message)

    def _apply_quality_guardrails(self, analysis: dict[str, Any], user_message: str) -> dict[str, Any]:
        return apply_quality_guardrails(analysis, user_message)

    def compose_reply(self, analysis: dict[str, Any], personality_mode: str) -> str:
        personality_mode = self._normalize_personality_mode(personality_mode)
        if analysis.get("conversation_mode") == "casual":
            return self._compose_casual_reply(analysis, personality_mode)
        if analysis.get("_needs_clarification"):
            return compose_clarifying_reply(analysis)

        topic = str(analysis.get("_topic", "general"))
        situation_details = list(analysis.get("_situation_details", []))
        tailored_solution = build_tailored_solution(topic, situation_details, personality_mode)
        solution_steps = analysis.get("immediate_actions") or analysis.get("action_plan") or [analysis["next_best_step"]]
        compact_steps = "\n".join(
            f"{index + 1}. {step}"
            for index, step in enumerate(solution_steps[:3])
        )
        lead = build_compact_lead(
            topic=topic,
            emotional_tone=str(analysis.get("emotional_tone", "reflective")),
            personality_mode=personality_mode,
        )
        return (
            f"{lead}\n\n"
            f"Best solution:\n{tailored_solution}\n\n"
            f"Do this now:\n{compact_steps}"
        )

    def _build_casual_analysis(
        self,
        *,
        user_message: str,
        personality_mode: str,
        casual_kind: str,
    ) -> dict[str, Any]:
        reply_prompt = {
            "greeting": "The user is greeting the assistant and opening a normal conversation.",
            "check_in": "The user is making light small talk or asking how the assistant is doing.",
            "gratitude": "The user is expressing thanks or appreciation.",
            "identity": "The user is asking what the assistant is or what it can do.",
            "general_chat": "The user is talking casually and does not appear to be asking for deep advice.",
        }.get(casual_kind, "The user is speaking casually.")

        analysis = {
            "conversation_mode": "casual",
            "problem_summary": f"{reply_prompt} No serious problem or decision-risk signal is currently dominant.",
            "core_issue": "No major problem was detected in this message. A normal conversational reply is more appropriate than a solution plan.",
            "emotional_tone": "warm",
            "urgency_label": "low",
            "response_strategy": "Respond casually, stay warm, and invite deeper conversation only if the user wants it.",
            "risk_level": 3,
            "confidence_score": 96,
            "recommendation": "steady",
            "detected_needs": ["connection", "conversation"],
            "strengths": [
                "You are opening the conversation naturally.",
                "Your message does not show immediate distress or high-risk pressure.",
            ],
            "hidden_risk_factors": [
                "No major hidden risk stands out from this message alone.",
            ],
            "decision_lens": "A normal conversational reply is more useful than a problem-solving framework here.",
            "suggestions": [
                "Keep the conversation going naturally.",
                "Share more detail if you want advice, analysis, or support.",
            ],
            "action_plan": [
                "Continue the conversation in a normal way.",
            ],
            "immediate_actions": [
                "Reply casually and keep the interaction light unless the user asks for help.",
            ],
            "short_term_actions": [
                "Invite the user to share more if they want advice or deeper support.",
            ],
            "long_term_actions": [
                "Build trust through natural conversation so deeper topics feel safe to discuss later.",
            ],
            "avoid_now": [
                "Do not force a heavy analysis when the user is only opening normal conversation.",
            ],
            "next_best_step": "Reply naturally and invite the user to continue.",
            "follow_up_question": "What would you like to talk about?",
            "reflection_prompt": "If you want deeper help, tell me what is actually on your mind right now.",
            "pattern_signals": [],
            "tools": [],
            "safety_notes": [],
            "when_to_seek_support": [],
            "personalization_note": "A normal conversational response is the best fit here.",
            "continuity_note": "No deeper continuity signal is needed for light conversation.",
            "unresolved_threads": [],
            "progress_signals": [],
            "_casual_kind": casual_kind,
            "_original_message": user_message,
        }
        return analysis

    def _compose_casual_reply(self, analysis: dict[str, Any], personality_mode: str) -> str:
        model_reply = str(analysis.get("casual_reply", "")).strip()
        if model_reply:
            return model_reply

        lowered = str(analysis.get("_original_message", "")).lower().strip()
        casual_kind = str(analysis.get("_casual_kind", "general_chat"))

        if casual_kind == "greeting":
            if personality_mode == "friend":
                return "Hey! I am here with you. How are you feeling today?"
            if personality_mode == "mentor":
                return "Hello. I am here and ready to talk. What is on your mind today?"
            return "Hi! I am here. What would you like to talk about today?"

        if casual_kind == "check_in":
            if "how are you" in lowered:
                return "I am doing well and ready to help. How are you doing today?"
            return "I am here and listening. Tell me what is on your mind."

        if casual_kind == "goodbye":
            return "Take care. I am here whenever you want to talk again."

        if casual_kind == "gratitude":
            return "You are welcome. I am glad to help. If you want, we can keep talking."

        if casual_kind == "identity":
            return (
                "I am LifeAI, your chat companion for normal conversation, emotional clarity, and real-life problem solving. "
                "You can talk casually with me, or describe a real problem and I will switch into deeper guidance."
            )

        return "I am here with you. We can chat normally, or if something is bothering you, tell me and I will help you think through it."

    def _compose_clarifying_reply(self, analysis: dict[str, Any], personality_mode: str) -> str:
        return (
            "I can help, but I need one detail first.\n\n"
            f"{analysis['follow_up_question']}\n\n"
            f"For now: {analysis['next_best_step']}"
        )

    def _build_compact_lead(self, *, topic: str, emotional_tone: str, personality_mode: str) -> str:
        if topic == "health":
            return "This sounds like a day-to-day health issue, so start with the simplest safe fix."
        if topic == "tech":
            return "This looks like a practical tech issue, so the answer is troubleshooting, not overthinking."
        if topic == "home":
            return "This looks like an everyday practical problem."
        if topic == "schedule":
            return "This looks like a timing problem that can still be recovered."
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

    def _classify_conversation_mode(self, lowered: str) -> str:
        return classify_conversation_mode(lowered)

    def _detect_casual_kind(self, lowered: str) -> str:
        return detect_casual_kind(lowered)

    def _needs_clarification(self, lowered: str, topic: str, situation_details: list[str]) -> bool:
        return needs_clarification(lowered, topic, situation_details)

    def _detect_needs(self, lowered: str, topic: str, situation_details: list[str], risk_level: int) -> list[str]:
        return detect_needs(lowered, topic, situation_details, risk_level)

    def _build_response_strategy(self, topic: str, detected_needs: list[str], urgency_label: str) -> str:
        return build_response_strategy(topic, detected_needs, urgency_label)

    def _build_decision_lens(self, topic: str, situation_details: list[str], risk_level: int) -> str:
        return build_decision_lens(topic, situation_details, risk_level)

    def _build_follow_up_question(
        self,
        topic: str,
        situation_details: list[str],
        detected_needs: list[str],
        lowered: str,
    ) -> str:
        return build_follow_up_question(topic, situation_details, detected_needs, lowered)

    def _urgency_label(self, risk_level: int) -> str:
        return urgency_label(risk_level)

    def _build_empathy_bridge(self, topic: str, emotional_tone: str, personality_mode: str) -> str:
        return build_empathy_bridge(topic, emotional_tone, personality_mode)

    def _build_profile_note(self, summary: str) -> str:
        return build_profile_note(summary)

    def _build_personalized_guidance_note(self, user_profile: dict[str, Any], topic: str) -> str:
        return build_personalized_guidance_note(user_profile, topic)

    def _build_suggestions(self, lowered: str, personality_mode: str, topic: str, situation_details: list[str]) -> list[str]:
        return build_suggestions(lowered, personality_mode, topic, situation_details)

    def _build_action_plan(self, lowered: str, topic: str, situation_details: list[str]) -> list[str]:
        return build_action_plan(topic, situation_details)

    def _build_immediate_actions(self, topic: str, situation_details: list[str], risk_level: int) -> list[str]:
        return build_immediate_actions(topic, situation_details, risk_level)

    def _build_short_term_actions(self, topic: str, situation_details: list[str]) -> list[str]:
        return build_short_term_actions(topic, situation_details)

    def _build_long_term_actions(self, topic: str, situation_details: list[str]) -> list[str]:
        return build_long_term_actions(topic)

    def _build_avoid_now(self, topic: str, situation_details: list[str], risk_level: int) -> list[str]:
        return build_avoid_now(topic, risk_level)

    def _build_when_to_seek_support(self, topic: str, risk_level: int, situation_details: list[str]) -> list[str]:
        return build_when_to_seek_support(topic, risk_level, situation_details)

    def _build_safety_notes(self, risk_level: int) -> list[str]:
        return build_safety_notes(risk_level)

    def _recommendation_for(self, risk_level: int) -> str:
        return recommendation_for(risk_level)

    def _detect_emotional_tone(self, lowered: str) -> str:
        return detect_emotional_tone(lowered)

    def _topic_key(self, lowered: str) -> str:
        return topic_key(lowered)

    def _build_summary(
        self,
        *,
        lowered: str,
        topic: str,
        emotional_tone: str,
        personality_mode: str,
        situation_details: list[str],
    ) -> str:
        mode_prefix = {
            "life": "Here is the grounded read:",
            "coach": "Here is the grounded read:",
            "friend": "Here is what I think you are carrying:",
            "mentor": "Here is the signal beneath the noise:",
        }.get(personality_mode, "Here is the grounded read:")
        topic_summary = {
            "career": "you are trying to make a career decision while carrying pressure, uncertainty, and a fear of getting the next move wrong",
            "relationship": "you are dealing with relationship tension where emotion is interfering with clean communication",
            "money": "you are carrying financial pressure that is making the problem feel heavier than the numbers alone",
            "stress": "your nervous system sounds overloaded, which makes every decision feel bigger and less manageable",
            "health": "you are dealing with a day-to-day health symptom that needs the simplest sensible response first",
            "tech": "you are dealing with a practical device or connection problem that needs troubleshooting, not overthinking",
            "home": "you are dealing with an everyday home inconvenience that needs a clear practical fix",
            "schedule": "you are dealing with a timing or logistics slip that can still be stabilized",
            "study": "you are trying to build a study system that is realistic enough to survive a normal week",
            "productivity": "you are trying to reduce friction and wasted time so your day feels more intentional",
            "food": "you are trying to make a practical food or energy choice that is sustainable in daily life",
            "general": "the situation feels emotionally noisy, so clarity is getting lost inside urgency and overthinking",
        }[topic]
        if topic == "career" and "switch job" in situation_details:
            topic_summary = "you are weighing whether to stay or leave while trying not to damage stability or self-trust"
        if topic == "relationship" and "fight" in situation_details:
            topic_summary = "you are trying to respond to conflict without making the relationship worse"
        if topic == "money" and "debt" in situation_details:
            topic_summary = "you are under debt pressure, which is likely shrinking your emotional and decision-making bandwidth"
        if topic == "stress" and "can't sleep" in situation_details:
            topic_summary = "stress is spilling into your body and sleep, which means your mind may be overestimating threat"
        tone_suffix = {
            "concerned": "The immediate need is a calm practical response, not panic.",
            "stressed": "The immediate need is regulation before deeper problem-solving.",
            "low": "The emotional weight itself is part of the decision problem.",
            "frustrated": "There is likely a boundary, expectation, or unresolved resentment underneath it.",
            "hopeful": "There is useful energy here, but it needs direction.",
            "reflective": "You already have insight; the next step is turning it into action.",
        }[emotional_tone]
        return f"{mode_prefix} It looks like {topic_summary}. {tone_suffix}"

    def _build_core_issue(self, lowered: str, topic: str, situation_details: list[str]) -> str:
        if topic == "health":
            return "The real difficulty is figuring out whether this needs a simple relief step, rest, or proper medical attention."
        if topic == "tech":
            return "The real difficulty is identifying the most likely technical cause quickly instead of troubleshooting randomly."
        if topic == "home":
            return "The real difficulty is solving today's inconvenience safely without letting it become a bigger repair problem."
        if topic == "schedule":
            return "The real difficulty is recovering control quickly so one slip does not damage the rest of the day."
        if topic == "career":
            if "switch job" in situation_details or "leave job" in situation_details:
                return "The real difficulty is not simply whether to leave. It is deciding how much discomfort is healthy growth versus a sign that staying is costing too much."
            if "interview" in situation_details:
                return "The real difficulty is performing under judgment while your self-worth is trying to attach itself to the result."
            return "The real difficulty is not only choosing a job path. It is making that choice while trying to protect identity, security, and future regret at the same time."
        if topic == "relationship":
            if "fight" in situation_details:
                return "The real difficulty is not just the disagreement. It is deciding how to repair trust without abandoning your own emotional truth."
            if "trust" in situation_details:
                return "The real difficulty is determining whether this relationship problem can be repaired or whether you are trying to force safety where it no longer exists."
            return "The real difficulty is balancing honesty with safety, so you can speak clearly without escalating the conflict."
        if topic == "money":
            if "debt" in situation_details:
                return "The real difficulty is that debt pressure turns every choice into a threat signal, making calm planning harder than the numbers alone justify."
            if "rent" in situation_details:
                return "The real difficulty is short-term survival pressure, which can crowd out longer-term thinking and make every hour feel urgent."
            return "The real difficulty is that financial pressure is shrinking your emotional bandwidth, so every option feels more threatening than it is."
        if topic == "stress":
            if "can't sleep" in situation_details:
                return "The real difficulty is that your body is no longer resetting properly, so your mind is trying to solve life from a depleted state."
            return "The real difficulty is that your mind is trying to solve too many things while your body is already in a high-alert state."
        return "The real difficulty is turning a vague, emotionally loaded situation into one clear problem that can actually be handled."

    def _extract_situation_details(self, lowered: str) -> list[str]:
        return extract_situation_details(lowered)

    def _build_practical_read(self, topic: str, situation_details: list[str]) -> str:
        if topic == "career":
            if "switch job" in situation_details or "leave job" in situation_details:
                return (
                    "This is a stay-versus-leave decision. The answer is usually not hidden in emotion alone. "
                    "It comes from comparing whether the job is still building your future or mainly draining your stability."
                )
            if "interview" in situation_details:
                return (
                    "This is partly a preparation problem and partly a pressure problem. You do not need a perfect performance. "
                    "You need a clear story, relevant proof, and calmer execution."
                )
            return (
                "This sounds like a direction problem rather than a motivation problem. "
                "You need clearer criteria for what good work should feel like and what trade-offs are acceptable."
            )
        if topic == "relationship":
            if "fight" in situation_details:
                return (
                    "This is not only about who is right. It is about repairing the conversation without abandoning your point of view. "
                    "The quality of the next interaction matters more than winning the last one."
                )
            if "trust" in situation_details:
                return (
                    "This is a trust assessment problem. Before deciding the future of the relationship, you need evidence, consistency, "
                    "and a clear boundary around what trust would actually require."
                )
            return (
                "This sounds like a communication and boundary problem. The solution is likely a calmer, more precise conversation, not more silent overthinking."
            )
        if topic == "money":
            if "debt" in situation_details:
                return (
                    "Debt pressure makes everything feel urgent. The strongest move is to separate immediate survival, debt containment, "
                    "and longer-term recovery so the problem stops feeling like one giant threat."
                )
            if "rent" in situation_details:
                return (
                    "This is a housing stability problem first. Once the rent timeline is clear, the rest of the money decisions become much more manageable."
                )
            return (
                "This sounds like a financial clarity problem. The solution starts with removing vagueness and forcing the numbers to become visible."
            )
        if topic == "stress":
            if "can't sleep" in situation_details:
                return (
                    "The problem is no longer just mental. It has reached your body and sleep, which means your system needs recovery before it can judge clearly."
                )
            if "burnout" in situation_details:
                return (
                    "This looks like depletion, not laziness. You may be trying to fix exhaustion with more pressure, which usually makes judgment worse."
                )
            return (
                "This sounds like overload. The solution is to lower internal pressure first so the real priorities can separate themselves."
            )
        if "decision" in situation_details:
            return (
                "This is a decision clarity problem. Right now the issue is probably too foggy, which is why your mind keeps circling instead of choosing."
            )
        return (
            "This looks like a situation where emotional noise is hiding the actual decision. "
            "Once the real problem is named clearly, the next move becomes easier."
        )

    def _build_tailored_solution(self, topic: str, situation_details: list[str], personality_mode: str) -> str:
        return build_tailored_solution(topic, situation_details, personality_mode)

    def _build_decision_frame(self, topic: str, situation_details: list[str]) -> str:
        return build_decision_frame(topic, situation_details)

    def _build_pattern_notes(self, pattern_signals: list[dict[str, str]]) -> str:
        return build_pattern_notes(pattern_signals)

    def _build_next_best_step(self, topic: str, situation_details: list[str]) -> str:
        return build_next_best_step(topic, situation_details)

    def _infer_strengths(self, lowered: str) -> list[str]:
        return infer_strengths(lowered)

    def _build_hidden_risks(self, lowered: str, risk_level: int) -> list[str]:
        return build_hidden_risks(lowered, risk_level)

    async def _call_huggingface(
        self,
        *,
        user_message: str,
        context: str,
        personality_mode: str,
        pattern_signals: list[dict[str, str]],
        baseline: dict[str, Any],
        user_profile: dict[str, Any],
    ) -> dict[str, Any]:
        from huggingface_hub import InferenceClient

        system_prompt = (
            "You are LifeAI, an emotionally intelligent decision-support assistant. "
            "Return only valid JSON with no markdown, no commentary, and no code fences. "
            "The JSON must contain exactly these keys: "
            "conversation_mode, problem_summary, core_issue, emotional_tone, urgency_label, response_strategy, "
            "risk_level, confidence_score, recommendation, detected_needs, strengths, hidden_risk_factors, decision_lens, "
            "suggestions, action_plan, immediate_actions, short_term_actions, long_term_actions, avoid_now, next_best_step, "
            "follow_up_question, reflection_prompt, pattern_signals, tools, safety_notes, when_to_seek_support, "
            "personalization_note, continuity_note, unresolved_threads, progress_signals. "
            "Give concise but specific advice that is tailored to the user's actual situation. "
            "Do not return generic life advice. Keep recommendations emotionally aware, practical, and safe. "
            "Use one of these recommendation values only: steady, caution, support, urgent_support. "
            "Set conversation_mode to problem_solving for serious messages."
        )
        user_prompt = (
            f"Personality mode: {personality_mode}\n"
            f"Conversation context:\n{context or 'No prior context.'}\n\n"
            f"Detected recurring patterns:\n{json.dumps(pattern_signals, ensure_ascii=True)}\n\n"
            f"User profile summary:\n{json.dumps(user_profile, ensure_ascii=True)}\n\n"
            f"Baseline analysis to improve:\n{json.dumps(self._strip_private_fields(baseline), ensure_ascii=True)}\n\n"
            f"User message:\n{user_message}\n\n"
            "Improve the summary, core issue, response strategy, decision lens, detected needs, strengths, hidden risks, suggestions, "
            "action plan, immediate actions, short-term actions, long-term actions, what to avoid, support guidance, next best step, "
            "follow-up question, reflection prompt, personalization note, continuity note, unresolved threads, and progress signals "
            "so they are tightly matched to this exact problem. "
            "Keep the response grounded and therapeutically careful without pretending to diagnose."
        )

        client = InferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        response = client.chat_completion(
            model=settings.HF_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=settings.HF_MAX_TOKENS,
            temperature=settings.HF_TEMPERATURE,
        )
        content = response.choices[0].message.content or ""
        return self._parse_external_json(content)

    async def _call_huggingface_casual(
        self,
        *,
        user_message: str,
        context: str,
        personality_mode: str,
        baseline: dict[str, Any],
        user_profile: dict[str, Any],
    ) -> dict[str, Any]:
        from huggingface_hub import InferenceClient

        system_prompt = (
            "You are LifeAI, a warm, natural conversational assistant. "
            "Return only valid JSON with no markdown. "
            "The JSON must contain exactly these keys: "
            "conversation_mode, problem_summary, core_issue, emotional_tone, urgency_label, response_strategy, "
            "risk_level, confidence_score, recommendation, detected_needs, strengths, hidden_risk_factors, decision_lens, "
            "suggestions, action_plan, immediate_actions, short_term_actions, long_term_actions, avoid_now, next_best_step, "
            "follow_up_question, reflection_prompt, pattern_signals, tools, safety_notes, when_to_seek_support, "
            "personalization_note, continuity_note, unresolved_threads, progress_signals, casual_reply. "
            "Set conversation_mode to casual. "
            "Keep the casual_reply short, natural, human, and suitable for ordinary conversation."
        )
        user_prompt = (
            f"Personality mode: {personality_mode}\n"
            f"Recent context:\n{context or 'No prior context.'}\n\n"
            f"User profile:\n{json.dumps(user_profile, ensure_ascii=True)}\n\n"
            f"Baseline casual analysis:\n{json.dumps(self._strip_private_fields(baseline), ensure_ascii=True)}\n\n"
            f"User message:\n{user_message}\n\n"
            "Write a natural casual reply and keep all other fields compatible with the baseline."
        )

        client = InferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        response = client.chat_completion(
            model=settings.HF_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=min(settings.HF_MAX_TOKENS, 450),
            temperature=max(settings.HF_TEMPERATURE, 0.5),
        )
        content = response.choices[0].message.content or ""
        return self._parse_external_json(content)

    def _merge_analysis(self, baseline: dict[str, Any], external: dict[str, Any]) -> dict[str, Any]:
        merged = dict(baseline)

        text_fields = [
            "conversation_mode",
            "problem_summary",
            "core_issue",
            "emotional_tone",
            "urgency_label",
            "response_strategy",
            "decision_lens",
            "recommendation",
            "next_best_step",
            "follow_up_question",
            "reflection_prompt",
            "personalization_note",
            "continuity_note",
            "casual_reply",
        ]
        list_fields = [
            "detected_needs",
            "strengths",
            "hidden_risk_factors",
            "suggestions",
            "action_plan",
            "immediate_actions",
            "short_term_actions",
            "long_term_actions",
            "avoid_now",
            "pattern_signals",
            "tools",
            "safety_notes",
            "when_to_seek_support",
            "unresolved_threads",
            "progress_signals",
        ]

        for field in text_fields:
            value = external.get(field)
            if isinstance(value, str) and value.strip():
                merged[field] = value.strip()

        for field in list_fields:
            value = external.get(field)
            if isinstance(value, list) and value:
                merged[field] = value

        for field in ["risk_level", "confidence_score"]:
            value = external.get(field)
            if isinstance(value, int):
                merged[field] = max(0, min(100, value))

        if not merged.get("action_plan"):
            merged["action_plan"] = baseline["action_plan"]

        if not merged.get("next_best_step"):
            merged["next_best_step"] = baseline["next_best_step"]

        return merged

    def _parse_external_json(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if "\n" in cleaned:
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])

        raise ValueError("External model did not return valid JSON")

    def _strip_private_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        analysis = {key: value for key, value in payload.items() if not key.startswith("_")}
