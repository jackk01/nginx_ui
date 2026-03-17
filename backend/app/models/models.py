from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    servers = relationship("Server", back_populates="user")


class Server(Base):
    """NGINX Server model"""
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=22)
    username = Column(String(100))
    password = Column(String(255))  # Encrypted
    ssh_key_path = Column(String(500))
    nginx_path = Column(String(500), default="/usr/sbin/nginx")
    nginx_conf_path = Column(String(500), default="/etc/nginx")
    nginx_log_path = Column(String(500), default="/var/log/nginx")
    mode = Column(String(20), default="local")  # "local" or "remote"
    status = Column(String(20), default="offline")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="servers")
    config_files = relationship("ConfigFile", back_populates="server")


class ConfigFile(Base):
    """NGINX Configuration File model"""
    __tablename__ = "config_files"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content = Column(Text)
    is_directory = Column(Boolean, default=False)
    parent_path = Column(String(500))
    last_modified = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    server = relationship("Server", back_populates="config_files")
    backups = relationship("ConfigBackup", back_populates="config_file")


class ConfigBackup(Base):
    """Configuration Backup model"""
    __tablename__ = "config_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    config_file_id = Column(Integer, ForeignKey("config_files.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    comment = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    config_file = relationship("ConfigFile", back_populates="backups")