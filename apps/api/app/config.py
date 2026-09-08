from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_FILE_PATH = Path(__file__).resolve()
# The source tree has a repository root three levels up; the container layout
# is /app/app and only needs a local fallback because Compose supplies paths.
ROOT = _FILE_PATH.parents[3] if len(_FILE_PATH.parents) > 3 else _FILE_PATH.parents[1]


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(int(default))).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    ryo_mcp_url: str = os.getenv("RYO_MCP_URL", "https://app-ryochan.com/api/mcp")
    ryo_mcp_key: str = os.getenv("RYO_MCP_KEY", "")
    fixtures: bool = _bool("SCARBOOK_FIXTURES")
    database_path: str = os.getenv("DATABASE_PATH", str(ROOT / "data" / "scarbook.db"))
    raw_dir: str = os.getenv("RAW_DIR", str(ROOT / "data" / "raw"))
    cors_origins: tuple[str, ...] = tuple(
        item.strip()
        for item in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,https://scarbook.pages.dev,https://scarbook.YOURDOMAIN",
        ).split(",")
        if item.strip()
    )
    # Groq is OpenAI-compatible; these defaults make the free-tier setup a
    # one-key configuration while preserving the generic variable names.
    llm_provider: str = os.getenv("LLM_PROVIDER") or "https://api.groq.com/openai/v1"
    llm_api_key: str = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL") or "openai/gpt-oss-20b"


settings = Settings()
