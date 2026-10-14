from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: SecretStr
    jwt_secret: SecretStr
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    starter_minutes: int = Field(default=120, ge=0, le=10000)
    reputation_half_life_days: float = Field(default=90, gt=0)
    match_weights: dict[str, float] = {
        "skill": 0.40,
        "reputation": 0.25,
        "activity": 0.15,
        "location": 0.10,
        "availability": 0.10,
    }

    @field_validator("jwt_secret")
    @classmethod
    def require_secret(cls, value):
        raw = value.get_secret_value()
        if len(raw) < 32 or raw.startswith("replace-"):
            raise ValueError("JWT_SECRET must be a generated secret of at least 32 characters")
        return value

    @field_validator("database_url")
    @classmethod
    def postgres_only(cls, value):
        if not value.get_secret_value().startswith("postgresql+psycopg://"):
            raise ValueError("Use a postgresql+psycopg database URL")
        return value

    @field_validator("match_weights")
    @classmethod
    def valid_weights(cls, value):
        expected = {"skill", "reputation", "activity", "location", "availability"}
        if (
            set(value) != expected
            or any(v < 0 for v in value.values())
            or abs(sum(value.values()) - 1) > 1e-6
        ):
            raise ValueError("Five nonnegative matching weights must sum to 1")
        return value


@lru_cache
def get_settings():
    return Settings()
