from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.db import init_db
from routers import account, admin, auth, chat, private_ai, reports
from routers.auth import ensure_default_admin


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await ensure_default_admin()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LifeAI backend for authentication, conversations, assistant routing, and reports.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(account.router, prefix="/api/account", tags=["account"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(private_ai.router, prefix="/api/private-ai", tags=["private-ai"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
