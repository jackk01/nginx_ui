"""
Pytest configuration and fixtures for NGINX UI tests
"""
import pytest
import asyncio
import os
import tempfile
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

# Fix for missing _sqlite3 module
try:
    import sqlite3
except ModuleNotFoundError:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3

# Set test database path before importing app
TEST_DB_PATH = tempfile.mktemp(suffix=".db")

# Import app modules after setting up test environment
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db_engine():
    """Create test database engine"""
    # Override the database URL for testing
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
    os.environ["DEBUG"] = "true"
    
    from app.core.config import settings
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
    
    yield engine
    
    # Cleanup
    await engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    from app.models.models import Base
    
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    # Create all tables
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    # Drop all tables
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_client(test_db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    from app.main import app
    from app.core.database import get_db
    
    # Override database dependency
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data() -> dict:
    """Test user data"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_admin_user_data() -> dict:
    """Test admin user data"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123"
    }


@pytest.fixture
async def test_user(test_db_session) -> "User":
    """Create test user in database"""
    from app.models.models import User
    from app.services.auth_service import get_password_hash
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=get_password_hash("testpassword123")
    )
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_server(test_db_session, test_user) -> "Server":
    """Create test server in database"""
    from app.models.models import Server
    
    server = Server(
        user_id=test_user.id,
        name="Test Server",
        host="localhost",
        port=22,
        username="test",
        mode="local",
        status="offline"
    )
    test_db_session.add(server)
    await test_db_session.commit()
    await test_db_session.refresh(server)
    return server


@pytest.fixture
def auth_token(test_user) -> str:
    """Generate authentication token for test user"""
    from app.services.auth_service import create_access_token
    from datetime import timedelta
    
    return create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )