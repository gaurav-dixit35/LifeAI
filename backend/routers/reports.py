import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.db import get_db
from models.chat_model import Chat, Message
from models.user_model import User
from routers.auth import get_current_user
from schemas.chat_schema import (
    AnalysisResult,
    RecentConversationSnapshot,
    ReportBreakdownItem,
    ReportComparisonMetric,
    ReportComparisonSummary,
    ReportFilterMeta,
    ReportResponse,
    ReportSummary,
    ReportTimelinePoint,
    ResponseHealthSummary,
)
from services.memory_service import MemoryService


router = APIRouter()
memory_service = MemoryService()


def estimate_minutes(messages: list[str]) -> int:
    total_words = sum(len(message.split()) for message in messages)
    return max(1, round(total_words / 45)) if messages else 0


def infer_topic(analysis: AnalysisResult, fallback_themes: list[str]) -> str:
    topic_label = next((theme for theme in fallback_themes if theme), "general life support")
    summary_text = analysis.problem_summary.lower()
    if analysis.assistant_kind == "code":
        return "coding"
    if "tech" in summary_text or "device" in summary_text:
        return "tech"
    if "health" in summary_text or "sleep" in summary_text:
        return "health"
    if "money" in summary_text or "financial" in summary_text:
        return "money"
    if "relationship" in summary_text:
        return "relationship"
    if "career" in summary_text or "job" in summary_text:
        return "career"
    if "schedule" in summary_text or "timing" in summary_text:
        return "schedule"
    if "study" in summary_text or "routine" in summary_text:
        return "routine"
    return topic_label


def build_metric(current: int, previous: int) -> ReportComparisonMetric:
    return ReportComparisonMetric(current=current, previous=previous, delta=current - previous)


def build_period_bounds(range_key: str, now: datetime) -> tuple[datetime | None, datetime | None, str, str]:
    if range_key == "30d":
        start = now - timedelta(days=29)
        previous_start = start - timedelta(days=30)
        return start, previous_start, "Last 30 days", "Compared with the previous 30 days"
    if range_key == "all":
        return None, None, "All recorded history", "No previous-period comparison for all-time view"
    start = now - timedelta(days=6)
    previous_start = start - timedelta(days=7)
    return start, previous_start, "Last 7 days", "Compared with the previous 7 days"


def in_period(moment: datetime, start: datetime | None, end: datetime) -> bool:
    if start is None:
        return True
    return start <= moment <= end


def in_previous_period(moment: datetime, start: datetime | None, previous_start: datetime | None) -> bool:
    if start is None or previous_start is None:
        return False
    previous_end = start - timedelta(microseconds=1)
    return previous_start <= moment <= previous_end


