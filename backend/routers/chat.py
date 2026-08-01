import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.db import get_db
from models.chat_model import Chat, Message
from models.user_model import User
from routers.auth import get_current_user
from schemas.chat_schema import (
    AnalysisResult,
    ChatCreate,
    ChatListResponse,
    ChatReplyResponse,
    ChatResponse,
    MessageResponse,
    PinChatUpdate,
    SavedMessageResponse,
    SavedMessageUpdate,
)
from services.code_ai_service import CodeAIService
from services.llm_service import LLMService
from services.memory_service import MemoryService
from services.private_ai_service import PrivateAIService
from services.provider_fallback_service import ProviderFallbackService


router = APIRouter()
llm_service = LLMService()
memory_service = MemoryService()
provider_service = ProviderFallbackService()
code_ai_service = CodeAIService()
private_ai_service = PrivateAIService()


def normalize_personality_mode(value: str) -> str:
    return value if value == "private" else "life"


def serialize_message(message: Message) -> MessageResponse:
    analysis = AnalysisResult.model_validate(json.loads(message.analysis)) if message.analysis else None
    return MessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        analysis=analysis,
        is_saved=bool(message.is_saved),
    )


def serialize_saved_message(message: Message) -> SavedMessageResponse:
    analysis = AnalysisResult.model_validate(json.loads(message.analysis)) if message.analysis else None
    return SavedMessageResponse(
        id=message.id,
        chat_id=message.chat_id,
        chat_title=message.chat.title if message.chat else "Untitled chat",
        personality_mode=normalize_personality_mode(message.chat.personality_mode if message.chat else "life"),
        role="assistant",
        content=message.content,
        created_at=message.created_at,
        analysis=analysis,
        is_saved=bool(message.is_saved),
    )


def serialize_chat(chat: Chat) -> ChatResponse:
    return ChatResponse(
        id=chat.id,
        title=chat.title,
        user_id=chat.user_id,
        personality_mode=normalize_personality_mode(chat.personality_mode),
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        is_pinned=bool(chat.is_pinned),
        messages=[serialize_message(message) for message in chat.messages],
    )


async def build_history(current_user: User, db: AsyncSession) -> tuple[list[Chat], list[Message]]:
    history_result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
        .order_by(Chat.updated_at.desc())
    )
    history_chats = history_result.scalars().unique().all()
    history_messages = [message for history_chat in history_chats for message in history_chat.messages]
    return history_chats, history_messages


async def build_life_reply(
    *,
    user_message: str,
    context: str,
    pattern_signals: list[dict[str, str]],
    user_profile: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    analysis_payload = await llm_service.generate_analysis(
        user_message=user_message,
        context=context,
        personality_mode="life",
        pattern_signals=pattern_signals,
        user_profile=user_profile,
    )
    analysis_payload["assistant_kind"] = "life"
    analysis_payload["knowledge_source"] = "daily-life workspace"
    analysis_payload["uploaded_file_name"] = None
    provider_used = "local"

    system_prompt = (
        "You are LifeAI, a practical daily-life assistant. Answer normal human questions clearly, concretely, and calmly. "
        "Use the provided analysis as guidance, but write naturally and directly."
    )
    user_prompt = (
        f"Recent context:\n{context or 'No prior context.'}\n\n"
        f"User question:\n{user_message}\n\n"
        f"Baseline analysis:\n{json.dumps({key: value for key, value in analysis_payload.items() if not str(key).startswith('_')}, ensure_ascii=True)}\n\n"
        "Write the best direct answer for the user. Focus on practical steps, relevance, and calm clarity."
    )
    try:
        provider_response = await provider_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=950,
            temperature=0.35,
        )
        provider_used = provider_response.provider
        assistant_text = provider_response.content
    except Exception:
        assistant_text = llm_service.compose_reply(analysis_payload, "life")

    analysis_payload["provider_used"] = provider_used
    return analysis_payload, assistant_text


@router.get("/saved", response_model=list[SavedMessageResponse])
async def list_saved_replies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedMessageResponse]:
    result = await db.execute(
        select(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Chat.user_id == current_user.id, Message.role == "assistant", Message.is_saved.is_(True))
        .options(selectinload(Message.chat))
        .order_by(Message.created_at.desc())
    )
    messages = result.scalars().unique().all()
    return [serialize_saved_message(message) for message in messages]


