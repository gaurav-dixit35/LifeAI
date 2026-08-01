import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship

from database.db import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    google_sub = Column(String, unique=True, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_emoji = Column(String, nullable=True)
    avatar_image = Column(Text, nullable=True)
    weekly_focus = Column(String, nullable=True)
    preferred_tone = Column(String, nullable=True)
    support_focus = Column(String, nullable=True)
    profile_goals = Column(Text, nullable=True)
    workspace_settings = Column(Text, nullable=True)

    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