@router.get("/", response_model=ReportResponse)
async def generate_report(
    date_range: str = Query(default="7d"),
    assistant_scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    range_key = date_range if date_range in {"7d", "30d", "all"} else "7d"
    scope = assistant_scope if assistant_scope in {"all", "life", "code"} else "all"
    now = datetime.now(timezone.utc)
    period_start, previous_start, range_label, comparison_label = build_period_bounds(range_key, now)

    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id, Chat.personality_mode != "private")
        .options(selectinload(Chat.messages))
        .order_by(Chat.updated_at.desc())
    )
    chats = result.scalars().unique().all()

    assistant_messages: list[Message] = []
    previous_assistant_messages: list[Message] = []
    all_period_messages: list[Message] = []
    previous_period_messages: list[Message] = []
    chat_ids_in_period: set[str] = set()
    chat_ids_in_previous_period: set[str] = set()

    for chat in chats:
        for message in chat.messages:
            created_at = message.created_at.astimezone(timezone.utc)
            is_current = in_period(created_at, period_start, now)
            is_previous = in_previous_period(created_at, period_start, previous_start)

            if is_current:
                all_period_messages.append(message)
                chat_ids_in_period.add(chat.id)
            elif is_previous:
                previous_period_messages.append(message)
                chat_ids_in_previous_period.add(chat.id)

            if message.role == "assistant" and message.analysis:
                analysis = AnalysisResult.model_validate(json.loads(message.analysis))
                if scope != "all" and analysis.assistant_kind != scope:
                    continue
                if is_current:
                    assistant_messages.append(message)
                elif is_previous:
                    previous_assistant_messages.append(message)

    analyses = [AnalysisResult.model_validate(json.loads(message.analysis)) for message in assistant_messages]
    previous_analyses = [AnalysisResult.model_validate(json.loads(message.analysis)) for message in previous_assistant_messages]
    user_profile = memory_service.build_user_profile(all_period_messages)

    risk_scores = [item.risk_level for item in analyses]
    confidence_scores = [item.confidence_score for item in analyses]
    previous_risk_scores = [item.risk_level for item in previous_analyses]
    previous_confidence_scores = [item.confidence_score for item in previous_analyses]

    emotion_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    urgency_counts: Counter[str] = Counter()
    assistant_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    daily_messages: dict[str, int] = defaultdict(int)
    daily_chats: dict[str, set[str]] = defaultdict(set)
    daily_risks: dict[str, list[int]] = defaultdict(list)
    follow_up_needed = 0
    problem_solving_count = 0
    casual_count = 0

    recent_conversations: list[RecentConversationSnapshot] = []
    recent_highlights: list[str] = []

    for message, analysis in zip(assistant_messages, analyses):
        emotion_counts[analysis.emotional_tone] += 1
        urgency_counts[analysis.urgency_label] += 1
        assistant_counts[analysis.assistant_kind] += 1
        provider_counts[analysis.provider_used or "local"] += 1
        topic_counts[infer_topic(analysis, list(user_profile.get("themes", [])))] += 1
        if analysis.conversation_mode == "problem_solving":
            problem_solving_count += 1
        else:
            casual_count += 1
        if analysis.follow_up_question:
            follow_up_needed += 1
        for signal in analysis.pattern_signals:
            pattern_counts[signal.title] += 1

        day_key = message.created_at.astimezone(timezone.utc).strftime("%a")
        daily_messages[day_key] += 1
        daily_chats[day_key].add(message.chat_id)
        daily_risks[day_key].append(analysis.risk_level)

        if len(recent_highlights) < 6:
            recent_highlights.append(analysis.problem_summary)

    for chat in chats:
        period_assistant_messages = [
            message for message in chat.messages
            if message.role == "assistant"
            and message.analysis
            and in_period(message.created_at.astimezone(timezone.utc), period_start, now)
        ]
        if not period_assistant_messages:
            continue
        latest_assistant = period_assistant_messages[-1]
        latest_analysis = AnalysisResult.model_validate(json.loads(latest_assistant.analysis))
        if scope != "all" and latest_analysis.assistant_kind != scope:
            continue
        preview = next((message.content for message in reversed(chat.messages) if message.content.strip()), "No preview yet")
        recent_conversations.append(
            RecentConversationSnapshot(
                id=chat.id,
                title=chat.title,
                preview=preview[:180],
                updated_at=chat.updated_at,
                assistant_kind=latest_analysis.assistant_kind,
                provider_used=latest_analysis.provider_used,
            )
        )

    common_emotions = [name for name, _ in emotion_counts.most_common(3)]
    recurring_patterns = [name for name, _ in pattern_counts.most_common(4)]
    topic_distribution = [ReportBreakdownItem(label=name, value=count) for name, count in topic_counts.most_common(6)]
    urgency_distribution = [ReportBreakdownItem(label=name.title(), value=count) for name, count in urgency_counts.most_common()]
    assistant_distribution = [ReportBreakdownItem(label=name.title(), value=count) for name, count in assistant_counts.most_common()]
    provider_distribution = [ReportBreakdownItem(label=name.title(), value=count) for name, count in provider_counts.most_common()]

    ordered_days: list[ReportTimelinePoint] = []
    days_to_show = 30 if range_key == "30d" else 7
    for offset in range(days_to_show - 1, -1, -1):
        day = now - timedelta(days=offset)
        label = day.strftime("%a") if range_key != "30d" else day.strftime("%d %b")
        key = day.strftime("%a") if range_key != "30d" else day.strftime("%Y-%m-%d")
        if range_key == "30d":
            point_messages = sum(
                1
                for message in all_period_messages
                if message.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d") == key
            )
            point_chats = len({
                message.chat_id
                for message in all_period_messages
                if message.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d") == key
            })
            point_risks = [
                AnalysisResult.model_validate(json.loads(message.analysis)).risk_level
                for message in assistant_messages
                if message.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d") == key and message.analysis
            ]
        else:
            point_messages = daily_messages.get(key, 0)
            point_chats = len(daily_chats.get(key, set()))
            point_risks = daily_risks.get(key, [])
        ordered_days.append(
            ReportTimelinePoint(
                day=label,
                messages=point_messages,
                chats=point_chats,
                average_risk=round(sum(point_risks) / len(point_risks)) if point_risks else 0,
            )
        )

    weekly_user_messages = [message.content for message in all_period_messages if message.role == "user"]
    top_topic = topic_distribution[0].label if topic_distribution else ("Coding" if scope == "code" else "general life support")
    strongest_signal = recurring_patterns[0] if recurring_patterns else "No strong recurring signal yet"

    summary = ReportSummary(
        total_chats=len(chat_ids_in_period),
        total_messages=len(all_period_messages),
        average_risk=round(sum(risk_scores) / len(risk_scores)) if risk_scores else 0,
        average_confidence=round(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0,
        messages_this_week=sum(point.messages for point in ordered_days[-7:]),
        estimated_minutes=estimate_minutes(weekly_user_messages),
        common_emotions=common_emotions,
        recurring_patterns=recurring_patterns,
        weekly_focus=(
            "Reduce current pressure, then solve the most practical issue first."
            if (risk_scores and max(risk_scores) >= 60)
            else user_profile.get("continuity_note", "Keep building clarity through small, practical daily-life questions.")
        ),
        active_themes=list(user_profile.get("themes", []))[:4],
        support_gaps=list(user_profile.get("support_gaps", []))[:3],
        growth_signals=list(user_profile.get("progress_signals", []))[:3],
        continuity_note=str(user_profile.get("continuity_note", "No long-term continuity signal yet.")),
        top_topic=top_topic,
        strongest_signal=strongest_signal,
    )

    comparison = ReportComparisonSummary(
        messages=build_metric(len(all_period_messages), len(previous_period_messages)),
        chats=build_metric(len(chat_ids_in_period), len(chat_ids_in_previous_period)),
        average_risk=build_metric(
            round(sum(risk_scores) / len(risk_scores)) if risk_scores else 0,
            round(sum(previous_risk_scores) / len(previous_risk_scores)) if previous_risk_scores else 0,
        ),
        average_confidence=build_metric(
            round(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0,
            round(sum(previous_confidence_scores) / len(previous_confidence_scores)) if previous_confidence_scores else 0,
        ),
    )

    return ReportResponse(
        generated_at=now,
        filter_meta=ReportFilterMeta(
            range_key=range_key,
            range_label=range_label,
            assistant_scope=scope,
            comparison_label=comparison_label,
        ),
        summary=summary,
        recent_highlights=recent_highlights,
        recent_conversations=recent_conversations[:6],
        activity_timeline=ordered_days,
        topic_distribution=topic_distribution,
        urgency_distribution=urgency_distribution,
        assistant_distribution=assistant_distribution,
        provider_distribution=provider_distribution,
        comparison=comparison,
        response_health=ResponseHealthSummary(
            problem_solving=problem_solving_count,
            casual=casual_count,
            follow_up_needed=follow_up_needed,
        ),
    )
