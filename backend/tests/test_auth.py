"""
Authentication service tests
"""
import pytest
from datetime import timedelta
from jose import jwt


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_password_hash_generation(self):
        """Test password hash is generated correctly"""
        from app.services.auth_service import get_password_hash
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_password_hash_unique(self):
        """Test that same password generates different hashes (salting)"""
        from app.services.auth_service import get_password_hash
        
        password = "testpassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Bcrypt adds salt, so hashes should be different
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from app.services.auth_service import get_password_hash, verify_password
        
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from app.services.auth_service import get_password_hash, verify_password
        
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestAccessToken:
    """Test JWT token functions"""
    
    def test_create_access_token(self):
        """Test JWT token creation"""
        from app.services.auth_service import create_access_token
        from app.core.config import settings
        
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry"""
        from app.services.auth_service import create_access_token
        
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert token is not None
        
        # Decode and verify expiry
        from app.core.config import settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "testuser"
        assert "exp" in payload
    
    def test_decode_access_token(self):
        """Test JWT token decoding"""
        from app.services.auth_service import create_access_token
        from app.core.config import settings
        
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == "testuser"
        assert "exp" in payload


@pytest.mark.asyncio
class TestAuthUser:
    """Test authentication with user in database"""
    
    async def test_authenticate_user_success(self, test_db_session, test_user):
        """Test user authentication with correct credentials"""
        from app.services.auth_service import authenticate_user
        
        user = await authenticate_user(
            test_db_session,
            "testuser",
            "testpassword123"
        )
        
        assert user is not None
        assert user.username == "testuser"
    
    async def test_authenticate_user_wrong_password(self, test_db_session, test_user):
        """Test user authentication with wrong password"""
        from app.services.auth_service import authenticate_user
        
        user = await authenticate_user(
            test_db_session,
            "testuser",
            "wrongpassword"
        )
        
        assert user is None
    
    async def test_authenticate_user_nonexistent(self, test_db_session):
        """Test authentication with non-existent user"""
        from app.services.auth_service import authenticate_user
        
        user = await authenticate_user(
            test_db_session,
            "nonexistent",
            "password"
        )
        
        assert user is None


@pytest.mark.asyncio
class TestDefaultAdmin:
    """Test default admin user creation"""
    
    async def test_create_default_admin(self, test_db_session):
        """Test default admin user is created"""
        from app.services.auth_service import create_default_admin
        from app.models.models import User
        from sqlalchemy import select
        
        # Create default admin
        await create_default_admin(test_db_session)
        
        # Check admin exists
        result = await test_db_session.execute(
            select(User).where(User.username == "admin")
        )
        admin = result.scalar_one_or_none()
        
        assert admin is not None
        assert admin.username == "admin"
        assert admin.email == "admin@nginx-ui.local"
    
    async def test_default_admin_not_duplicated(self, test_db_session):
        """Test default admin is not created twice"""
        from app.services.auth_service import create_default_admin
        from app.models.models import User
        from sqlalchemy import select
        
        # Create default admin twice
        await create_default_admin(test_db_session)
        await create_default_admin(test_db_session)
        
        # Check only one admin exists
        result = await test_db_session.execute(
            select(User).where(User.username == "admin")
        )
        admins = result.scalars().all()
        
        assert len(admins) == 1


class TestOAuth2Scheme:
    """Test OAuth2 scheme"""
    
    def test_oauth2_scheme_defined(self):
        """Test OAuth2 scheme is properly defined"""
        from app.services.auth_service import oauth2_scheme
        
        assert oauth2_scheme is not None
        assert oauth2_scheme.model.name == "OAuth2PasswordBearer"