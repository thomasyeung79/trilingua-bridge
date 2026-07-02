"""TriLingua Bridge V3 — FastAPI entry point."""
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, users, translate, coach, history, vocab, quota

app = FastAPI(
    title="TriLingua Bridge API",
    description="AI-powered multilingual communication assistant",
    version="3.0.0",
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Sentry
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment, traces_sample_rate=0.1)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(translate.router, prefix="/api/v1/translate", tags=["translate"])
app.include_router(coach.router, prefix="/api/v1/coach", tags=["coach"])
app.include_router(history.router, prefix="/api/v1/history", tags=["workspace"])
app.include_router(vocab.router, prefix="/api/v1/vocab", tags=["workspace"])
app.include_router(quota.router, prefix="/api/v1/quota", tags=["quota"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0"}