@router.get("/", response_model=list[ChatListResponse])
async def list_chats(
    personality_mode: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatListResponse]:
    query = (
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
        .order_by(Chat.is_pinned.desc(), Chat.updated_at.desc())
    )
    if personality_mode in {"life", "private"}:
        query = query.where(Chat.personality_mode == personality_mode)

    result = await db.execute(query)
    chats = result.scalars().unique().all()

    items: list[ChatListResponse] = []
    for chat in chats:
        preview = chat.messages[-1].content[:120] if chat.messages else None
        items.append(
            ChatListResponse(
                id=chat.id,
                title=chat.title,
                personality_mode=normalize_personality_mode(chat.personality_mode),
                created_at=chat.created_at,
                updated_at=chat.updated_at,
                preview=preview,
                is_pinned=bool(chat.is_pinned),
            )
        )
    return items


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    personality_mode = normalize_personality_mode(chat_data.personality_mode)
    default_title = "New Private AI chat" if personality_mode == "private" else "New LifeAI chat"
    chat = Chat(
        title=chat_data.title or default_title,
        user_id=current_user.id,
        personality_mode=personality_mode,
    )
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return ChatResponse(
        id=chat.id,
        title=chat.title,
        user_id=chat.user_id,
        personality_mode=normalize_personality_mode(chat.personality_mode),
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        is_pinned=bool(chat.is_pinned),
        messages=[],
    )


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    result = await db.execute(
        select(Chat)
        .where(Chat.id == chat_id, Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return serialize_chat(chat)


@router.post("/{chat_id}/pin", response_model=ChatListResponse)
async def pin_chat(
    chat_id: str,
    payload: PinChatUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatListResponse:
    result = await db.execute(
        select(Chat)
        .where(Chat.id == chat_id, Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    chat.is_pinned = payload.is_pinned
    await db.commit()
    await db.refresh(chat)
    preview = chat.messages[-1].content[:120] if chat.messages else None
    return ChatListResponse(
        id=chat.id,
        title=chat.title,
        personality_mode=normalize_personality_mode(chat.personality_mode),
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        preview=preview,
        is_pinned=bool(chat.is_pinned),
    )


@router.post("/messages/{message_id}/save", response_model=MessageResponse)
async def save_message(
    message_id: str,
    payload: SavedMessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    result = await db.execute(
        select(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Message.id == message_id, Chat.user_id == current_user.id, Message.role == "assistant")
        .options(selectinload(Message.chat))
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="Assistant message not found")

    message.is_saved = payload.is_saved
    await db.commit()
    await db.refresh(message)
    return serialize_message(message)


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(select(Chat).where(Chat.id == chat_id, Chat.user_id == current_user.id))
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    await db.delete(chat)
    await db.commit()
    return {"message": "Chat deleted"}


@router.post("/{chat_id}/regenerate", response_model=ChatReplyResponse)
async def regenerate_last_reply(
    chat_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatReplyResponse:
    result = await db.execute(
        select(Chat)
        .where(Chat.id == chat_id, Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    user_messages = [message for message in chat.messages if message.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message available to regenerate from")

    latest_user_message = user_messages[-1]
    scoped_messages: list[Message] = []
    for message in chat.messages:
        scoped_messages.append(message)
        if message.id == latest_user_message.id:
            break

    context = memory_service.build_context(scoped_messages)
    _, history_messages = await build_history(current_user, db)
    pattern_signals = memory_service.extract_patterns(history_messages)
    user_profile = memory_service.build_user_profile(history_messages)

    if normalize_personality_mode(chat.personality_mode) == "private":
        analysis_payload = private_ai_service.build_analysis("ollama")
        assistant_text, provider_used = await private_ai_service.generate_reply(user_message=latest_user_message.content, context=context)
        analysis_payload["provider_used"] = provider_used
    elif code_ai_service.is_code_query(latest_user_message.content):
        retrieval = code_ai_service.retrieve_context(latest_user_message.content)
        try:
            assistant_text, provider_used = await code_ai_service.generate_reply(
                user_message=latest_user_message.content,
                context=context,
                retrieval=retrieval,
                provider_service=provider_service,
            )
        except Exception:
            assistant_text = code_ai_service.local_fallback_reply(retrieval)
            provider_used = "local"
        analysis_payload = code_ai_service.build_analysis(
            user_message=latest_user_message.content,
            retrieval=retrieval,
            provider_used=provider_used,
        )
    else:
        analysis_payload, assistant_text = await build_life_reply(
            user_message=latest_user_message.content,
            context=context,
            pattern_signals=pattern_signals,
            user_profile=user_profile,
        )

    analysis = AnalysisResult.model_validate(analysis_payload)
    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        content=assistant_text,
        analysis=analysis.model_dump_json(),
        is_saved=False,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return ChatReplyResponse(
        message=serialize_message(assistant_message),
        analysis=analysis,
    )


@router.post("/{chat_id}/messages", response_model=ChatReplyResponse)
async def send_message(
    chat_id: str,
    content: str = Form(default=""),
    file: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatReplyResponse:
    result = await db.execute(
        select(Chat)
        .where(Chat.id == chat_id, Chat.user_id == current_user.id)
        .options(selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    uploaded_text: str | None = None
    uploaded_file_name: str | None = None
    if file is not None:
        uploaded_file_name = file.filename or "uploaded-file"
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        try:
            uploaded_text = code_ai_service.extract_text_from_upload(uploaded_file_name, file_bytes)
        except Exception as error:
            raise HTTPException(status_code=400, detail=f"Could not read uploaded file: {error}") from error
        if not uploaded_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file")

    normalized_content = content.strip()
    if not normalized_content and uploaded_file_name:
        normalized_content = f"Analyze the uploaded file {uploaded_file_name} and help me with the coding issue or code context inside it."

    if not normalized_content:
        raise HTTPException(status_code=422, detail="Message content or upload is required")

    stored_user_content = normalized_content
    if uploaded_file_name:
        stored_user_content = f"{normalized_content}\n\n[Uploaded file: {uploaded_file_name}]"

    user_message = Message(chat_id=chat.id, role="user", content=stored_user_content, is_saved=False)
    db.add(user_message)
    await db.flush()

    all_messages = [*chat.messages, user_message]
    context = memory_service.build_context(all_messages)
    _, history_messages = await build_history(current_user, db)
    pattern_signals = memory_service.extract_patterns(history_messages)
    user_profile = memory_service.build_user_profile(history_messages)

    mode = normalize_personality_mode(chat.personality_mode)
    if mode == "private":
        analysis_payload = private_ai_service.build_analysis("ollama")
        assistant_text, provider_used = await private_ai_service.generate_reply(user_message=normalized_content, context=context)
        analysis_payload["provider_used"] = provider_used
    else:
        use_code_ai = bool(uploaded_text) or code_ai_service.is_code_query(normalized_content)
        if use_code_ai:
            retrieval = code_ai_service.retrieve_context(
                normalized_content,
                uploaded_text=uploaded_text,
                uploaded_file_name=uploaded_file_name,
            )
            try:
                assistant_text, provider_used = await code_ai_service.generate_reply(
                    user_message=normalized_content,
                    context=context,
                    retrieval=retrieval,
                    provider_service=provider_service,
                )
            except Exception:
                assistant_text = code_ai_service.local_fallback_reply(retrieval)
                provider_used = "local"
            analysis_payload = code_ai_service.build_analysis(
                user_message=normalized_content,
                retrieval=retrieval,
                provider_used=provider_used,
            )
        else:
            analysis_payload, assistant_text = await build_life_reply(
                user_message=normalized_content,
                context=context,
                pattern_signals=pattern_signals,
                user_profile=user_profile,
            )

    analysis = AnalysisResult.model_validate(analysis_payload)
    assistant_message = Message(
        chat_id=chat.id,
        role="assistant",
        content=assistant_text,
        analysis=analysis.model_dump_json(),
        is_saved=False,
    )
    db.add(assistant_message)

    default_title = "New Private AI chat" if mode == "private" else "New LifeAI chat"
    if chat.title == default_title or not chat.title.strip():
        chat.title = normalized_content[:60]

    await db.commit()
    await db.refresh(assistant_message)

    return ChatReplyResponse(
        message=serialize_message(assistant_message),
        analysis=analysis,
    )
