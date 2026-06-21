from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Arize Phoenix observability — disabled to avoid gRPC port conflicts in local dev
# import phoenix as px
# from openinference.instrumentation.langchain import LangChainInstrumentor
# px.launch_app()
# LangChainInstrumentor().instrument()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(
    os.path.dirname(settings.FAISS_INDEX_PATH)
    if os.path.dirname(settings.FAISS_INDEX_PATH)
    else ".",
    exist_ok=True,
)

from app.db.database import engine  # noqa: E402
from app.db.models import Base  # noqa: E402

Base.metadata.create_all(bind=engine)

# ── Seed default admin user for local dev ──────────────────────────────────────
def _seed_default_user() -> None:
    """Create a default admin user if no users exist (dev convenience)."""
    from app.core.auth import hash_password
    from app.db.database import SessionLocal
    from app.db.models import User, UserRole

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                email="admin@nexus.dev",
                hashed_password=hash_password("admin"),
                role=UserRole.CURATOR,
            )
            db.add(admin)
            db.commit()
            print("✅ Default user created: admin@nexus.dev / admin")
    finally:
        db.close()

_seed_default_user()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="LLM-Powered Knowledge Retrieval Platform API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api import approval, auth, chat, documents, openai_compatible, users  # noqa: E402
from app.api import settings as settings_route  # noqa: E402

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(approval.router, prefix=settings.API_V1_STR)
app.include_router(documents.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(settings_route.router, prefix=settings.API_V1_STR)
app.include_router(openai_compatible.router, prefix="/v1")


@app.get("/api/health")
async def health_check():
    """Primary health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "llm_model": settings.LLM_MODEL,
        "llm_provider": settings.LLM_PROVIDER,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
