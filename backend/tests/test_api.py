"""
API endpoint tests
"""
import pytest


@pytest.mark.asyncio
class TestAuthAPI:
    """Test authentication API endpoints"""
    
    async def test_login_success(self, test_client, test_user):
        """Test successful login"""
        response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"
    
    async def test_login_failure_wrong_password(self, test_client, test_user):
        """Test login with wrong password"""
        response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    async def test_login_failure_nonexistent_user(self, test_client):
        """Test login with non-existent user"""
        response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "password"
            }
        )
        
        assert response.status_code == 401
    
    async def test_register_success(self, test_client):
        """Test user registration"""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
    
    async def test_register_duplicate_username(self, test_client, test_user):
        """Test registration with duplicate username"""
        response = await test_client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]
    
    async def test_get_current_user(self, test_client, test_user):
        """Test get current user endpoint"""
        # Login first
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = await test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    async def test_get_current_user_unauthorized(self, test_client):
        """Test get current user without token"""
        response = await test_client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    async def test_logout(self, test_client, test_user):
        """Test logout endpoint"""
        # Login first
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Logout
        response = await test_client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert "Successfully logged out" in response.json()["message"]


@pytest.mark.asyncio
class TestServerAPI:
    """Test server management API endpoints"""
    
    async def test_list_servers_empty(self, test_client, test_user):
        """Test listing servers when none exist"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # List servers
        response = await test_client.get(
            "/api/servers",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    async def test_create_server(self, test_client, test_user):
        """Test creating a new server"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Create server
        response = await test_client.post(
            "/api/servers",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "My Server",
                "host": "192.168.1.100",
                "port": 22,
                "username": "nginx",
                "password": "password123",
                "nginx_path": "/usr/sbin/nginx",
                "nginx_conf_path": "/etc/nginx",
                "nginx_log_path": "/var/log/nginx",
                "mode": "remote"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Server"
        assert data["host"] == "192.168.1.100"
        assert data["mode"] == "remote"
    
    async def test_list_servers_with_data(self, test_client, test_user, test_server):
        """Test listing servers when some exist"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # List servers
        response = await test_client.get(
            "/api/servers",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Test Server"
    
    async def test_get_server_detail(self, test_client, test_user, test_server):
        """Test getting server details"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get server detail
        response = await test_client.get(
            f"/api/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Server"
        assert data["host"] == "localhost"
    
    async def test_update_server(self, test_client, test_user, test_server):
        """Test updating a server"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Update server
        response = await test_client.put(
            f"/api/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Updated Server",
                "host": "192.168.1.1",
                "port": 2222,
                "mode": "remote"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Server"
        assert data["host"] == "192.168.1.1"
    
    async def test_delete_server(self, test_client, test_user, test_server):
        """Test deleting a server"""
        # Login
        login_response = await test_client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Delete server
        response = await test_client.delete(
            f"/api/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        
        # Verify server is deleted
        get_response = await test_client.get(
            f"/api/servers/{test_server.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 404


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test root endpoints"""
    
    async def test_root_endpoint(self, test_client):
        """Test root endpoint returns app info"""
        response = await test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "NGINX UI"
    
    async def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = await test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"