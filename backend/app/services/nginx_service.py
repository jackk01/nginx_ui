import os
import subprocess
from typing import Optional, Tuple
from datetime import datetime
from app.services.ssh_service import get_client, LocalClient


class NginxService:
    """NGINX management service"""
    
    def __init__(self, server_config: dict):
        self.host = server_config.get("host", "localhost")
        self.port = server_config.get("port", 22)
        self.username = server_config.get("username")
        self.password = server_config.get("password")
        self.key_path = server_config.get("ssh_key_path")
        self.nginx_path = server_config.get("nginx_path", "/usr/sbin/nginx")
        self.nginx_conf_path = server_config.get("nginx_conf_path", "/etc/nginx")
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
    
    async def get_status(self) -> dict:
        """Get NGINX status"""
        client = self._get_client()
        
        # Check if nginx is running
        if isinstance(client, LocalClient):
            result = subprocess.run(
                ["pgrep", "-x", "nginx"],
                capture_output=True,
                text=True
            )
            running = result.returncode == 0
            pid = int(result.stdout.strip().split('\n')[0]) if running else None
        else:
            exit_code, stdout, _ = await client.execute_command("pgrep -x nginx")
            running = exit_code == 0
            pid = int(stdout.strip()) if running else None
        
        # Get version
        version = await self.get_version()
        
        return {
            "running": running,
            "pid": pid,
            "version": version
        }
    
    async def get_version(self) -> Optional[str]:
        """Get NGINX version"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    [self.nginx_path, "-v"],
                    capture_output=True,
                    text=True,
                    stderr=subprocess.STDOUT
                )
                version_output = result.stderr
            else:
                exit_code, stdout, stderr = await client.execute_command(f"{self.nginx_path} -v")
                version_output = stderr or stdout
            
            # Parse version from output like "nginx version: nginx/1.24.0"
            if "nginx/" in version_output:
                return version_output.split("nginx/")[-1].strip()
            return "unknown"
        except Exception:
            return None
    
    async def test_config(self) -> dict:
        """Test NGINX configuration"""
        client = self._get_client()
        
        test_command = f"{self.nginx_path} -t"
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    test_command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr
            else:
                exit_code, stdout, stderr = await client.execute_command(test_command)
                success = exit_code == 0
                output = stdout + stderr
            
            return {
                "success": success,
                "output": output.strip()
            }
        except Exception as e:
            return {
                "success": False,
                "output": str(e)
            }
    
    async def reload(self) -> dict:
        """Reload NGINX configuration"""
        client = self._get_client()
        
        # First test config
        test_result = await self.test_config()
        if not test_result["success"]:
            return {
                "success": False,
                "message": "Configuration test failed",
                "output": test_result["output"]
            }
        
        # Reload nginx
        reload_command = f"{self.nginx_path} -s reload"
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    reload_command,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr
            else:
                exit_code, stdout, stderr = await client.execute_command(reload_command)
                success = exit_code == 0
                output = stdout + stderr
            
            if success:
                return {
                    "success": True,
                    "message": "NGINX reloaded successfully",
                    "output": output.strip()
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to reload NGINX",
                    "output": output.strip()
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "output": ""
            }
    
    async def restart(self) -> dict:
        """Restart NGINX service"""
        client = self._get_client()
        
        # Try different restart methods
        restart_commands = [
            f"{self.nginx_path} -s stop && {self.nginx_path}",
            "systemctl restart nginx",
            "service nginx restart",
            f"pkill -9 nginx && {self.nginx_path}"
        ]
        
        for restart_command in restart_commands:
            try:
                if isinstance(client, LocalClient):
                    # Use systemctl for local
                    result = subprocess.run(
                        "systemctl restart nginx",
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    success = result.returncode == 0
                else:
                    exit_code, stdout, stderr = await client.execute_command(restart_command)
                    success = exit_code == 0
                
                if success:
                    return {
                        "success": True,
                        "message": "NGINX restarted successfully",
                        "output": ""
                    }
            except Exception:
                continue
        
        return {
            "success": False,
            "message": "Failed to restart NGINX",
            "output": ""
        }
    
    async def start(self) -> dict:
        """Start NGINX"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    "systemctl start nginx",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0
            else:
                exit_code, stdout, stderr = await client.execute_command(f"{self.nginx_path}")
                success = exit_code == 0
            
            if success:
                return {
                    "success": True,
                    "message": "NGINX started successfully",
                    "output": ""
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to start NGINX",
                    "output": ""
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "output": ""
            }
    
    async def stop(self) -> dict:
        """Stop NGINX"""
        client = self._get_client()
        
        try:
            if isinstance(client, LocalClient):
                result = subprocess.run(
                    "systemctl stop nginx",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                success = result.returncode == 0
            else:
                exit_code, stdout, stderr = await client.execute_command(f"{self.nginx_path} -s stop")
                success = exit_code == 0
            
            if success:
                return {
                    "success": True,
                    "message": "NGINX stopped successfully",
                    "output": ""
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to stop NGINX",
                    "output": ""
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "output": ""
            }