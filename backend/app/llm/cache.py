import os
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Any

DEFAULT_CACHE_DIR = Path("./data")
DEFAULT_CACHE_DB = DEFAULT_CACHE_DIR / "llm_cache.db"

def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path or os.getenv("LLM_CACHE_PATH", str(DEFAULT_CACHE_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_cache (
            key TEXT PRIMARY KEY,
            provider TEXT,
            model TEXT,
            system TEXT,
            user TEXT,
            response_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn

def compute_cache_key(provider: str, model: str, system: str, user: str) -> str:
    """Computes sha256(provider+model+system+user) per architecture §7.1."""
    raw = f"{provider}:{model}:{system}:{user}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def get_cached_response(key: str, db_path: Path | str | None = None) -> dict[str, Any] | None:
    """Retrieves cached JSON completion by hash key."""
    try:
        with _get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT response_json FROM llm_cache WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return None

def set_cached_response(
    key: str,
    provider: str,
    model: str,
    system: str,
    user: str,
    response: dict[str, Any],
    db_path: Path | str | None = None
) -> None:
    """Stores LLM response in SQLite cache."""
    try:
        with _get_connection(db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO llm_cache (key, provider, model, system, user, response_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, provider, model, system, user, json.dumps(response))
            )
            conn.commit()
    except Exception:
        pass
