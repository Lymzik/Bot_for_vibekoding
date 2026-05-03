from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    telegram_bot_token: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key_text: str
    default_text_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_api_key_image: str
    default_image_model: str = "fal-ai/flux-pro"
    webhook_base_url: str = ""
    log_level: str = "INFO"
    max_concurrent_tasks: int = 5
    webhook_secret: str = "vibemaster-secret-2024"
    port: int = 8080


settings = Settings()
