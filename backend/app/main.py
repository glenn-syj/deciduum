from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import secrets

from app.core.config import get_settings
from app.core.database import init_db
from app.routers import decisions, memos, directions, today, tasks, logs


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Close connections
    pass


app = FastAPI(
    title="Deciduum API",
    description="Time-based decision and cognition log",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key Authentication Dependency
async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "API key is required",
                    "details": {"header": "X-API-Key"},
                }
            },
        )

    # Use configured API key or allow any key if not configured
    if settings.deciduum_api_key and x_api_key != settings.deciduum_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid API key",
                    "details": {},
                }
            },
        )

    return x_api_key


# Health check (no auth required)
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# Include routers with API key dependency
app.include_router(
    decisions.router, prefix="/v1", dependencies=[Depends(verify_api_key)]
)
app.include_router(memos.router, prefix="/v1", dependencies=[Depends(verify_api_key)])
app.include_router(
    directions.router, prefix="/v1", dependencies=[Depends(verify_api_key)]
)
app.include_router(today.router, prefix="/v1", dependencies=[Depends(verify_api_key)])
app.include_router(tasks.router, prefix="/v1", dependencies=[Depends(verify_api_key)])
app.include_router(logs.router, prefix="/v1", dependencies=[Depends(verify_api_key)])


@app.get("/")
async def root():
    return {"message": "Deciduum API", "version": "1.0.0"}
