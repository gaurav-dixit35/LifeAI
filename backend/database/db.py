from collections.abc import AsyncGenerator

from sqlalchemy import Column, DateTime, func, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config import settings


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def _apply_lightweight_migrations(sync_conn) -> None:
    inspector = inspect(sync_conn)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        user_column_specs = {
            "is_admin": "ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0",
            "google_sub": "ALTER TABLE users ADD COLUMN google_sub VARCHAR",
            "reset_token": "ALTER TABLE users ADD COLUMN reset_token VARCHAR",
            "reset_token_expires_at": "ALTER TABLE users ADD COLUMN reset_token_expires_at DATETIME",
            "bio": "ALTER TABLE users ADD COLUMN bio TEXT",
            "avatar_emoji": "ALTER TABLE users ADD COLUMN avatar_emoji VARCHAR",
            "avatar_image": "ALTER TABLE users ADD COLUMN avatar_image TEXT",
            "weekly_focus": "ALTER TABLE users ADD COLUMN weekly_focus VARCHAR",
            "preferred_tone": "ALTER TABLE users ADD COLUMN preferred_tone VARCHAR",
            "support_focus": "ALTER TABLE users ADD COLUMN support_focus VARCHAR",
            "profile_goals": "ALTER TABLE users ADD COLUMN profile_goals TEXT",
            "workspace_settings": "ALTER TABLE users ADD COLUMN workspace_settings TEXT",
        }
        for column_name, statement in user_column_specs.items():
            if column_name not in user_columns:
                sync_conn.execute(text(statement))

    if "chats" in tables:
        chat_columns = {column["name"] for column in inspector.get_columns("chats")}
        if "is_pinned" not in chat_columns:
            sync_conn.execute(text("ALTER TABLE chats ADD COLUMN is_pinned BOOLEAN NOT NULL DEFAULT 0"))

    if "messages" in tables:
        message_columns = {column["name"] for column in inspector.get_columns("messages")}
        if "is_saved" not in message_columns:
            sync_conn.execute(text("ALTER TABLE messages ADD COLUMN is_saved BOOLEAN NOT NULL DEFAULT 0"))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_apply_lightweight_migrations)
