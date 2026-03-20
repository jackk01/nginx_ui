from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.schemas.schemas import (
    ServerCreate, ServerUpdate, ServerResponse,
    ServerConnectionTest, ConfigFileTree, LogFileResponse,
    ConfigFileContent
)
from app.services.auth_service import get_current_user
from app.services.ssh_service import get_client
from app.services.nginx_service import NginxService
from app.services.config_service import ConfigService, LogService
from app.models.models import User, Server
import urllib.parse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/servers", tags=["Servers"])


def server_to_dict(server: Server) -> dict:
    """Convert server model to dictionary"""
    return {
        "id": server.id,
        "user_id": server.user_id,
        "name": server.name,
        "host": server.host,
        "port": server.port,
        "username": server.username,
        "password": server.password,
        "ssh_key_path": server.ssh_key_path,
        "nginx_path": server.nginx_path,
        "nginx_conf_path": server.nginx_conf_path,
        "nginx_log_path": server.nginx_log_path,
        "mode": server.mode,
        "status": server.status,
        "created_at": server.created_at,
        "updated_at": server.updated_at
    }


@router.get("", response_model=List[ServerResponse])
async def get_servers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all servers for current user"""
    result = await db.execute(
        select(Server).where(Server.user_id == current_user.id)
    )
    servers = result.scalars().all()
    return [ServerResponse.model_validate(s) for s in servers]


@router.post("", response_model=ServerResponse)
async def create_server(
    server_data: ServerCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new server"""
    server = Server(
        user_id=current_user.id,
        name=server_data.name,
        host=server_data.host,
        port=server_data.port,
        username=server_data.username,
        password=server_data.password,
        ssh_key_path=server_data.ssh_key_path,
        nginx_path=server_data.nginx_path,
        nginx_conf_path=server_data.nginx_conf_path,
        nginx_log_path=server_data.nginx_log_path,
        mode=server_data.mode,
        status="offline"
    )
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return ServerResponse.model_validate(server)


@router.get("/{server_id}", response_model=ServerResponse)
async def get_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get server by ID"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    return ServerResponse.model_validate(server)


@router.put("/{server_id}", response_model=ServerResponse)
async def update_server(
    server_id: int,
    server_data: ServerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update server"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    # Update fields
    update_data = server_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)
    
    await db.commit()
    await db.refresh(server)
    return ServerResponse.model_validate(server)


@router.delete("/{server_id}")
async def delete_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete server"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    await db.delete(server)
    await db.commit()
    
    return {"message": "Server deleted successfully"}


