from app.api.auth import router as auth_router
from app.api.servers import router as servers_router
from app.api.websocket import router as websocket_router

__all__ = ["auth_router", "servers_router", "websocket_router"]