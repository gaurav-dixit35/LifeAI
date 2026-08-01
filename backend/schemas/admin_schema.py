from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from schemas.chat_schema import ReportBreakdownItem


class AdminSummary(BaseModel):
    total_users: int
    admin_users: int
    active_users_7d: int
    total_chats: int
    total_messages: int
    life_questions: int
    code_questions: int
    private_chats: int
    uploads_processed: int
    average_risk: int
    average_confidence: int


class AdminTimelinePoint(BaseModel):
    day: str
    new_users: int
    active_users: int
    messages: int


class ProviderHealthItem(BaseModel):
    provider: str
    configured: bool
    healthy: bool
    model: str
    detail: str


class AdminAlertItem(BaseModel):
    severity: Literal["info", "warning", "critical"]
    title: str
    detail: str


class AdminUserSnapshot(BaseModel):
    id: str
    name: str
    email: str
    is_admin: bool
    is_active: bool
    chats: int
    messages: int
    created_at: datetime
    last_active: datetime | None = None


class AdminChatSnapshot(BaseModel):
    id: str
    title: str
    personality_mode: str
    user_name: str
    preview: str
    message_count: int
    updated_at: datetime
    assistant_kind: str = "life"
    provider_used: str = "local"
    urgency_label: str = "low"
    risk_level: int = 0


class FlaggedChatSnapshot(BaseModel):
    id: str
    title: str
    user_name: str
    assistant_kind: str
    provider_used: str
    urgency_label: str
    risk_level: int
    updated_at: datetime
    preview: str


class AdminUserUpdateRequest(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


class AdminMutationResponse(BaseModel):
    message: str


class AdminOverviewResponse(BaseModel):
    generated_at: datetime
    summary: AdminSummary
    assistant_distribution: list[ReportBreakdownItem]
    provider_distribution: list[ReportBreakdownItem]
    topic_distribution: list[ReportBreakdownItem]
    activity_timeline: list[AdminTimelinePoint]
    provider_health: list[ProviderHealthItem]
    alerts: list[AdminAlertItem]
    flagged_chats: list[FlaggedChatSnapshot]
    recent_users: list[AdminUserSnapshot]
    recent_chats: list[AdminChatSnapshot]
