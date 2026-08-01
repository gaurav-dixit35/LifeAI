import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database.db import get_db
from models.chat_model import Chat
from models.user_model import User
from routers.auth import get_current_admin_user
from schemas.admin_schema import (
    AdminAlertItem,
    AdminChatSnapshot,
    AdminMutationResponse,
    AdminOverviewResponse,
    AdminSummary,
    AdminTimelinePoint,
    AdminUserSnapshot,
    AdminUserUpdateRequest,
    FlaggedChatSnapshot,
    ProviderHealthItem,
)
from schemas.chat_schema import AnalysisResult, ReportBreakdownItem
from services.private_ai_service import PrivateAIService
from services.provider_fallback_service import ProviderFallbackService


router = APIRouter()
provider_service = ProviderFallbackService()
private_ai_service = PrivateAIService()


_ANALYSIS_DEFAULTS = {
    "assistant_kind": "life",
    "provider_used": "local",
    "knowledge_source": "",
    "uploaded_file_name": None,
    "conversation_mode": "problem_solving",
    "problem_summary": "No summary recorded.",
    "core_issue": "No core issue recorded.",
    "emotional_tone": "steady",
    "urgency_label": "low",
    "response_strategy": "Provide a practical next step.",
    "risk_level": 0,
    "confidence_score": 60,
    "recommendation": "steady",
    "detected_needs": [],
    "strengths": [],
    "hidden_risk_factors": [],
    "decision_lens": "",
    "suggestions": [],
    "action_plan": [],
    "immediate_actions": [],
    "short_term_actions": [],
    "long_term_actions": [],
    "avoid_now": [],
    "next_best_step": "Review the conversation details.",
    "follow_up_question": "What would you like to clarify next?",
    "reflection_prompt": "",
    "pattern_signals": [],
    "tools": [],
    "safety_notes": [],
    "when_to_seek_support": [],
    "personalization_note": "",
    "continuity_note": "",
    "unresolved_threads": [],
    "progress_signals": [],
}


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _coerce_analysis(raw_analysis: str | None) -> AnalysisResult | None:
    if not raw_analysis:
        return None
    try:
        parsed = json.loads(raw_analysis)
        if not isinstance(parsed, dict):
            return None
        merged = {**_ANALYSIS_DEFAULTS, **parsed}
        return AnalysisResult.model_validate(merged)
    except Exception:
        return None


def _topic_from_analysis(analysis: AnalysisResult) -> str:
    summary_text = analysis.problem_summary.lower()
    if analysis.assistant_kind == "code":
        return "coding"
    if "tech" in summary_text or "device" in summary_text:
        return "tech"
    if "health" in summary_text or "sleep" in summary_text:
        return "health"
    if "money" in summary_text or "financial" in summary_text:
        return "money"
    if "study" in summary_text or "routine" in summary_text:
        return "routine"
    if "career" in summary_text or "job" in summary_text:
        return "career"
    return "general"


