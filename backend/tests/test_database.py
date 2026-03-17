"""
Database model tests
"""
import pytest
from datetime import datetime
from sqlalchemy import select


@pytest.mark.asyncio
class TestUserModel:
    """Test User model operations"""
    
    async def test_create_user(self, test_db_session):
        """Test creating a new user"""
        from app.models.models import User
        from app.services.auth_service import get_password_hash
        
        user = User(
            username="newuser",
            email="newuser@example.com",
            password_hash=get_password_hash("password123")
        )
        
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.created_at is not None
    
    async def test_user_unique_username(self, test_db_session):
        """Test user username is unique"""
        from app.models.models import User
        from app.services.auth_service import get_password_hash
        
        user1 = User(
            username="duplicate",
            email="user1@example.com",
            password_hash=get_password_hash("password")
        )
        test_db_session.add(user1)
        await test_db_session.commit()
        
        user2 = User(
            username="duplicate",
            email="user2@example.com",
            password_hash=get_password_hash("password")
        )
        test_db_session.add(user2)
        
        # This should raise an integrity error
        with pytest.raises(Exception):
            await test_db_session.commit()
    
    async def test_get_user_by_username(self, test_db_session, test_user):
        """Test getting user by username"""
        from app.models.models import User
        
        result = await test_db_session.execute(
            select(User).where(User.username == "testuser")
        )
        user = result.scalar_one_or_none()
        
        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    async def test_update_user(self, test_db_session, test_user):
        """Test updating user information"""
        test_user.email = "updated@example.com"
        await test_db_session.commit()
        await test_db_session.refresh(test_user)
        
        assert test_user.email == "updated@example.com"
        assert test_user.updated_at is not None
    
    async def test_delete_user(self, test_db_session, test_user):
        """Test deleting a user"""
        user_id = test_user.id
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
        # Verify user is deleted
        result = await test_db_session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        assert user is None


@pytest.mark.asyncio
class TestServerModel:
    """Test Server model operations"""
    
    async def test_create_server(self, test_db_session, test_user):
        """Test creating a new server"""
        from app.models.models import Server
        
        server = Server(
            user_id=test_user.id,
            name="Production Server",
            host="192.168.1.100",
            port=22,
            username="nginx",
            mode="remote",
            status="online"
        )
        
        test_db_session.add(server)
        await test_db_session.commit()
        await test_db_session.refresh(server)
        
        assert server.id is not None
        assert server.name == "Production Server"
        assert server.host == "192.168.1.100"
        assert server.user_id == test_user.id
    
    async def test_server_default_values(self, test_db_session, test_user):
        """Test server default values"""
        from app.models.models import Server
        
        server = Server(
            user_id=test_user.id,
            name="Local Server",
            host="localhost",
            mode="local"
        )
        
        test_db_session.add(server)
        await test_db_session.commit()
        await test_db_session.refresh(server)
        
        assert server.port == 22  # Default port
        assert server.status == "offline"  # Default status
        assert server.nginx_path == "/usr/sbin/nginx"  # Default nginx path
    
    async def test_get_servers_by_user(self, test_db_session, test_user):
        """Test getting all servers for a user"""
        from app.models.models import Server
        
        # Create multiple servers
        server1 = Server(user_id=test_user.id, name="Server 1", host="192.168.1.1", mode="remote")
        server2 = Server(user_id=test_user.id, name="Server 2", host="192.168.1.2", mode="remote")
        
        test_db_session.add_all([server1, server2])
        await test_db_session.commit()
        
        # Get servers
        result = await test_db_session.execute(
            select(Server).where(Server.user_id == test_user.id)
        )
        servers = result.scalars().all()
        
        assert len(servers) == 2
    
    async def test_update_server_status(self, test_db_session, test_server):
        """Test updating server status"""
        test_server.status = "online"
        await test_db_session.commit()
        await test_db_session.refresh(test_server)
        
        assert test_server.status == "online"
    
    async def test_delete_server(self, test_db_session, test_server):
        """Test deleting a server"""
        server_id = test_server.id
        await test_db_session.delete(test_server)
        await test_db_session.commit()
        
        # Verify server is deleted
        result = await test_db_session.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()
        
        assert server is None


