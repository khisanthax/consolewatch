from fastapi import APIRouter

from app.api.routes import console_entries, health, printers, sessions, watch

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(printers.router, prefix="/printers", tags=["printers"])
api_router.include_router(console_entries.router, prefix="/console-entries", tags=["console-entries"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(watch.router, prefix="/watch", tags=["watch"])
