"""Application configuration settings."""
from dataclasses import dataclass
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str
    port: int
    user: str
    password: str
    domain: str
    tls: str
    url: str = ""

    def __post_init__(self):
        self.url = f"{self.domain}://{self.user}:{self.password}@{self.host}:{self.port}" if \
            self.user and self.password else \
            f"{self.domain}://{self.host}:{self.port}"


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Core Application
        self.env: str = self._get_env_var("ENV")

        # Database
        self.database_url: str = self._get_env_var("DATABASE_URL")

        # Authentication
        self.jwt_secret_key: str = self._get_env_var(
            "JWT_SECRET_KEY")

        # CORS
        self.cors_origin: str = self._get_env_var("CORS_ORIGIN")

        if self.env == "prod":
            self.redis_config = RedisConfig(
                host=self._get_env_var("REDIS_HOST"),
                port=int(self._get_env_var("REDIS_PORT")),
                user=self._get_env_var("REDIS_USER"),
                password=self._get_env_var("REDIS_PASSWORD"),
                domain=self._get_env_var("REDIS_DOMAIN"),
                tls=self._get_env_var("REDIS_TLS"),
            )
        elif self.env == "docker":
            self.redis_config = RedisConfig(
                host=self._get_env_var("REDIS_HOST"),
                port=int(self._get_env_var("REDIS_PORT")),
                user="",
                password="",
                domain=self._get_env_var("REDIS_DOMAIN"),
                tls=self._get_env_var("REDIS_TLS"),
            )

    def _get_env_var(self, key: str) -> str:
        """Get an environment variable with a default value."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} environment variable is required")
        return value


# Global settings instance
settings = Settings()
