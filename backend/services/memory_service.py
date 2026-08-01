from collections import Counter

from models.chat_model import Message


class MemoryService:
    def build_context(self, messages: list[Message], limit: int = 8) -> str:
        recent = messages[-limit:]
        return "\n".join(f"{message.role}: {message.content}" for message in recent)

    def extract_patterns(self, messages: list[Message]) -> list[dict[str, str]]:
        user_messages = [message.content.lower() for message in messages if message.role == "user"]
        if not user_messages:
            return []

        buckets = Counter()
        for text in user_messages:
            if any(word in text for word in ["career", "job", "work"]):
                buckets["career uncertainty"] += 1
            if any(word in text for word in ["stress", "anxious", "overwhelmed"]):
                buckets["stress spikes"] += 1
            if any(word in text for word in ["relationship", "friend", "partner", "family"]):
                buckets["relationship tension"] += 1
            if any(word in text for word in ["money", "finance", "debt"]):
                buckets["financial pressure"] += 1
            if any(word in text for word in ["decision", "choose", "choice", "what should i do"]):
                buckets["decision paralysis"] += 1
            if any(word in text for word in ["sleep", "tired", "burnout", "exhausted"]):
                buckets["recovery strain"] += 1
            if any(word in text for word in ["alone", "lonely", "isolated", "no one"]):
                buckets["support gaps"] += 1
            if any(word in text for word in ["boundary", "honest conversation", "repair", "apology"]):
                buckets["repair seeking"] += 1
            if any(word in text for word in ["future", "direction", "purpose"]):
                buckets["identity direction"] += 1
            if any(word in text for word in ["better", "improved", "calmer", "progress"]):
                buckets["growth signals"] += 1

        signals: list[dict[str, str]] = []
        for label, count in buckets.most_common(4):
            signals.append(
                {
                    "title": label.title(),
                    "detail": f"Appears in {count} recent reflection(s), suggesting a recurring theme.",
                }
            )
        return signals

    def build_user_profile(self, messages: list[Message]) -> dict[str, list[str] | str]:
        user_messages = [message.content.lower() for message in messages if message.role == "user"]
        if not user_messages:
            return {
                "themes": [],
                "stressors": [],
                "strengths": [],
                "support_gaps": [],
                "progress_signals": [],
                "unresolved_threads": [],
                "preferred_support_style": "balanced guidance",
                "continuity_note": "There is not enough history yet to form a continuity view.",
                "personalization_note": "A fuller personal profile will form after more conversations.",
                "summary": "No established personal pattern yet.",
            }

        themes: list[str] = []
        stressors: list[str] = []
        strengths: list[str] = []
        support_gaps: list[str] = []
        progress_signals: list[str] = []
        unresolved_threads: list[str] = []

        if any(any(word in text for word in ["career", "job", "work", "future"]) for text in user_messages):
            themes.append("career direction")
        if any(any(word in text for word in ["relationship", "friend", "partner", "family"]) for text in user_messages):
            themes.append("relationship strain")
        if any(any(word in text for word in ["money", "debt", "rent", "finance"]) for text in user_messages):
            themes.append("financial pressure")
        if any(any(word in text for word in ["stress", "anxious", "panic", "overwhelmed", "burnout"]) for text in user_messages):
            themes.append("emotional overload")

        if any(any(word in text for word in ["deadline", "urgent", "today", "tomorrow"]) for text in user_messages):
            stressors.append("time pressure")
        if any(any(word in text for word in ["expect", "pressure", "disappoint"]) for text in user_messages):
            stressors.append("expectation pressure")
        if any(any(word in text for word in ["can't sleep", "cannot sleep", "tired", "exhausted"]) for text in user_messages):
            stressors.append("low recovery")

        if any(any(word in text for word in ["help", "advice", "guidance"]) for text in user_messages):
            strengths.append("asks for help before shutting down")
        if any(any(word in text for word in ["think", "reflect", "understand", "clarity"]) for text in user_messages):
            strengths.append("reflective and insight-seeking")
        if any(any(word in text for word in ["care", "future", "better"]) for text in user_messages):
            strengths.append("motivated to improve life direction")
        if any(any(word in text for word in ["step by step", "clear plan", "next step"]) for text in user_messages):
            strengths.append("responds well to structured guidance")

        if any(any(word in text for word in ["alone", "lonely", "no one", "isolated"]) for text in user_messages):
            support_gaps.append("may be carrying stress without enough support")
        if any(any(word in text for word in ["do not know what to do", "don't know what to do", "stuck"]) for text in user_messages):
            support_gaps.append("decision pressure may rise faster than clarity")

        if any(any(word in text for word in ["better", "improved", "calmer", "more clear", "clearer"]) for text in user_messages):
            progress_signals.append("shows moments of recovery or growing clarity")
        if any(any(word in text for word in ["reached out", "talked to", "apologized", "applied"]) for text in user_messages):
            progress_signals.append("takes real-world action instead of only reflecting")
        if any(any(word in text for word in ["trying", "working on", "learning"]) for text in user_messages):
            progress_signals.append("stays engaged even when the situation is hard")

        if sum(any(word in text for word in ["career", "job", "work", "future"]) for text in user_messages) >= 2:
            unresolved_threads.append("career direction is still an active open loop")
        if sum(any(word in text for word in ["relationship", "friend", "partner", "family", "fight"]) for text in user_messages) >= 2:
            unresolved_threads.append("relationship tension appears unresolved across conversations")
        if sum(any(word in text for word in ["money", "debt", "rent", "finance"]) for text in user_messages) >= 2:
            unresolved_threads.append("financial stability remains an active pressure point")
        if sum(any(word in text for word in ["stress", "overwhelmed", "burnout", "can't sleep", "cannot sleep"]) for text in user_messages) >= 2:
            unresolved_threads.append("recovery and nervous-system overload still need attention")

        preferred_support_style = self._preferred_support_style(user_messages)
        continuity_note = self._build_continuity_note(themes, unresolved_threads, progress_signals)
        personalization_note = self._build_personalization_note(strengths, stressors, preferred_support_style)

        summary_parts = []
        if themes:
            summary_parts.append(f"Recurring themes: {', '.join(themes)}.")
        if stressors:
            summary_parts.append(f"Likely stress amplifiers: {', '.join(stressors)}.")
        if strengths:
            summary_parts.append(f"Personal strengths already visible: {', '.join(strengths)}.")
        if support_gaps:
            summary_parts.append(f"Support concern: {', '.join(support_gaps)}.")
        if progress_signals:
            summary_parts.append(f"Signs of growth: {', '.join(progress_signals)}.")
        if unresolved_threads:
            summary_parts.append(f"Active unresolved loops: {', '.join(unresolved_threads)}.")

        return {
            "themes": themes[:4],
            "stressors": stressors[:4],
            "strengths": strengths[:4],
            "support_gaps": support_gaps[:3],
            "progress_signals": progress_signals[:3],
            "unresolved_threads": unresolved_threads[:3],
            "preferred_support_style": preferred_support_style,
            "continuity_note": continuity_note,
            "personalization_note": personalization_note,
            "summary": " ".join(summary_parts) or "Some early themes are forming, but more conversation history is needed.",
        }

    def _preferred_support_style(self, user_messages: list[str]) -> str:
        if any("just listen" in text or "hear me out" in text for text in user_messages):
            return "gentle listening before advice"
        if any("step by step" in text or "plan" in text or "next step" in text for text in user_messages):
            return "structured practical guidance"
        if any("understand" in text or "why" in text or "clarity" in text for text in user_messages):
            return "reflective clarity-building"
        return "balanced guidance"

    def _build_continuity_note(
        self,
        themes: list[str],
        unresolved_threads: list[str],
        progress_signals: list[str],
    ) -> str:
        if unresolved_threads:
            return f"The strongest continuity signal is that {unresolved_threads[0]}."
        if themes:
            return f"A recurring personal theme is {themes[0]}, which is shaping how new problems are felt."
        if progress_signals:
            return f"There are early signs of movement: {progress_signals[0]}."
        return "History is still forming, so current guidance should stay flexible."

    def _build_personalization_note(
        self,
        strengths: list[str],
        stressors: list[str],
        preferred_support_style: str,
    ) -> str:
        note = f"This user seems to respond best to {preferred_support_style}."
        if strengths:
            note += f" A visible strength is {strengths[0]}."
        if stressors:
            note += f" A recurring pressure source is {stressors[0]}."
        return note
