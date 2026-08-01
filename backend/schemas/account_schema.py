from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


AnswerDensity = Literal["balanced", "detailed"]
DashboardDensity = Literal["comfortable", "compact"]
DefaultLandingPage = Literal["dashboard", "workspace"]
ExportFormat = Literal["json", "csv", "markdown"]
PreferredTone = Literal["practical", "supportive", "direct"]


class WorkspaceSettings(BaseModel):
    showSuggestedPrompts: bool = True
    showTypingAnimation: bool = True
    showSolutionCards: bool = True
    showMessageActions: bool = True
    showDashboardCharts: bool = True
    dashboardDensity: DashboardDensity = "comfortable"
    answerDensity: AnswerDensity = "balanced"
    confirmBeforeDelete: bool = True
    showConversationPreviews: bool = True
    defaultLandingPage: DefaultLandingPage = "dashboard"
    reduceMotion: bool = False
    exportFormat: ExportFormat = "json"
    sendOnEnter: bool = True
    autoScrollChat: bool = True
    showRiskMeter: bool = True
    showConfidenceBadge: bool = True


class WorkspaceSettingsUpdate(WorkspaceSettings):
    pass


class ProfileGoalItem(BaseModel):
    label: str = Field(min_length=2, max_length=50)


class AccountProfileResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    bio: str
    avatar_emoji: str
    avatar_image: str | None = None
    weekly_focus: str
    preferred_tone: PreferredTone
    support_focus: str
    profile_goals: list[str]

    model_config = {"from_attributes": True}


class AccountProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    bio: str = Field(min_length=0, max_length=300)
    avatar_emoji: str = Field(min_length=1, max_length=4)
    avatar_image: str | None = Field(default=None, max_length=3_000_000)
    weekly_focus: str = Field(min_length=0, max_length=160)
    preferred_tone: PreferredTone = "practical"
    support_focus: str = Field(min_length=0, max_length=80)
    profile_goals: list[str] = Field(default_factory=list, max_length=8)
