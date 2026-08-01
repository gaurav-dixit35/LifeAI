from __future__ import annotations

from dataclasses import dataclass

import httpx

from config import settings


@dataclass
class ProviderResponse:
    provider: str
    content: str


class ProviderFallbackService:
    def __init__(self) -> None:
        self.timeout = httpx.Timeout(35.0, connect=10.0)

    async def generate(self, *, system_prompt: str, user_prompt: str, max_tokens: int = 900, temperature: float = 0.35) -> ProviderResponse:
        last_error: Exception | None = None
        for provider in settings.LIFE_AI_PROVIDER_ORDER:
            try:
                content = await self._generate_from_provider(
                    provider=provider,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if content.strip():
                    return ProviderResponse(provider=provider, content=content.strip())
            except Exception as error:
                last_error = error
                continue

        if last_error is not None:
            raise last_error
        raise RuntimeError("No AI provider is configured.")

    async def verify_provider(self, provider: str) -> tuple[bool, str]:
        prompt = "Reply with only the word OK."
        try:
            response = await self._generate_from_provider(
                provider=provider,
                system_prompt="You are a health check responder.",
                user_prompt=prompt,
                max_tokens=16,
                temperature=0,
            )
            return True, response.strip()[:80] or "OK"
        except Exception as error:
            return False, str(error)

    async def _generate_from_provider(
        self,
        *,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        normalized = provider.strip().lower()
        if normalized == "gemini":
            return await self._call_gemini(system_prompt, user_prompt, max_tokens, temperature)
        if normalized == "openrouter":
            return await self._call_openrouter(system_prompt, user_prompt, max_tokens, temperature)
        if normalized == "groq":
            return await self._call_groq(system_prompt, user_prompt, max_tokens, temperature)
        raise RuntimeError(f"Unsupported provider: {provider}")

    async def _call_gemini(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("Gemini key is not configured")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL_NAME}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)
            response.raise_for_status()
            data = response.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
        if not text.strip():
            raise RuntimeError("Gemini returned empty content")
        return text

    async def _call_openrouter(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        if not settings.OPENROUTER_API_KEY:
            raise RuntimeError("OpenRouter key is not configured")
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-Title": settings.OPENROUTER_APP_NAME,
        }
        payload = {
            "model": settings.OPENROUTER_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenRouter returned no choices")
        text = choices[0].get("message", {}).get("content", "")
        if not text.strip():
            raise RuntimeError("OpenRouter returned empty content")
        return text

    async def _call_groq(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str:
        if not settings.GROQ_API_KEY:
            raise RuntimeError("Groq key is not configured")
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.GROQ_MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("Groq returned no choices")
        text = choices[0].get("message", {}).get("content", "")
        if not text.strip():
            raise RuntimeError("Groq returned empty content")
        return text
