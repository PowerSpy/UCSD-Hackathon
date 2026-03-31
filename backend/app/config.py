from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LLM_PROVIDERS = frozenset({"openai", "anthropic", "zai"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./socratic.db"
    # openai | anthropic | zai (Z.AI OpenAI-compatible API)
    llm_provider: str = "zai"
    http_timeout_seconds: float = 120.0
    llm_max_retries: int = 2
    log_level: str = "INFO"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    zai_api_key: str | None = None
    zai_base_url: str = "https://api.z.ai/api/paas/v4"
    zai_model: str = "glm-5"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    @field_validator("llm_provider", mode="before")
    @classmethod
    def _normalize_llm_provider(cls, v: object) -> str:
        s = (str(v) if v is not None else "zai").lower().strip()
        if s not in _LLM_PROVIDERS:
            return "zai"
        return s


settings = Settings()
