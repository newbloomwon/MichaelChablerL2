import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "Punkt"

    # Database - required, must be set in environment or .env file
    DATABASE_URL: str = Field(
        default="postgresql://punkt:punkt123@localhost:5432/punkt",
        env="DATABASE_URL"
    )

    # Redis - required, must be set in environment or .env file
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )

    # JWT - MUST come from environment variable; no hardcoded fallback in production.
    # Provide JWT_SECRET in your .env file or environment.
    # Resolves I-01: hardcoded JWT secret.
    JWT_SECRET: str = Field(
        default="dev-secret-key-change-in-production",
        env="JWT_SECRET"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # CORS - resolves I-07: supports both React (port 3000) and Vite (port 5173) dev servers.
    # Override via CORS_ORIGINS env var as a JSON array string:
    #   CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",   # React dev server (Create React App)
            "http://localhost:5173",   # Vite dev server
        ],
        env="CORS_ORIGINS"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> List[str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            try:
                result = json.loads(v)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                pass
            # Comma-separated fallback: CORS_ORIGINS=http://a.com,http://b.com
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


settings = Settings()
