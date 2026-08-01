from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ToolSchema(BaseModel):
    name: str
    description: str
    required: bool = True


class PatternSignal(BaseModel):
    title: str
    detail: str


class AnalysisResult(BaseModel):
    assistant_kind: Literal["life", "code", "private"] = "life"
    provider_used: str = "local"
    knowledge_source: str = ""
    uploaded_file_name: str | None = None
    conversation_mode: Literal["casual", "problem_solving"] = "problem_solving"
    problem_summary: str
    core_issue: str
    emotional_tone: str
    urgency_label: Literal["low", "guarded", "elevated", "high", "critical"] = "low"
    response_strategy: str
    risk_level: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    recommendation: Literal["steady", "caution", "support", "urgent_support"]
    detected_needs: list[str]
    strengths: list[str]
    hidden_risk_factors: list[str]
    decision_lens: str = ""
    suggestions: list[str]
    action_plan: list[str]
    immediate_actions: list[str] = []
    short_term_actions: list[str] = []
    long_term_actions: list[str] = []
    avoid_now: list[str] = []
    next_best_step: str
    follow_up_question: str
    reflection_prompt: str
    pattern_signals: list[PatternSignal]
    tools: list[ToolSchema]
    safety_notes: list[str]
    when_to_seek_support: list[str] = []
    personalization_note: str = ""
    continuity_note: str = ""
    unresolved_threads: list[str] = []
    progress_signals: list[str] = []


class MessageCreate(BaseModel):
    content: str = Field(default="", max_length=4000)


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime
    analysis: AnalysisResult | None = None
    is_saved: bool = False

    model_config = {"from_attributes": True}


class SavedMessageResponse(BaseModel):
    id: str
    chat_id: str
    chat_title: str
    personality_mode: str
    role: Literal["assistant"]
    content: str
    created_at: datetime
    analysis: AnalysisResult | None = None
    is_saved: bool = True


class ChatCreate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    personality_mode: Literal["life", "private"] = "life"

    @field_validator("personality_mode")
    @classmethod
    def normalize_personality_mode(cls, value: str) -> str:
        return value if value in {"life", "private"} else "life"


class ChatListResponse(BaseModel):
    id: str
    title: str
    personality_mode: str
    created_at: datetime
    updated_at: datetime
    preview: str | None = None
    is_pinned: bool = False

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    id: str
    title: str
    user_id: str
    personality_mode: str
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class ChatReplyResponse(BaseModel):
    message: MessageResponse
    analysis: AnalysisResult


class PinChatUpdate(BaseModel):
    is_pinned: bool


class SavedMessageUpdate(BaseModel):
    is_saved: bool


class PrivateAIStatusResponse(BaseModel):
    ollama_running: bool
    model_available: bool
    model: str
    stored_private_chats: int = 0


class PrivateEphemeralRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: str = Field(default="", max_length=12000)


class PrivateEphemeralResponse(BaseModel):
    content: str
    provider_used: str
    analysis: AnalysisResult


class ReportTimelinePoint(BaseModel):
    day: str
    messages: int
    chats: int
    average_risk: int


class ReportBreakdownItem(BaseModel):
    label: str
    value: int


class ResponseHealthSummary(BaseModel):
    problem_solving: int
    casual: int
    follow_up_needed: int


class ReportSummary(BaseModel):
    total_chats: int
    total_messages: int
    average_risk: int
    average_confidence: int
    messages_this_week: int
    estimated_minutes: int
    common_emotions: list[str]
    recurring_patterns: list[str]
    weekly_focus: str
    active_themes: list[str]
    support_gaps: list[str]
    growth_signals: list[str]
    continuity_note: str
    top_topic: str
    strongest_signal: str


class ReportFilterMeta(BaseModel):
    range_key: Literal["7d", "30d", "all"]
    range_label: str
    assistant_scope: Literal["all", "life", "code"]
    comparison_label: str


class ReportComparisonMetric(BaseModel):
    current: int
    previous: int
    delta: int


class ReportComparisonSummary(BaseModel):
    messages: ReportComparisonMetric
    chats: ReportComparisonMetric
    average_risk: ReportComparisonMetric
    average_confidence: ReportComparisonMetric


class RecentConversationSnapshot(BaseModel):
    id: str
    title: str
    preview: str
    updated_at: datetime
    assistant_kind: Literal["life", "code"]
    provider_used: str


class ReportResponse(BaseModel):
    generated_at: datetime
    filter_meta: ReportFilterMeta
    summary: ReportSummary
    recent_highlights: list[str]
    recent_conversations: list[RecentConversationSnapshot]
    activity_timeline: list[ReportTimelinePoint]
    topic_distribution: list[ReportBreakdownItem]
    urgency_distribution: list[ReportBreakdownItem]
    assistant_distribution: list[ReportBreakdownItem]
    provider_distribution: list[ReportBreakdownItem]
    comparison: ReportComparisonSummary
    response_health: ResponseHealthSummary
