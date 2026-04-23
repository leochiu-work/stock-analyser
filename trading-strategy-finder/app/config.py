from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    api_key: str = "changeme"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "gemma3"
    ollama_embed_model: str = "nomic-embed-text"
    e2b_api_key: str = ""
    e2b_timeout_seconds: int = 60
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    price_service_base_url: str = "http://stock-price-service:8000"
    ta_service_base_url: str = "http://stock-ta-service:8000"
    max_research_iterations: int = 3
    backtest_years: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