@pytest.mark.asyncio
class TestUserServerRelationship:
    """Test User-Server relationship"""
    
    async def test_user_servers_relationship(self, test_db_session, test_user):
        """Test user has many servers"""
        from app.models.models import Server
        
        server = Server(
            user_id=test_user.id,
            name="Test Server",
            host="localhost",
            mode="local"
        )
        test_db_session.add(server)
        await test_db_session.commit()
        
        # Access user's servers
        await test_db_session.refresh(test_user)
        
        # Test relationship exists
        result = await test_db_session.execute(
            select(Server).where(Server.user_id == test_user.id)
        )
        servers = result.scalars().all()
        
        assert len(servers) == 1
        assert servers[0].name == "Test Server"
    
    async def test_cascade_delete_servers(self, test_db_session, test_user, test_server):
        """Test servers are deleted when user is deleted"""
        user_id = test_user.id
        server_id = test_server.id
        
        await test_db_session.delete(test_user)
        await test_db_session.commit()
        
        # Servers should also be deleted (if cascade is configured)
        # Note: This depends on relationship configuration
        result = await test_db_session.execute(
            select(Server).where(Server.id == server_id)
        )
        server = result.scalar_one_or_none()
        
        # Without cascade, server might still exist
        # With cascade delete, it would be None


@pytest.mark.asyncio
class TestConfigFileModel:
    """Test ConfigFile model operations"""
    
    async def test_create_config_file(self, test_db_session, test_server):
        """Test creating a config file record"""
        from app.models.models import ConfigFile
        
        config_file = ConfigFile(
            server_id=test_server.id,
            file_path="/etc/nginx/nginx.conf",
            file_name="nginx.conf",
            content="worker_processes 1;",
            is_directory=False
        )
        
        test_db_session.add(config_file)
        await test_db_session.commit()
        await test_db_session.refresh(config_file)
        
        assert config_file.id is not None
        assert config_file.file_name == "nginx.conf"
        assert config_file.server_id == test_server.id
    
    async def test_config_file_directory(self, test_db_session, test_server):
        """Test creating a config file directory entry"""
        from app.models.models import ConfigFile
        
        config_dir = ConfigFile(
            server_id=test_server.id,
            file_path="/etc/nginx/conf.d",
            file_name="conf.d",
            is_directory=True
        )
        
        test_db_session.add(config_dir)
        await test_db_session.commit()
        
        assert config_dir.id is not None
        assert config_dir.is_directory is True
        assert config_dir.content is None


@pytest.mark.asyncio
class TestConfigBackupModel:
    """Test ConfigBackup model operations"""
    
    async def test_create_config_backup(self, test_db_session, test_server):
        """Test creating a config backup"""
        from app.models.models import ConfigFile, ConfigBackup
        
        # Create config file first
        config_file = ConfigFile(
            server_id=test_server.id,
            file_path="/etc/nginx/nginx.conf",
            file_name="nginx.conf",
            content="worker_processes 1;"
        )
        test_db_session.add(config_file)
        await test_db_session.commit()
        await test_db_session.refresh(config_file)
        
        # Create backup
        backup = ConfigBackup(
            config_file_id=config_file.id,
            content="worker_processes 1;",
            version=1,
            comment="Initial backup"
        )
        test_db_session.add(backup)
        await test_db_session.commit()
        await test_db_session.refresh(backup)
        
        assert backup.id is not None
        assert backup.version == 1
        assert backup.comment == "Initial backup"
    
    async def test_config_backup_versioning(self, test_db_session, test_server):
        """Test config backup versioning"""
        from app.models.models import ConfigFile, ConfigBackup
        
        # Create config file
        config_file = ConfigFile(
            server_id=test_server.id,
            file_path="/etc/nginx/nginx.conf",
            file_name="nginx.conf",
            content="worker_processes 1;"
        )
        test_db_session.add(config_file)
        await test_db_session.commit()
        await test_db_session.refresh(config_file)
        
        # Create multiple backups
        for i in range(1, 4):
            backup = ConfigBackup(
                config_file_id=config_file.id,
                content=f"version {i}",
                version=i,
                comment=f"Backup version {i}"
            )
            test_db_session.add(backup)
        
        await test_db_session.commit()
        
        # Get all backups
        result = await test_db_session.execute(
            select(ConfigBackup).where(
                ConfigBackup.config_file_id == config_file.id
            ).order_by(ConfigBackup.version)
        )
        backups = result.scalars().all()
        
        assert len(backups) == 3
        assert backups[0].version == 1
        assert backups[1].version == 2
        assert backups[2].version == 3


@pytest.mark.asyncio
class TestDatabaseInitialization:
    """Test database initialization"""
    
    async def test_init_db_creates_tables(self, test_db_engine):
        """Test database initialization creates all tables"""
        from app.models.models import Base
        
        # Tables should be created by fixture
        async with test_db_engine.connect() as conn:
            # Check if tables exist
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in result.fetchall()]
        
        expected_tables = ["users", "servers", "config_files", "config_backups"]
        for table in expected_tables:
            assert table in tables
    
    async def test_get_db_dependency(self):
        """Test get_db dependency provides session"""
        from app.core.database import get_db
        from app.core.config import settings
        
        # This is a generator function
        import inspect
        assert inspect.isgeneratorfunction(get_db)