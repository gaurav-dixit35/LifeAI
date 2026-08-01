from __future__ import annotations

from typing import Any

import httpx

from config import settings


class PrivateAIService:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(45.0, connect=8.0)

    async def generate_reply(self, *, user_message: str, context: str) -> tuple[str, str]:
        payload = {
            "model": settings.OLLAMA_MODEL_NAME,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Private AI, a private local assistant. Keep the response grounded, calm, and useful. "
                        "Never mention external providers. This conversation stays local to Ollama."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Recent context:\n{context or 'No prior context.'}\n\nUser message:\n{user_message}",
                },
            ],
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        message = data.get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise RuntimeError("Ollama returned empty content")
        return content, "ollama"

    async def status(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
        models = data.get("models", [])
        available = any(model.get("name") == settings.OLLAMA_MODEL_NAME for model in models)
        return {
            "ollama_running": True,
            "model_available": available,
            "model": settings.OLLAMA_MODEL_NAME,
        }

    def build_analysis(self, provider_used: str = "ollama") -> dict[str, Any]:
        return {
            "assistant_kind": "private",
            "provider_used": provider_used,
            "knowledge_source": "local ollama",
            "uploaded_file_name": None,
            "conversation_mode": "problem_solving",
            "problem_summary": "Private AI answered through the local Ollama model.",
            "core_issue": "The user is using the private local assistant instead of the cloud-backed workspace.",
            "emotional_tone": "reflective",
            "urgency_label": "low",
            "response_strategy": "Keep the reply private, local, and practical without sending the request to cloud providers.",
            "risk_level": 0,
            "confidence_score": 88,
            "recommendation": "steady",
            "detected_needs": ["private conversation"],
            "strengths": ["The user chose the private local assistant for a more personal conversation."],
            "hidden_risk_factors": [],
            "decision_lens": "Use a calm, private local conversation space.",
            "suggestions": [],
            "action_plan": [],
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": [],
            "avoid_now": [],
            "next_best_step": "Continue the private conversation.",
            "follow_up_question": "What feels most important to talk through privately?",
            "reflection_prompt": "What do you want to understand more clearly in this private space?",
            "pattern_signals": [],
            "tools": [],
            "safety_notes": [],
            "when_to_seek_support": [],
            "personalization_note": "Private AI is using the local Ollama model only.",
            "continuity_note": "Private chats stay separate from the main LifeAI workspace.",
            "unresolved_threads": [],
            "progress_signals": [],
        }
