from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "Automated Multi-Platform Posting System"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 4000
    HTTP_TIMEOUT_SECONDS: float = 10.0

    # Fallback / Simulation switch
    # When enabled, platforms without configured credentials simulate realistic success
    # while platforms with real credentials call actual external APIs.
    ALLOW_MOCK_FALLBACK: bool = True

    # Platform 1: Telegram Bot API
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Platform 2: Discord Webhook API
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # Platform 3: Slack Incoming Webhook
    SLACK_WEBHOOK_URL: Optional[str] = None

    # Platform 4: Mastodon Social REST API
    MASTODON_INSTANCE_URL: str = "https://mastodon.social"
    MASTODON_ACCESS_TOKEN: Optional[str] = None

    # Platform 5: Bluesky (AT Protocol)
    BLUESKY_HANDLE: Optional[str] = None
    BLUESKY_APP_PASSWORD: Optional[str] = None
    BLUESKY_PDS_URL: str = "https://bsky.social"

    # Platform 6 (LLM Platform): Hugging Face Community / Discussions
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    HUGGINGFACE_REPO_ID: Optional[str] = None  # Format: "username/repo" or "spaces/..."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
