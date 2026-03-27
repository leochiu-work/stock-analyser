from datetime import date

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    default_start_date: date = date(2020, 1, 1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