@router.post("/{server_id}/test-connection", response_model=ServerConnectionTest)
async def test_connection(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test SSH connection"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    try:
        client = get_client(
            server.host,
            server.port,
            server.username or "",
            server.mode,
            server.password,
            server.ssh_key_path
        )

        if server.mode == "local" or server.host in ["localhost", "127.0.0.1", ""]:
            return ServerConnectionTest(success=True, message="Local server")

        # Test SSH connection
        success = await client.connect()

        if success:
            await client.close()
            return ServerConnectionTest(success=True, message="Connection successful")
        else:
            return ServerConnectionTest(success=False, message="Connection failed")
    except Exception as e:
        return ServerConnectionTest(success=False, message=str(e))


@router.post("/{server_id}/check-status")
async def check_server_status(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check and update server online/offline status"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()

    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )

    try:
        client = get_client(
            server.host,
            server.port,
            server.username or "",
            server.mode,
            server.password,
            server.ssh_key_path
        )

        # For local mode or localhost, always online
        if server.mode == "local" or server.host in ["localhost", "127.0.0.1", ""]:
            server.status = "online"
            await db.commit()
            return {"status": "online", "message": "Local server is online"}

        # For remote mode, test SSH connection
        success = await client.connect()

        if success:
            await client.close()
            server.status = "online"
            await db.commit()
            return {"status": "online", "message": "Server is online"}
        else:
            server.status = "offline"
            await db.commit()
            return {"status": "offline", "message": "Cannot connect to server"}
    except Exception as e:
        server.status = "offline"
        await db.commit()
        return {"status": "offline", "message": str(e)}


# ==================== Config API ====================

@router.get("/{server_id}/config/files")
async def get_config_files(
    server_id: int,
    path: str = "",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration files"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    config_service = ConfigService(server_to_dict(server))
    
    # Decode URL-encoded path
    decoded_path = urllib.parse.unquote(path)
    # Support both relative path and absolute path for robust breadcrumb navigation.
    if not decoded_path:
        target_path = server.nginx_conf_path
    elif decoded_path.startswith('/'):
        target_path = decoded_path
    else:
        target_path = f"{server.nginx_conf_path}/{decoded_path}"
    
    files = await config_service.list_config_files(target_path)
    return files


@router.get("/{server_id}/config/files/{file_path:path}")
async def get_config_file_content(
    server_id: int,
    file_path: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get configuration file content"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    config_service = ConfigService(server_to_dict(server))
    decoded_path = urllib.parse.unquote(file_path)
    
    # Determine if this is an absolute path or relative path
    # If it starts with '/', treat it as absolute path from root
    # Otherwise, treat it as relative to nginx_conf_path
    if decoded_path.startswith('/'):
        # Absolute path - use directly after decoding
        target_path = decoded_path
    else:
        # Relative path - prepend nginx_conf_path
        target_path = f"{server.nginx_conf_path}/{decoded_path}"

    # DEBUG: Log the path resolution
    logger.info(f"[DEBUG] get_config_file_content called:")
    logger.info(f"  - server_id: {server_id}")
    logger.info(f"  - file_path (raw): {file_path}")
    logger.info(f"  - decoded_path: {decoded_path}")
    logger.info(f"  - server.nginx_conf_path: {server.nginx_conf_path}")
    logger.info(f"  - target_path: {target_path}")

    try:
        content = await config_service.read_config_file(target_path)
        logger.info(f"[DEBUG] Successfully read file: {target_path}")
        return {"content": content, "file_path": target_path}
    except Exception as e:
        logger.error(f"[DEBUG] Failed to read file {target_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{server_id}/config/files/{file_path:path}")
async def save_config_file(
    server_id: int,
    file_path: str,
    file_data: ConfigFileContent,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save configuration file"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    config_service = ConfigService(server_to_dict(server))
    decoded_path = urllib.parse.unquote(file_path)
    
    # Determine if this is an absolute path or relative path
    if decoded_path.startswith('/'):
        target_path = decoded_path
    else:
        target_path = f"{server.nginx_conf_path}/{decoded_path}"

    # Create backup if requested
    if file_data.auto_backup:
        await config_service.create_backup(target_path)

    success = await config_service.write_config_file(target_path, file_data.content)
    
    if success:
        return {"message": "File saved successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )


@router.post("/{server_id}/config/test")
async def test_nginx_config(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test NGINX configuration"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    test_result = await nginx_service.test_config()
    return test_result


# ==================== Log API ====================

@router.get("/{server_id}/logs")
async def get_log_files(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get log files list"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    log_service = LogService(server_to_dict(server))
    files = await log_service.list_log_files()
    return files


@router.get("/{server_id}/logs/{log_path:path}")
async def get_log_content(
    server_id: int,
    log_path: str,
    lines: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get log file content"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    log_service = LogService(server_to_dict(server))
    decoded_path = urllib.parse.unquote(log_path)
    if decoded_path.startswith('/'):
        target_path = decoded_path
    else:
        target_path = f"{server.nginx_log_path}/{decoded_path}"
    
    log_data = await log_service.read_log_file(target_path, lines)
    return log_data


# ==================== NGINX Control API ====================

@router.get("/{server_id}/nginx/status")
async def get_nginx_status(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get NGINX status"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    status_data = await nginx_service.get_status()
    return status_data


@router.post("/{server_id}/nginx/reload")
async def reload_nginx(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reload NGINX"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    result = await nginx_service.reload()
    return result


@router.post("/{server_id}/nginx/restart")
async def restart_nginx(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Restart NGINX"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    result = await nginx_service.restart()
    return result


@router.post("/{server_id}/nginx/start")
async def start_nginx(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start NGINX"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    result = await nginx_service.start()
    return result


@router.post("/{server_id}/nginx/stop")
async def stop_nginx(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop NGINX"""
    result = await db.execute(
        select(Server).where(
            Server.id == server_id,
            Server.user_id == current_user.id
        )
    )
    server = result.scalar_one_or_none()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    nginx_service = NginxService(server_to_dict(server))
    result = await nginx_service.stop()
    return result
