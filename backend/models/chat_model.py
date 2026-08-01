import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from database.db import Base, TimestampMixin


class Chat(Base, TimestampMixin):
    __tablename__ = "chats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False, default="New LifeAI chat")
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    personality_mode = Column(String, nullable=False, default="life")
    is_pinned = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = Column(String, ForeignKey("chats.id"), index=True, nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    analysis = Column(Text, nullable=True)
    is_saved = Column(Boolean, default=False, nullable=False)

    chat = relationship("Chat", back_populates="messages")
