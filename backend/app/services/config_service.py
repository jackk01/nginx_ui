import os
import subprocess
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
from app.services.ssh_service import get_client, LocalClient


class ConfigService:
    """Configuration file management service"""
    
    def __init__(self, server_config: dict):
        self.host = server_config.get("host", "localhost")
        self.port = server_config.get("port", 22)
        self.username = server_config.get("username")
        self.password = server_config.get("password")
        self.key_path = server_config.get("ssh_key_path")
        self.nginx_conf_path = server_config.get("nginx_conf_path", "/etc/nginx")
        self.mode = server_config.get("mode", "local")
        self._client = None
    
    def _get_client(self):
        """Get the appropriate client"""
        if self._client is None:
            self._client = get_client(
                self.host,
                self.port,
                self.username or "",
                self.mode,
                self.password,
                self.key_path
            )
        return self._client
    
    async def list_config_files(self, path: Optional[str] = None) -> List[Dict]:
        """List configuration files in directory"""
        client = self._get_client()
        
        target_path = path or self.nginx_conf_path
        
        try:
            if isinstance(client, LocalClient):
                files = self._list_local_directory(target_path)
            else:
                files = await client.list_directory(target_path)
            
            # Filter to only include nginx config files
            config_extensions = ['.conf', '']
            config_files = []
            
            for f in files:
                name = f['name']
                # Skip hidden files and parent directory
                if name.startswith('.'):
                    continue
                
                # Include .conf files and directories
                is_config = any(name.endswith(ext) for ext in config_extensions) or f['is_dir']
                if is_config:
                    config_files.append({
                        'file_path': f['path'],
                        'file_name': name,
                        'is_directory': f['is_dir']
                    })
            
            # Sort: directories first, then files
            config_files.sort(key=lambda x: (not x['is_directory'], x['file_name'].lower()))
            
            return config_files
        except Exception as e:
            print(f"Error listing config files: {e}")
            return []
    
    def _list_local_directory(self, dir_path: str) -> List[Dict]:
        """List local directory"""
        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                return []
            
            files = []
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue
                files.append({
                    'name': item.name,
                    'is_dir': item.is_dir(),
                    'path': str(item)
                })
            return files
        except Exception:
            return []
    
    async def read_config_file(self, file_path: str) -> str:
        """Read configuration file content"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                return client.read_file(file_path)
            else:
                return await client.read_file(file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read config file: {e}")
    
    async def write_config_file(self, file_path: str, content: str) -> bool:
        """Write configuration file content"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                return client.write_file(file_path, content)
            else:
                return await client.write_file(file_path, content)
        except Exception as e:
            print(f"Failed to write config file: {e}")
            return False
    
    async def create_backup(self, file_path: str, comment: Optional[str] = None) -> Dict:
        """Create a backup of configuration file"""
        try:
            content = await self.read_config_file(file_path)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(self.nginx_conf_path) / ".backups"
            
            # For local mode, save backup locally
            if isinstance(self._get_client(), LocalClient):
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_file = backup_dir / f"{Path(file_path).name}.{timestamp}.bak"
                backup_file.write_text(content, encoding='utf-8')
                
                return {
                    "success": True,
                    "backup_path": str(backup_file),
                    "version": timestamp
                }
            else:
                # For remote mode, store in database (handled by API)
                return {
                    "success": True,
                    "content": content,
                    "version": timestamp,
                    "comment": comment
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_backups(self, file_path: str) -> List[Dict]:
        """List backups for a configuration file"""
        client = self._get_client()
        
        try:
            backup_dir = Path(self.nginx_conf_path) / ".backups"
            config_name = Path(file_path).name
            
            if isinstance(client, LocalClient):
                if not backup_dir.exists():
                    return []
                
                backups = []
                for f in backup_dir.glob(f"{config_name}.*.bak"):
                    backups.append({
                        "file_path": str(f),
                        "file_name": f.name,
                        "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                    })
                
                return sorted(backups, key=lambda x: x['created_at'], reverse=True)
            else:
                return []
        except Exception:
            return []
    
    async def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup file"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                backup_content = client.read_file(backup_path)
                original_path = str(Path(backup_path).name).rsplit('.', 2)[0]
                return client.write_file(original_path, backup_content)
            else:
                return False
        except Exception:
            return False


class LogService:
    """Log file management service"""
    
    def __init__(self, server_config: dict):
        self.host = server_config.get("host", "localhost")
        self.port = server_config.get("port", 22)
        self.username = server_config.get("username")
        self.password = server_config.get("password")
        self.key_path = server_config.get("ssh_key_path")
        self.nginx_log_path = server_config.get("nginx_log_path", "/var/log/nginx")
        self.mode = server_config.get("mode", "local")
        self._client = None
    
    def _get_client(self):
        """Get the appropriate client"""
        if self._client is None:
            self._client = get_client(
                self.host,
                self.port,
                self.username or "",
                self.mode,
                self.password,
                self.key_path
            )
        return self._client
    
    async def list_log_files(self) -> List[Dict]:
        """List log files"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                return self._list_local_directory(self.nginx_log_path)
            else:
                return await client.list_directory(self.nginx_log_path)
        except Exception:
            return []
    
    def _list_local_directory(self, dir_path: str) -> List[Dict]:
        """List local directory"""
        try:
            path = Path(dir_path)
            if not path.exists() or not path.is_dir():
                return []
            
            files = []
            for item in path.iterdir():
                if item.name.startswith('.'):
                    continue
                if item.is_file() and (item.suffix == '.log' or item.name in ['access.log', 'error.log']):
                    stat = item.stat()
                    files.append({
                        'file_path': str(item),
                        'file_name': item.name,
                        'size': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            return files
        except Exception:
            return []
    
    async def read_log_file(self, file_path: str, lines: int = 100, offset: int = 0) -> Dict:
        """Read log file content (last N lines)"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                # Use tail command for efficiency
                result = subprocess.run(
                    f"tail -n {lines} {file_path} 2>/dev/null | wc -l",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                total_lines = int(result.stdout.strip()) if result.returncode == 0 else 0
                
                result = subprocess.run(
                    f"tail -n {lines} {file_path}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                content = result.stdout if result.returncode == 0 else ""
                
                return {
                    "content": content,
                    "total_lines": total_lines,
                    "file_path": file_path
                }
            else:
                # For remote, use tail command
                exit_code, stdout, stderr = await client.execute_command(
                    f"tail -n {lines} {file_path}"
                )
                content = stdout if exit_code == 0 else ""
                
                # Get total line count
                exit_code, stdout, _ = await client.execute_command(f"wc -l {file_path}")
                total_lines = int(stdout.strip().split()[0]) if exit_code == 0 else 0
                
                return {
                    "content": content,
                    "total_lines": total_lines,
                    "file_path": file_path
                }
        except Exception as e:
            return {
                "content": f"Error reading log: {e}",
                "total_lines": 0,
                "file_path": file_path
            }
    
    async def tail_log(self, file_path: str, lines: int = 50) -> str:
        """Tail log file - get latest lines"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    f"tail -n {lines} {file_path}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.stdout if result.returncode == 0 else ""
            else:
                exit_code, stdout, _ = await client.execute_command(
                    f"tail -n {lines} {file_path}"
                )
                return stdout if exit_code == 0 else ""
        except Exception:
            return ""