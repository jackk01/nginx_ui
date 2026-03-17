from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import asyncio
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.services.auth_service import get_current_user
from app.services.config_service import LogService
from app.models.models import User, Server

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[int, WebSocket] = {}


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """Get user from WebSocket token"""
    from jose import JWTError, jwt
    from app.core.config import settings
    from app.services.auth_service import pwd_context
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


@router.websocket("/ws/logs/{server_id}")
async def websocket_log_tail(
    websocket: WebSocket,
    server_id: int,
    token: str = None
):
    """WebSocket endpoint for real-time log tailing"""
    
    # Accept connection
    await websocket.accept()
    
    # Authenticate (optional - for now allow without auth for simplicity)
    # if token:
    #     async with AsyncSessionLocal() as db:
    #         user = await get_user_from_token(token, db)
    #         if not user:
    #             await websocket.close(code=4001)
    #             return
    
    # Get server config
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()
        
        if not server:
            await websocket.send_json({
                "type": "error",
                "message": "Server not found"
            })
            await websocket.close()
            return
        
        # Initialize log service
        server_dict = {
            "host": server.host,
            "port": server.port,
            "username": server.username,
            "password": server.password,
            "ssh_key_path": server.ssh_key_path,
            "nginx_log_path": server.nginx_log_path,
            "mode": server.mode
        }
        
        log_service = LogService(server_dict)
        
        # Store connection
        active_connections[server_id] = websocket
        
        try:
            # Send initial connection success
            await websocket.send_json({
                "type": "status",
                "message": "Connected to log stream"
            })
            
            # Handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    action = message.get("action")
                    
                    if action == "start":
                        # Start tailing
                        log_path = message.get("log_path")
                        lines = message.get("lines", 50)
                        
                        # Send initial content
                        log_data = await log_service.read_log_file(log_path, lines)
                        await websocket.send_json({
                            "type": "log",
                            "content": log_data["content"],
                            "total_lines": log_data["total_lines"]
                        })
                        
                    elif action == "stop":
                        # Stop tailing
                        break
                        
                    elif action == "ping":
                        # Keep alive
                        await websocket.send_json({
                            "type": "pong"
                        })
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e)
                    })
                    
        except WebSocketDisconnect:
            pass
        finally:
            if server_id in active_connections:
                del active_connections[server_id]