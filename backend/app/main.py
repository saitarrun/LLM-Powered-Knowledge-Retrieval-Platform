import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH) if os.path.dirname(settings.FAISS_INDEX_PATH) else ".", exist_ok=True)

from app.db.database import engine  # noqa: E402
from app.db.models import Base  # noqa: E402

Base.metadata.create_all(bind=engine)

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
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
