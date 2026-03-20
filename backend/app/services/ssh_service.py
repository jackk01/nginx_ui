import asyncssh
from typing import Optional, Tuple
from pathlib import Path


class SSHClient:
    """SSH Client for remote NGINX management"""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        key_path: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_path = key_path
        self._client: Optional[asyncssh.SSHClientConnection] = None
    
    async def connect(self) -> bool:
        """Establish SSH connection"""
        if self._client is not None:
            return True

        try:
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "known_hosts": None,  # Disable host key checking for simplicity
            }

            if self.key_path:
                connect_kwargs["client_keys"] = [str(Path(self.key_path).expanduser())]

            if self.password:
                connect_kwargs["password"] = self.password

            self._client = await asyncssh.connect(**connect_kwargs)
            return True
        except Exception as e:
            self._client = None
            print(f"SSH connection failed: {e}")
            return False
    
    async def close(self):
        """Close SSH connection"""
        if self._client:
            self._client.close()
            await self._client.wait_closed()
            self._client = None

    async def _ensure_connected(self):
        """Ensure an active SSH connection exists before remote operations."""
        if self._client is None:
            success = await self.connect()
            if not success:
                raise RuntimeError(
                    f"Failed to connect to SSH server {self.username}@{self.host}:{self.port}"
                )
    
    async def execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute command on remote server"""
        await self._ensure_connected()
        result = await self._client.run(command)
        return result.exit_status, result.stdout, result.stderr
    
    async def read_file(self, file_path: str) -> str:
        """Read file content from remote server"""
        await self._ensure_connected()
        async with self._client.start_sftp_client() as sftp:
            async with sftp.open(file_path, 'r') as f:
                return await f.read()
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to file on remote server"""
        await self._ensure_connected()
        try:
            async with self._client.start_sftp_client() as sftp:
                async with sftp.open(file_path, 'w') as f:
                    await f.write(content)
            return True
        except Exception as e:
            print(f"Failed to write file: {e}")
            return False
    
    async def list_directory(self, dir_path: str) -> list:
        """List directory contents"""
        await self._ensure_connected()
        result = await self._client.run(f"ls -la {dir_path}")
        if result.exit_status != 0:
            return []
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line or line.startswith('total'):
                continue
            
            parts = line.split()
            if len(parts) >= 9:
                is_dir = parts[0].startswith('d')
                filename = ' '.join(parts[8:])
                files.append({
                    'name': filename,
                    'is_dir': is_dir,
                    'path': f"{dir_path.rstrip('/')}/{filename}"
                })
        
        return files
    
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists"""
        await self._ensure_connected()
        result = await self._client.run(f"test -e {file_path} && echo 'exists' || echo 'not_exists'")
        return 'exists' in result.stdout


class LocalClient:
    """Local file system client for local NGINX management"""
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """Read local file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {e}")
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """Write content to local file"""
        try:
            # Create parent directories if not exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Failed to write file: {e}")
            return False
    
    @staticmethod
    def execute_command(command: str) -> Tuple[int, str, str]:
        """Execute local command"""
        import subprocess
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    
    @staticmethod
    def list_directory(dir_path: str) -> list:
        """List local directory"""
        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                return []
            
            files = []
            for item in path.iterdir():
                files.append({
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'path': str(item)
                })
            return files
        except Exception as e:
            print(f"Failed to list directory: {e}")
            return []
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """Check if local file exists"""
        return Path(file_path).exists()


def get_client(
    host: str,
    port: int,
    username: str,
    mode: str,
    password: Optional[str] = None,
    key_path: Optional[str] = None
):
    """Get appropriate client based on mode"""
    if mode == "local" or host in ["localhost", "127.0.0.1", ""]:
        return LocalClient()
    else:
        return SSHClient(host, port, username, password, key_path)
