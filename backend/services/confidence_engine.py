class ConfidenceEngine:
    def score(
        self,
        *,
        message: str,
        conversation_mode: str,
        risk_level: int,
        action_plan: list[str],
        safety_notes: list[str],
        pattern_signals: list[dict],
        follow_up_question: str,
    ) -> int:
        if conversation_mode == "casual":
            return 95

        confidence = 58

        if len(message.split()) > 8:
            confidence += 10
        if len(message.split()) > 30:
            confidence += 4
        if len(action_plan) >= 3:
            confidence += 12
        if safety_notes:
            confidence += 6
        if pattern_signals:
            confidence += 6
        if follow_up_question:
            confidence += 3
        if "because" in message.lower() or "but" in message.lower():
            confidence += 4
        if risk_level >= 70:
            confidence -= 10
        if risk_level >= 85:
            confidence -= 8

        return max(35, min(96, confidence))

    def label(self, score: int) -> str:
        if score >= 80:
            return "high"
        if score >= 60:
            return "medium"
        return "low"
