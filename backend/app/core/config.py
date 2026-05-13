import json
import os
from pathlib import Path
from typing import List, Optional, Set

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ТутПроблема API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@db:5432/tutproblema"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_ECHO: bool = False

    # JWT
    SECRET_KEY: str = "please-go-and-change-it-to-something-else"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    TOKEN_ALGORITHM: str = "HS256"

    # Argon2
    ARGON2_TIME_COST: int = 1
    ARGON2_MEMORY_COST: int = 19456
    ARGON2_PARALLELISM: int = 1
    ARGON2_HASH_LEN: int = 16
    ARGON2_PEPPER: str = "please-go-and-change-it-to-something-else"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "PATCH",
    ]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    # Password Validation
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_SPECIAL_CHARS: str = "@$!%*?&#"
    PASSWORD_DISALLOW_COMMON: bool = True
    COMMON_PASSWORDS_FILE: str = "common-passwords.txt"
    COMMON_PASSWORDS: list[str] = []

    # Username Validation
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 50
    USERNAME_ALLOWED_PATTERN: str = r"^[a-zA-Z0-9_]+$"

    # Email
    EMAIL_MIN_LENGTH: int = 5
    EMAIL_MAX_LENGTH: int = 255
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "temp@gmail.com"
    SMTP_PASSWORD: str = "abcd efgh ijkl mnop"
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # Upload
    UPLOAD_DIR: str = "uploads"
    PHOTO_URL_PREFIX: str = "/api/uploads/photos"
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "gif", "webp"}
    MIN_PHOTOS_PER_REPORT: int = 1
    MAX_PHOTOS_PER_REPORT: int = 10

    # Report
    REPORT_TITLE_MIN_LENGTH: int = 5
    REPORT_TITLE_MAX_LENGTH: int = 200
    REPORT_DESCRIPTION_MAX_LENGTH: int = 2000
    RESOLUTION_COMMENT_MIN_LENGTH: int = 5
    RESOLUTION_COMMENT_MAX_LENGTH: int = 2000
    DEFAULT_RADIUS_METERS: int = 1000
    MIN_RADIUS_METERS: int = 500
    MAX_RADIUS_METERS: int = 3000
    MAX_REPORT_DISTANCE_METERS: int = 1000

    # Earth Radius
    EARTH_RADIUS_METERS: int = 6371000

    # Vote
    VOTE_VERIFICATION_BUFFER_METERS: int = 50
    VOTE_ACCURACY_MAX: int = 1000
    MAX_VOTE_DISTANCE_METERS: int = 1000

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MIN_PAGE_SIZE: int = 1
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_INCLUDE_TIMESTAMP: bool = True
    LOG_INCLUDE_APP_NAME: bool = True
    LOG_INCLUDE_REQUEST_ID: bool = True

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_CONNECTIONS: int = 20

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_BY_USER: bool = True

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD_SECONDS: int = 60

    RATE_LIMIT_GLOBAL_REQUESTS: int = 1000
    RATE_LIMIT_GLOBAL_PERIOD_SECONDS: int = 60

    RATE_LIMIT_AUTH_REQUESTS: int = 10
    RATE_LIMIT_AUTH_PERIOD_SECONDS: int = 60

    RATE_LIMIT_API_REQUESTS: int = 200
    RATE_LIMIT_API_PERIOD_SECONDS: int = 60

    RATE_LIMIT_UPLOAD_REQUESTS: int = 50
    RATE_LIMIT_UPLOAD_PERIOD_SECONDS: int = 3600

    RATE_LIMIT_VOTE_REQUESTS: int = 30
    RATE_LIMIT_VOTE_PERIOD_SECONDS: int = 60

    RATE_LIMIT_REPORT_CREATE_REQUESTS: int = 20
    RATE_LIMIT_REPORT_CREATE_PERIOD_SECONDS: int = 3600

    @field_validator(
        "CORS_ORIGINS",
        "CORS_ALLOW_METHODS",
        "CORS_ALLOW_HEADERS",
        "ALLOWED_HOSTS",
        mode="before",
    )
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return set(json.loads(v))
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


def load_common_passwords(file_path: str) -> List[str]:
    passwords = []
    try:
        possible_paths = [
            Path(file_path),
            Path(__file__).parent.parent.parent / file_path,
            Path.cwd() / file_path,
            Path("/app") / file_path,
        ]

        for path in possible_paths:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    passwords = [
                        line.strip().lower() for line in f if line.strip()
                    ]
                break

        if not passwords:
            print(
                f"Warning: Common passwords file '{file_path}' not found in any location. Using default list."
            )
            passwords = [
                "password",
                "password123",
                "12345678",
                "qwerty123",
                "admin123",
                "letmein123",
                "welcome123",
            ]
    except Exception as e:
        print(f"Error loading common passwords file: {e}. Using default list.")
        import traceback

        traceback.print_exc()
        passwords = [
            "password",
            "password123",
            "12345678",
            "qwerty123",
            "admin123",
            "letmein123",
            "welcome123",
        ]

    return passwords


settings = Settings()

if settings.PASSWORD_DISALLOW_COMMON:
    settings.COMMON_PASSWORDS = load_common_passwords(
        settings.COMMON_PASSWORDS_FILE
    )

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
