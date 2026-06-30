from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .config import get_settings


def get_connection(path: str | None = None) -> sqlite3.Connection:
    db_path = Path(path or get_settings().database_path)
    if db_path.parent != Path("."):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            description TEXT,
            language TEXT,
            topics TEXT NOT NULL DEFAULT '[]',
            stars INTEGER NOT NULL DEFAULT 0,
            forks INTEGER NOT NULL DEFAULT 0,
            created_at TEXT,
            pushed_at TEXT,
            license TEXT,
            readme_excerpt TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            UNIQUE(owner, name)
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
            snapshot_at TEXT NOT NULL,
            stars INTEGER NOT NULL,
            forks INTEGER NOT NULL,
            stars_delta INTEGER NOT NULL DEFAULT 0,
            forks_delta INTEGER NOT NULL DEFAULT 0,
            sectors TEXT NOT NULL DEFAULT '[]',
            source TEXT NOT NULL,
            trend_score REAL NOT NULL DEFAULT 0,
            UNIQUE(repo_id, snapshot_at, source)
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_snapshot_at ON snapshots(snapshot_at);
        CREATE INDEX IF NOT EXISTS idx_snapshots_score ON snapshots(trend_score DESC);
        """
    )
    conn.commit()


def encode_json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


def decode_json(value: str | None, fallback: Any) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback
