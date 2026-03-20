from functools import lru_cache
from pathlib import Path

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SQLITE_PATH = BACKEND_DIR / "data" / "nginx_ui.db"


class Settings(BaseSettings):
    """Application settings"""
    
    # App settings
    APP_NAME: str = "NGINX UI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "nginx-ui-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Default NGINX paths (for local mode)
    DEFAULT_NGINX_PATH: str = "/usr/sbin/nginx"
    DEFAULT_NGINX_CONF_PATH: str = "/etc/nginx"
    DEFAULT_NGINX_LOG_PATH: str = "/var/log/nginx"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_bool(cls, value):
        """Allow common string env values for DEBUG."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            true_values = {"1", "true", "yes", "on", "debug", "dev", "development"}
            false_values = {"0", "false", "no", "off", "release", "prod", "production"}
            if normalized in true_values:
                return True
            if normalized in false_values:
                return False
        return value

    @model_validator(mode="after")
    def normalize_sqlite_url(self):
        """
        Normalize SQLite path so startup works from any working directory,
        and ensure the parent directory exists before connecting.
        """
        prefix = "sqlite+aiosqlite:///"
        if not self.DATABASE_URL.startswith(prefix):
            return self

        db_path_raw = self.DATABASE_URL[len(prefix):]
        if db_path_raw == ":memory:":
            return self

        db_path = Path(db_path_raw)
        if not db_path.is_absolute():
            db_path = BACKEND_DIR / db_path

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.DATABASE_URL = f"{prefix}{db_path.resolve().as_posix()}"
        return self
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
