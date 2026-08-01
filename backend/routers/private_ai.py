from fastapi import APIRouter, Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db
from models.chat_model import Chat
from models.user_model import User
from routers.auth import get_current_user
from schemas.chat_schema import PrivateAIStatusResponse, PrivateEphemeralRequest, PrivateEphemeralResponse
from services.private_ai_service import PrivateAIService

router = APIRouter()
private_ai_service = PrivateAIService()


@router.get("/status", response_model=PrivateAIStatusResponse)
async def private_ai_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PrivateAIStatusResponse:
    status = await private_ai_service.status()
    count_result = await db.execute(
        select(func.count(Chat.id)).where(Chat.user_id == current_user.id, Chat.personality_mode == "private")
    )
    stored_private_chats = int(count_result.scalar() or 0)
    return PrivateAIStatusResponse(**status, stored_private_chats=stored_private_chats)


@router.post("/ephemeral", response_model=PrivateEphemeralResponse)
async def private_ai_ephemeral(
    payload: PrivateEphemeralRequest,
    _: User = Depends(get_current_user),
) -> PrivateEphemeralResponse:
    content, provider_used = await private_ai_service.generate_reply(
        user_message=payload.message,
        context=payload.context,
    )
    analysis = private_ai_service.build_analysis(provider_used)
    return PrivateEphemeralResponse(content=content, provider_used=provider_used, analysis=analysis)


@router.delete("/history")
async def clear_private_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, int | str]:
    count_result = await db.execute(
        select(func.count(Chat.id)).where(Chat.user_id == current_user.id, Chat.personality_mode == "private")
    )
    deleted_chats = int(count_result.scalar() or 0)
    await db.execute(
        delete(Chat).where(Chat.user_id == current_user.id, Chat.personality_mode == "private")
    )
    await db.commit()
    return {"message": "Private history cleared", "deleted_chats": deleted_chats}