@router.get("/overview", response_model=AdminOverviewResponse)
async def admin_overview(
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminOverviewResponse:
    user_result = await db.execute(
        select(User).options(selectinload(User.chats).selectinload(Chat.messages)).order_by(User.created_at.desc())
    )
    users = user_result.scalars().unique().all()

    chat_result = await db.execute(
        select(Chat).options(selectinload(Chat.user), selectinload(Chat.messages)).order_by(Chat.updated_at.desc())
    )
    chats = chat_result.scalars().unique().all()

    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=6)

    assistant_counter: Counter[str] = Counter()
    provider_counter: Counter[str] = Counter()
    topic_counter: Counter[str] = Counter()
    risk_scores: list[int] = []
    confidence_scores: list[int] = []
    uploads_processed = 0
    total_messages = 0
    life_questions = 0
    code_questions = 0
    private_chats = 0
    inactive_users = 0
    day_message_counts: dict[str, int] = defaultdict(int)
    day_new_users: dict[str, int] = defaultdict(int)
    day_active_users: dict[str, set[str]] = defaultdict(set)

    recent_users: list[AdminUserSnapshot] = []
    recent_chats: list[AdminChatSnapshot] = []
    flagged_chats: list[FlaggedChatSnapshot] = []

    for user in users:
        if not user.is_active:
            inactive_users += 1
        last_active = None
        message_count = 0
        chat_count = len(user.chats)
        for chat in user.chats:
            if chat.updated_at and (last_active is None or chat.updated_at > last_active):
                last_active = chat.updated_at
            message_count += len(chat.messages)
        recent_users.append(
            AdminUserSnapshot(
                id=user.id,
                name=user.name,
                email=user.email,
                is_admin=user.is_admin,
                is_active=user.is_active,
                chats=chat_count,
                messages=message_count,
                created_at=user.created_at,
                last_active=last_active,
            )
        )
        created_at_utc = _as_utc(user.created_at)
        last_active_utc = _as_utc(last_active)
        if created_at_utc and created_at_utc >= seven_days_ago:
            day_new_users[created_at_utc.strftime("%a")] += 1
        if last_active_utc and last_active_utc >= seven_days_ago:
            day_active_users[last_active_utc.strftime("%a")].add(user.id)

    for chat in chats:
        if chat.personality_mode == "private":
            private_chats += 1
        last_preview = next((message.content for message in reversed(chat.messages) if message.content.strip()), "No preview yet")
        assistant_kind = "life"
        provider_used = "local"
        urgency_label = "low"
        risk_level = 0
        for message in reversed(chat.messages):
            if message.role == "assistant":
                analysis = _coerce_analysis(message.analysis)
                if analysis is None:
                    continue
                assistant_kind = analysis.assistant_kind
                provider_used = analysis.provider_used or "local"
                urgency_label = analysis.urgency_label
                risk_level = analysis.risk_level
                if analysis.urgency_label in {"high", "critical"} or analysis.risk_level >= 72:
                    flagged_chats.append(
                        FlaggedChatSnapshot(
                            id=chat.id,
                            title=chat.title,
                            user_name=chat.user.name if chat.user else "Unknown user",
                            assistant_kind=analysis.assistant_kind,
                            provider_used=provider_used,
                            urgency_label=analysis.urgency_label,
                            risk_level=analysis.risk_level,
                            updated_at=chat.updated_at,
                            preview=last_preview[:180],
                        )
                    )
                break
        recent_chats.append(
            AdminChatSnapshot(
                id=chat.id,
                title=chat.title,
                personality_mode=chat.personality_mode,
                user_name=chat.user.name if chat.user else "Unknown user",
                preview=last_preview[:180],
                message_count=len(chat.messages),
                updated_at=chat.updated_at,
                assistant_kind=assistant_kind,
                provider_used=provider_used,
                urgency_label=urgency_label,
                risk_level=risk_level,
            )
        )
        for message in chat.messages:
            total_messages += 1
            message_created_at_utc = _as_utc(message.created_at)
            if message_created_at_utc and message_created_at_utc >= seven_days_ago:
                day_key = message_created_at_utc.strftime("%a")
                day_message_counts[day_key] += 1
                if chat.user_id:
                    day_active_users[day_key].add(chat.user_id)
            if message.role != "assistant":
                continue
            analysis = _coerce_analysis(message.analysis)
            if analysis is None:
                continue
            assistant_counter[analysis.assistant_kind] += 1
            provider_counter[analysis.provider_used or "local"] += 1
            topic_counter[_topic_from_analysis(analysis)] += 1
            risk_scores.append(analysis.risk_level)
            confidence_scores.append(analysis.confidence_score)
            if analysis.assistant_kind == "life":
                life_questions += 1
            elif analysis.assistant_kind == "code":
                code_questions += 1
            if analysis.uploaded_file_name:
                uploads_processed += 1

    ordered_timeline: list[AdminTimelinePoint] = []
    for offset in range(6, -1, -1):
        day = now - timedelta(days=offset)
        label = day.strftime("%a")
        ordered_timeline.append(
            AdminTimelinePoint(
                day=label,
                new_users=day_new_users.get(label, 0),
                active_users=len(day_active_users.get(label, set())),
                messages=day_message_counts.get(label, 0),
            )
        )

    provider_health: list[ProviderHealthItem] = []
    provider_models = {
        "gemini": settings.GEMINI_MODEL_NAME,
        "openrouter": settings.OPENROUTER_MODEL_NAME,
        "groq": settings.GROQ_MODEL_NAME,
    }
    provider_keys = {
        "gemini": bool(settings.GEMINI_API_KEY),
        "openrouter": bool(settings.OPENROUTER_API_KEY),
        "groq": bool(settings.GROQ_API_KEY),
    }
    unhealthy_provider_count = 0
    for provider in ["gemini", "openrouter", "groq"]:
        configured = provider_keys[provider]
        healthy = False
        detail = "Key not configured"
        if configured:
            healthy, detail = await provider_service.verify_provider(provider)
        if configured and not healthy:
            unhealthy_provider_count += 1
        provider_health.append(
            ProviderHealthItem(
                provider=provider.title(),
                configured=configured,
                healthy=healthy,
                model=provider_models[provider],
                detail=detail,
            )
        )

    ollama_status = await private_ai_service.status()
    ollama_running = bool(ollama_status.get("ollama_running"))
    ollama_model_available = bool(ollama_status.get("model_available"))
    ollama_model_name = str(ollama_status.get("model") or settings.OLLAMA_MODEL_NAME)
    provider_health.append(
        ProviderHealthItem(
            provider="Ollama",
            configured=True,
            healthy=ollama_running and ollama_model_available,
            model=ollama_model_name,
            detail=(
                "Local model ready"
                if ollama_running and ollama_model_available
                else "Local model unavailable"
            ),
        )
    )

    alerts: list[AdminAlertItem] = []
    if unhealthy_provider_count:
        alerts.append(
            AdminAlertItem(
                severity="critical" if unhealthy_provider_count > 1 else "warning",
                title="Provider fallback pressure detected",
                detail=f"{unhealthy_provider_count} external provider(s) are configured but not healthy right now. Review provider health before demos or heavy usage.",
            )
        )
    if not (ollama_running and ollama_model_available):
        alerts.append(
            AdminAlertItem(
                severity="warning",
                title="Private AI local model needs attention",
                detail="Ollama is unavailable or the configured local model is not ready. Private AI will feel degraded until the local model returns.",
            )
        )
    if flagged_chats:
        alerts.append(
            AdminAlertItem(
                severity="warning",
                title="High-risk conversations detected",
                detail=f"{len(flagged_chats)} recent chat(s) show elevated or high urgency and should be reviewed in the admin moderation area.",
            )
        )
    if inactive_users:
        alerts.append(
            AdminAlertItem(
                severity="info",
                title="Inactive accounts present",
                detail=f"{inactive_users} account(s) are currently inactive. Use user controls below to review whether they should remain suspended.",
            )
        )
    if not alerts:
        alerts.append(
            AdminAlertItem(
                severity="info",
                title="System looks stable",
                detail="Providers, user activity, and moderation signals are currently within a healthy operating range.",
            )
        )

    return AdminOverviewResponse(
        generated_at=now,
        summary=AdminSummary(
            total_users=len(users),
            admin_users=sum(1 for user in users if user.is_admin),
            active_users_7d=len({user_id for ids in day_active_users.values() for user_id in ids}),
            total_chats=len(chats),
            total_messages=total_messages,
            life_questions=life_questions,
            code_questions=code_questions,
            private_chats=private_chats,
            uploads_processed=uploads_processed,
            average_risk=round(sum(risk_scores) / len(risk_scores)) if risk_scores else 0,
            average_confidence=round(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0,
        ),
        assistant_distribution=[
            ReportBreakdownItem(label=label.title(), value=value)
            for label, value in assistant_counter.most_common()
        ],
        provider_distribution=[
            ReportBreakdownItem(label=label.title(), value=value)
            for label, value in provider_counter.most_common()
        ],
        topic_distribution=[
            ReportBreakdownItem(label=label.title(), value=value)
            for label, value in topic_counter.most_common(8)
        ],
        activity_timeline=ordered_timeline,
        provider_health=provider_health,
        alerts=alerts,
        flagged_chats=sorted(flagged_chats, key=lambda item: (item.risk_level, _as_utc(item.updated_at) or now), reverse=True)[:8],
        recent_users=recent_users[:8],
        recent_chats=recent_chats[:10],
    )


@router.patch("/users/{user_id}", response_model=AdminMutationResponse)
async def update_user_state(
    user_id: str,
    payload: AdminUserUpdateRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMutationResponse:
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.is_active is None and payload.is_admin is None:
        raise HTTPException(status_code=400, detail="No admin update was provided.")

    if target_user.id == current_admin.id and payload.is_admin is False:
        raise HTTPException(status_code=400, detail="You cannot revoke your own admin access.")

    if target_user.id == current_admin.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    if payload.is_active is not None:
        target_user.is_active = payload.is_active
    if payload.is_admin is not None:
        target_user.is_admin = payload.is_admin

    await db.commit()
    return AdminMutationResponse(message="User access updated successfully.")


@router.delete("/chats/{chat_id}", response_model=AdminMutationResponse)
async def delete_chat_as_admin(
    chat_id: str,
    _: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> AdminMutationResponse:
    chat = await db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    await db.delete(chat)
    await db.commit()
    return AdminMutationResponse(message="Chat removed from the system.")

