from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.user_model import User
from routers.auth import get_current_user
from schemas.account_schema import (
    AccountProfileResponse,
    AccountProfileUpdate,
    WorkspaceSettings,
    WorkspaceSettingsUpdate,
)


router = APIRouter()

DEFAULT_SETTINGS = WorkspaceSettings().model_dump()
DEFAULT_PROFILE = {
    "bio": "Building clarity one practical step at a time.",
    "avatar_emoji": "🧠",
    "weekly_focus": "",
    "preferred_tone": "practical",
    "support_focus": "daily-life clarity",
    "profile_goals": [],
}


def _deserialize_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return fallback
    return parsed


def build_profile_response(user: User) -> AccountProfileResponse:
    return AccountProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        created_at=user.created_at,
        bio=user.bio or DEFAULT_PROFILE["bio"],
        avatar_emoji=user.avatar_emoji or DEFAULT_PROFILE["avatar_emoji"],
        avatar_image=user.avatar_image,
        weekly_focus=user.weekly_focus or DEFAULT_PROFILE["weekly_focus"],
        preferred_tone=(user.preferred_tone or DEFAULT_PROFILE["preferred_tone"]),
        support_focus=user.support_focus or DEFAULT_PROFILE["support_focus"],
        profile_goals=list(_deserialize_json(user.profile_goals, DEFAULT_PROFILE["profile_goals"])),
    )


def build_settings_response(user: User) -> WorkspaceSettings:
    stored = _deserialize_json(user.workspace_settings, {})
    if not isinstance(stored, dict):
        stored = {}
    return WorkspaceSettings.model_validate({**DEFAULT_SETTINGS, **stored})


@router.get("/profile", response_model=AccountProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)) -> AccountProfileResponse:
    return build_profile_response(current_user)


@router.put("/profile", response_model=AccountProfileResponse)
async def update_profile(
    payload: AccountProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AccountProfileResponse:
    current_user.name = payload.name.strip()
    current_user.bio = payload.bio.strip()
    current_user.avatar_emoji = payload.avatar_emoji
    current_user.avatar_image = payload.avatar_image
    current_user.weekly_focus = payload.weekly_focus.strip()
    current_user.preferred_tone = payload.preferred_tone
    current_user.support_focus = payload.support_focus.strip()
    current_user.profile_goals = json.dumps(payload.profile_goals)
    await db.commit()
    await db.refresh(current_user)
    return build_profile_response(current_user)


@router.get("/settings", response_model=WorkspaceSettings)
async def get_settings(current_user: User = Depends(get_current_user)) -> WorkspaceSettings:
    return build_settings_response(current_user)


@router.put("/settings", response_model=WorkspaceSettings)
async def update_settings(
    payload: WorkspaceSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceSettings:
    settings_payload = payload.model_dump()
    current_user.workspace_settings = json.dumps(settings_payload)
    await db.commit()
    await db.refresh(current_user)
    return WorkspaceSettings.model_validate(settings_payload)
