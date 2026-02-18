from fastapi import APIRouter
from app.routers import decisions, memos, directions, today

api_router = APIRouter(prefix="/v1")

api_router.include_router(decisions.router, prefix="/decisions", tags=["decisions"])
api_router.include_router(memos.router, prefix="/memos", tags=["memos"])
api_router.include_router(directions.router, prefix="/directions", tags=["directions"])
api_router.include_router(today.router, prefix="/today", tags=["today"])
