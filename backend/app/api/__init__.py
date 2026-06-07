from fastapi import APIRouter

from app.api.routes import health, printers

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(printers.router, prefix="/printers", tags=["printers"])
