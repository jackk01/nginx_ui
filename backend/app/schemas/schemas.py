from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ==================== User Schemas ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Server Schemas ====================

class ServerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    host: str = Field(..., max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    username: Optional[str] = None
    nginx_path: str = "/usr/sbin/nginx"
    nginx_conf_path: str = "/etc/nginx"
    nginx_log_path: str = "/var/log/nginx"
    mode: str = "local"  # "local" or "remote"


class ServerCreate(ServerBase):
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None


class ServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    host: Optional[str] = Field(None, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    nginx_path: Optional[str] = None
    nginx_conf_path: Optional[str] = None
    nginx_log_path: Optional[str] = None
    mode: Optional[str] = None


class ServerResponse(ServerBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServerConnectionTest(BaseModel):
    success: bool
    message: str


# ==================== Config File Schemas ====================

class ConfigFileBase(BaseModel):
    file_path: str
    file_name: str
    is_directory: bool = False
    parent_path: Optional[str] = None


class ConfigFileResponse(ConfigFileBase):
    id: int
    server_id: int
    content: Optional[str] = None
    last_modified: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfigFileContent(BaseModel):
    """Schema for reading/writing config file content"""
    content: str
    auto_backup: bool = True


class ConfigFileTree(BaseModel):
    """Schema for file tree structure"""
    file_path: str
    file_name: str
    is_directory: bool
    children: Optional[List["ConfigFileTree"]] = None


# ==================== Config Backup Schemas ====================

class ConfigBackupBase(BaseModel):
    comment: Optional[str] = None


class ConfigBackupCreate(ConfigBackupBase):
    pass


class ConfigBackupResponse(ConfigBackupBase):
    id: int
    config_file_id: int
    version: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== NGINX Status Schemas ====================

class NginxStatus(BaseModel):
    """NGINX running status"""
    running: bool
    pid: Optional[int] = None
    version: Optional[str] = None
    config_test: Optional[dict] = None


class NginxActionResponse(BaseModel):
    """Response for NGINX control actions"""
    success: bool
    message: str
    output: Optional[str] = None


# ==================== Log Schemas ====================

class LogFileBase(BaseModel):
    file_path: str
    file_name: str
    size: int = 0
    modified_time: Optional[datetime] = None


class LogFileResponse(LogFileBase):
    pass


class LogContent(BaseModel):
    """Log file content"""
    content: str
    total_lines: int
    file_path: str


class LogTailRequest(BaseModel):
    """Request for tail log"""
    lines: int = Field(default=100, ge=1, le=1000)
    keyword: Optional[str] = None


# ==================== Auth Schemas ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Update forward ref for ConfigFileTree
ConfigFileTree.model_rebuild()