from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    github_token: str | None = None
    github_username: str | None = None
    database_path: str = "./trend_dashboard.sqlite3"
    github_max_results_per_query: int = 12


@lru_cache
def get_settings() -> Settings:
    root_env = Path(__file__).resolve().parents[2] / ".env"
    local_env = Path.cwd() / ".env"
    load_dotenv(root_env)
    load_dotenv(local_env, override=True)

    return Settings(
        github_token=os.getenv("GITHUB_TOKEN") or None,
        github_username=os.getenv("GITHUB_USERNAME") or None,
        database_path=os.getenv("DATABASE_PATH", "./trend_dashboard.sqlite3"),
        github_max_results_per_query=int(os.getenv("GITHUB_MAX_RESULTS_PER_QUERY", "12")),
    )
