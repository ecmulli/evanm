from pathlib import Path

from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    anthropic_api_key: str
    notion_token: str
    notion_database_id: str = "301d285476a5476d91dc9f6225da4e87"

    model_config = {"env_prefix": "", "env_file": str(ENV_FILE), "extra": "ignore"}
