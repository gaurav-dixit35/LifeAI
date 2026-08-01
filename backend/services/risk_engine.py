class RiskEngine:
    HIGH_RISK_TERMS = {
        "suicide": 65,
        "self-harm": 65,
        "harm myself": 65,
        "abuse": 45,
        "panic attack": 35,
        "unsafe": 35,
        "trapped": 25,
        "hopeless": 35,
        "can't go on": 50,
    }

    EMOTIONAL_TERMS = {
        "stressed": 15,
        "anxious": 18,
        "burnout": 20,
        "confused": 10,
        "fight": 10,
        "job": 8,
        "career": 10,
        "money": 15,
        "relationship": 12,
        "pressure": 10,
        "lonely": 14,
        "isolated": 18,
        "guilt": 10,
        "ashamed": 12,
        "stuck": 12,
        "fear of failure": 14,
        "low confidence": 12,
    }

    PRACTICAL_TERMS = {
        "headache": 8,
        "back pain": 10,
        "neck pain": 8,
        "cold": 8,
        "cough": 8,
        "fever": 16,
        "hair fall": 6,
        "skin": 6,
        "allergy": 8,
        "internet": 8,
        "battery": 7,
        "password": 8,
        "laptop": 8,
        "charger": 8,
        "storage": 7,
        "deleted": 10,
        "network": 7,
        "app crashing": 9,
        "software": 8,
        "shirt": 4,
        "sandal": 4,
        "punctured": 6,
        "keys": 9,
        "alarm": 7,
        "overslept": 8,
        "late": 6,
        "wallet": 8,
        "missed bus": 8,
        "missed train": 8,
        "umbrella": 4,
        "electricity": 8,
        "fan": 5,
        "fridge": 8,
        "laundry": 4,
        "water shortage": 10,
        "leakage": 8,
        "sink": 6,
        "toilet": 8,
        "mosquito": 5,
        "traffic": 7,
        "fuel": 7,
        "parking": 5,
        "documents": 8,
        "room messy": 4,
        "phone addiction": 10,
        "social media": 8,
    }

    CONTEXT_AMPLIFIERS = {
        "everyone expects": 8,
        "every day": 8,
        "can't sleep": 10,
        "not eating": 12,
        "spiral": 10,
        "no one": 10,
        "alone": 8,
        "deadline": 6,
        "urgent": 7,
        "do not know what to do": 8,
        "don't know what to do": 8,
        "nothing is working": 10,
        "falling apart": 12,
        "i am failing": 9,
    }

    def score(self, text: str) -> int:
        content = text.lower()
        if self._is_casual(content):
            return 4

        risk = 8
        practical_score = 0
        emotional_score = 0

        for term, weight in self.HIGH_RISK_TERMS.items():
            if term in content:
                risk += weight

        for term, weight in self.EMOTIONAL_TERMS.items():
            if term in content:
                emotional_score += weight

        for term, weight in self.PRACTICAL_TERMS.items():
            if term in content:
                practical_score += weight

        for term, weight in self.CONTEXT_AMPLIFIERS.items():
            if term in content:
                risk += weight

        risk += emotional_score
        risk += min(practical_score, 18)

        if "!" in content:
            risk += 3
        if len(content) > 350:
            risk += 4
        if any(word in content for word in ["tomorrow", "today", "right now", "immediately"]):
            risk += 4
        if any(phrase in content for phrase in ["i feel", "i am feeling", "i'm feeling"]):
            risk += 4
        if any(phrase in content for phrase in ["should i", "what should i do", "how do i"]):
            risk += 4

        if self._is_practical_only_issue(content, emotional_score):
            risk = max(8, min(42, risk - 8))

        return max(5, min(100, risk))

    def label(self, score: int) -> str:
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    def _is_casual(self, content: str) -> bool:
        normalized = content.strip()
        casual_inputs = {
            "hi",
            "hello",
            "hey",
            "hii",
            "yo",
            "how are you",
            "what's up",
            "whats up",
            "thanks",
            "thank you",
            "what can you do",
            "who are you",
        }
        return normalized in casual_inputs

    def _is_practical_only_issue(self, content: str, emotional_score: int) -> bool:
        practical_hit = any(term in content for term in self.PRACTICAL_TERMS)
        high_risk_hit = any(term in content for term in self.HIGH_RISK_TERMS)
        return practical_hit and emotional_score < 12 and not high_risk_hit
