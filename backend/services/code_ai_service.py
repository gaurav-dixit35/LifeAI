from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from config import settings
from services.provider_fallback_service import ProviderFallbackService


class CodeAIService:
    def __init__(self) -> None:
        self.training_path = Path(__file__).resolve().parents[2] / "other" / "training.txt"

    def is_code_query(self, text: str) -> bool:
        lowered = text.lower()
        code_markers = [
            "error",
            "exception",
            "traceback",
            "bug",
            "debug",
            "compile",
            "build fails",
            "stack trace",
            "fastapi",
            "react",
            "next.js",
            "nextjs",
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "docker",
            "kubernetes",
            "sql",
            "api returns",
            "401",
            "403",
            "404",
            "422",
            "500",
            "hook",
            "syntaxerror",
            "typeerror",
            "referenceerror",
            "nullpointer",
            "segmentation fault",
            "git conflict",
        ]
        if any(marker in lowered for marker in code_markers):
            return True
        if "```" in text:
            return True
        if re.search(r"\b[A-Za-z0-9_]+\.(py|js|ts|tsx|jsx|java|cpp|c|go|rs|sql)\b", text):
            return True
        return False

    def extract_text_from_upload(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip()
        return content.decode("utf-8", errors="ignore").strip()

    def retrieve_context(self, query: str, uploaded_text: str | None = None, uploaded_file_name: str | None = None) -> dict[str, Any]:
        corpus_text = uploaded_text or self._load_training_text()
        source_name = uploaded_file_name or "default training.txt"
        chunks = self._split_chunks(corpus_text)
        scored = self._rank_chunks(query, chunks)
        top_chunks = [chunk for _, chunk in scored[:3]]
        combined_context = "\n\n---\n\n".join(top_chunks)
        return {
            "source_name": source_name,
            "chunks": top_chunks,
            "combined_context": combined_context[: settings.CODE_AI_MAX_CONTEXT_CHARS],
            "used_upload": bool(uploaded_text),
        }

    async def generate_reply(
        self,
        *,
        user_message: str,
        context: str,
        retrieval: dict[str, Any],
        provider_service: ProviderFallbackService,
    ) -> tuple[str, str]:
        system_prompt = (
            "You are Code AI inside LifeAI. Solve coding errors and debugging problems. "
            "Use the retrieved context first, stay grounded in the supplied file/training data when possible, "
            "and give practical debugging steps, not generic filler. If the context is weak, say what is missing."
        )
        user_prompt = (
            f"Recent chat context:\n{context or 'No prior context.'}\n\n"
            f"Coding question:\n{user_message}\n\n"
            f"Knowledge source: {retrieval['source_name']}\n"
            f"Retrieved context:\n{retrieval['combined_context'] or 'No strong retrieval match found.'}\n\n"
            "Answer with:\n"
            "1. likely cause\n"
            "2. exact checks/fixes\n"
            "3. a safer next debugging step if it still fails\n"
            "Keep it concrete."
        )
        response = await provider_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=950,
            temperature=0.2,
        )
        return response.content, response.provider

    def build_analysis(
        self,
        *,
        user_message: str,
        retrieval: dict[str, Any],
        provider_used: str,
    ) -> dict[str, Any]:
        steps = self._build_steps(user_message, retrieval)
        confidence = 90 if retrieval["chunks"] else 62
        return {
            "assistant_kind": "code",
            "provider_used": provider_used,
            "knowledge_source": retrieval["source_name"],
            "uploaded_file_name": retrieval["source_name"] if retrieval["used_upload"] else None,
            "conversation_mode": "problem_solving",
            "problem_summary": f"Code AI is handling a coding/debugging question using {retrieval['source_name']} as the primary context.",
            "core_issue": "The user needs a practical debugging answer grounded in coding context, likely an error, failing behavior, or uploaded project material.",
            "emotional_tone": "focused",
            "urgency_label": "guarded",
            "response_strategy": "Use the retrieved coding context first, identify the likely failure point, and give direct debugging steps.",
            "risk_level": 10,
            "confidence_score": confidence,
            "recommendation": "steady",
            "detected_needs": ["debugging clarity", "root cause isolation", "practical fix"],
            "strengths": [
                "The user is asking a concrete technical question.",
                "The problem can usually be reduced through step-by-step verification.",
            ],
            "hidden_risk_factors": [
                "A misleading stack trace or partial snippet can hide the real failing layer.",
                "Changing multiple things at once can make debugging slower.",
            ],
            "decision_lens": "Judge fixes by whether they isolate the failing layer and reduce uncertainty, not by whether they feel like the biggest change.",
            "suggestions": steps,
            "action_plan": steps,
            "immediate_actions": steps,
            "short_term_actions": [
                "Retest after each single change instead of batching fixes.",
                "Capture the exact new error or behavior after the first debugging pass.",
            ],
            "long_term_actions": [
                "Keep a reproducible minimal test case for recurring issues.",
                "Improve logs, types, or validation around the failing area.",
            ],
            "avoid_now": [
                "Do not change unrelated files before confirming the failing layer.",
                "Do not rely on guesswork when one smaller diagnostic step can narrow the cause.",
            ],
            "next_best_step": steps[0],
            "follow_up_question": "What exact error message, failing line, or behavior do you see after the first fix attempt?",
            "reflection_prompt": "Which part of the stack or flow still feels least certain after this answer?",
            "pattern_signals": [],
            "tools": [
                {
                    "name": "Minimal reproduction",
                    "description": "Reduce the bug to the smallest failing example you can still run.",
                    "required": True,
                },
                {
                    "name": "Exact error capture",
                    "description": "Copy the full error, stack trace, or failing output before changing more code.",
                    "required": True,
                },
            ],
            "safety_notes": ["Test one fix at a time so you know which change actually worked."],
            "when_to_seek_support": ["Escalate to a teammate or better logs if the issue crosses multiple layers and the failing point is still unclear."],
            "personalization_note": "Code AI is answering this because the message looks like a coding/debugging problem or file-based technical question.",
            "continuity_note": "Code AI stays focused on the current bug and its surrounding context.",
            "unresolved_threads": [],
            "progress_signals": [],
        }

    def local_fallback_reply(self, retrieval: dict[str, Any]) -> str:
        chunks = retrieval["chunks"]
        if not chunks:
            return (
                "I could not find a strong direct match in the current coding context. "
                "Share the exact error, stack trace, or a more focused snippet so I can narrow the cause faster."
            )
        excerpt = chunks[0][:1200].strip()
        return (
            "I used the best matching coding context I could find. Start by checking the exact failing line, compare it against this retrieved reference, and test one fix at a time.\n\n"
            f"Matched context:\n{excerpt}"
        )

    def _load_training_text(self) -> str:
        try:
            return self.training_path.read_text(encoding="utf-8", errors="ignore")
        except FileNotFoundError:
            return ""

    def _split_chunks(self, text: str) -> list[str]:
        if not text.strip():
            return []
        raw_chunks = re.split(r"(?=\{\"id\":)|\n\s*\n\s*\n+", text)
        chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
        normalized: list[str] = []
        for chunk in chunks:
            collapsed = re.sub(r"\s+", " ", chunk).strip()
            if len(collapsed) >= 80:
                normalized.append(collapsed)
        return normalized or [re.sub(r"\s+", " ", text).strip()[: settings.CODE_AI_MAX_CONTEXT_CHARS]]

    def _rank_chunks(self, query: str, chunks: list[str]) -> list[tuple[float, str]]:
        query_tokens = self._tokenize(query)
        scored: list[tuple[float, str]] = []
        for chunk in chunks:
            chunk_lower = chunk.lower()
            chunk_tokens = self._tokenize(chunk_lower)
            overlap = len(query_tokens & chunk_tokens)
            phrase_bonus = sum(1 for token in query_tokens if token and token in chunk_lower)
            score = (overlap * 3) + phrase_bonus + min(len(chunk) / 900, 2.5)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored

    def _tokenize(self, text: str) -> set[str]:
        tokens = set(re.findall(r"[a-zA-Z0-9_+#.-]{3,}", text.lower()))
        stop = {"the", "and", "for", "with", "that", "this", "from", "have", "what", "when", "where", "while", "into"}
        return {token for token in tokens if token not in stop}

    def _build_steps(self, user_message: str, retrieval: dict[str, Any]) -> list[str]:
        source = retrieval["source_name"]
        return [
            f"Start with the exact failing message or snippet and compare it against the strongest match from {source}.",
            "Confirm the failing layer first: input, validation, API contract, state update, or runtime environment.",
            "Apply one fix, rerun, and capture the next exact error or behavior before changing anything else.",
        ]
