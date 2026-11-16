"""Application settings, loaded from environment variables and backend/.env."""

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    """Every value can be overridden in backend/.env or as an environment variable."""

    APP_NAME: str = "AegisCloud"

    # Database
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "aegiscloud_db"

    # Authentication
    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:5173"

    # Single-account mode: only DEMO_EMAIL can sign in, and sign-up is disabled
    SINGLE_ACCOUNT_MODE: bool = True
    DEMO_EMAIL: str = "admin@gmail.com"
    DEMO_PASSWORD: str = "Test@123"

    # Trivy
    TRIVY_TIMEOUT_SECONDS: int = 180
    MAX_CONCURRENT_SCANS: int = 2

    # Falco webhook shared secret (empty = no check, local development only)
    FALCO_WEBHOOK_SECRET: str = ""

    # AWS SNS
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SNS_TOPIC_ARN: str = ""
    SNS_NOTIFY_PRIORITIES: str = "critical"

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        """CORS_ORIGINS as a clean list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def sns_priorities(self) -> set[str]:
        """Alert priorities that should trigger an SNS notification, lower-cased."""
        return {p.strip().lower() for p in self.SNS_NOTIFY_PRIORITIES.split(",") if p.strip()}


settings = Settings()