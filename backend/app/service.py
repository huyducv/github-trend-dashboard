from __future__ import annotations

from datetime import datetime, timezone
import sqlite3

from .db import decode_json, encode_json, init_db
from .github_client import GitHubClient, GitHubRepo
from .scoring import calculate_trend_score
from .taxonomy import appears_english, classify_repo


async def sync_repositories(conn: sqlite3.Connection, client: GitHubClient) -> dict:
    init_db(conn)
    discovered = await client.discover_repos()
    snapshot_at = datetime.now(timezone.utc).isoformat()
    kept = 0
    skipped = 0

    for repo in discovered:
        text_for_language = f"{repo.description or ''} {repo.readme_excerpt or ''}".strip()
        if not appears_english(text_for_language):
            skipped += 1
            continue
        upsert_repository(conn, repo, snapshot_at)
        repo_id = get_repo_id(conn, repo.owner, repo.name)
        previous = previous_snapshot(conn, repo_id)
        sectors = classify_repo(repo.topics, repo.description, repo.readme_excerpt, repo.language)
        trend_score, stars_delta, forks_delta = calculate_trend_score(
            repo.stars,
            repo.forks,
            previous["stars"] if previous else None,
            previous["forks"] if previous else None,
            repo.pushed_at,
        )
        conn.execute(
            """
            INSERT INTO snapshots (
                repo_id, snapshot_at, stars, forks, stars_delta, forks_delta, sectors, source, trend_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo_id,
                snapshot_at,
                repo.stars,
                repo.forks,
                stars_delta,
                forks_delta,
                encode_json(sectors),
                repo.source,
                trend_score,
            ),
        )
        kept += 1

    conn.commit()
    return {"snapshot_at": snapshot_at, "repositories_seen": len(discovered), "repositories_saved": kept, "skipped": skipped}


def upsert_repository(conn: sqlite3.Connection, repo: GitHubRepo, seen_at: str) -> None:
    existing = conn.execute(
        "SELECT id, first_seen_at FROM repositories WHERE owner = ? AND name = ?",
        (repo.owner, repo.name),
    ).fetchone()
    first_seen = existing["first_seen_at"] if existing else seen_at
    conn.execute(
        """
        INSERT INTO repositories (
            owner, name, url, description, language, topics, stars, forks, created_at, pushed_at,
            license, readme_excerpt, first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(owner, name) DO UPDATE SET
            url = excluded.url,
            description = excluded.description,
            language = excluded.language,
            topics = excluded.topics,
            stars = excluded.stars,
            forks = excluded.forks,
            created_at = excluded.created_at,
            pushed_at = excluded.pushed_at,
            license = excluded.license,
            readme_excerpt = excluded.readme_excerpt,
            last_seen_at = excluded.last_seen_at
        """,
        (
            repo.owner,
            repo.name,
            repo.url,
            repo.description,
            repo.language,
            encode_json(repo.topics),
            repo.stars,
            repo.forks,
            repo.created_at,
            repo.pushed_at,
            repo.license,
            repo.readme_excerpt,
            first_seen,
            seen_at,
        ),
    )


def get_repo_id(conn: sqlite3.Connection, owner: str, name: str) -> int:
    row = conn.execute("SELECT id FROM repositories WHERE owner = ? AND name = ?", (owner, name)).fetchone()
    if not row:
        raise ValueError(f"Repository not found after upsert: {owner}/{name}")
    return int(row["id"])


def previous_snapshot(conn: sqlite3.Connection, repo_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT stars, forks FROM snapshots WHERE repo_id = ? ORDER BY snapshot_at DESC LIMIT 1",
        (repo_id,),
    ).fetchone()


def dashboard(conn: sqlite3.Connection, sector: str | None = None, limit: int = 50) -> dict:
    init_db(conn)
    latest_snapshot = conn.execute("SELECT MAX(snapshot_at) AS value FROM snapshots").fetchone()["value"]
    if not latest_snapshot:
        return {"snapshot_at": None, "repos": [], "sectors": [], "totals": {"repositories": 0, "stars_delta": 0, "forks_delta": 0}}

    rows = conn.execute(
        """
        SELECT r.*, s.snapshot_at, s.stars_delta, s.forks_delta, s.sectors, s.source, s.trend_score
        FROM snapshots s
        JOIN repositories r ON r.id = s.repo_id
        WHERE s.snapshot_at = ?
        ORDER BY s.trend_score DESC, s.stars_delta DESC, r.stars DESC
        LIMIT ?
        """,
        (latest_snapshot, limit * 3),
    ).fetchall()
    repos = [row_to_repo(row) for row in rows]
    if sector:
        repos = [repo for repo in repos if sector in repo["sectors"]]
    repos = repos[:limit]

    sector_counts: dict[str, dict] = {}
    for repo in repos:
        for sector_id in repo["sectors"]:
            item = sector_counts.setdefault(sector_id, {"id": sector_id, "count": 0, "stars_delta": 0, "forks_delta": 0})
            item["count"] += 1
            item["stars_delta"] += repo["stars_delta"]
            item["forks_delta"] += repo["forks_delta"]

    return {
        "snapshot_at": latest_snapshot,
        "repos": repos,
        "sectors": sorted(sector_counts.values(), key=lambda item: item["stars_delta"], reverse=True),
        "totals": {
            "repositories": len(repos),
            "stars_delta": sum(repo["stars_delta"] for repo in repos),
            "forks_delta": sum(repo["forks_delta"] for repo in repos),
        },
    }


def topics(conn: sqlite3.Connection) -> dict:
    data = dashboard(conn, limit=500)
    topic_counts: dict[str, int] = {}
    for repo in data["repos"]:
        for topic in repo["topics"]:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return {
        "snapshot_at": data["snapshot_at"],
        "topics": [{"name": topic, "count": count} for topic, count in sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)[:50]],
        "sectors": data["sectors"],
    }


def repo_detail(conn: sqlite3.Connection, owner: str, name: str) -> dict | None:
    init_db(conn)
    repo = conn.execute("SELECT * FROM repositories WHERE lower(owner) = lower(?) AND lower(name) = lower(?)", (owner, name)).fetchone()
    if not repo:
        return None
    history = conn.execute(
        "SELECT snapshot_at, stars, forks, stars_delta, forks_delta, sectors, source, trend_score FROM snapshots WHERE repo_id = ? ORDER BY snapshot_at ASC",
        (repo["id"],),
    ).fetchall()
    payload = repo_row_to_dict(repo)
    payload["history"] = [
        {
            "snapshot_at": row["snapshot_at"],
            "stars": row["stars"],
            "forks": row["forks"],
            "stars_delta": row["stars_delta"],
            "forks_delta": row["forks_delta"],
            "sectors": decode_json(row["sectors"], []),
            "source": row["source"],
            "trend_score": row["trend_score"],
        }
        for row in history
    ]
    payload["sectors"] = payload["history"][-1]["sectors"] if payload["history"] else []
    return payload


def row_to_repo(row: sqlite3.Row) -> dict:
    payload = repo_row_to_dict(row)
    payload.update(
        {
            "snapshot_at": row["snapshot_at"],
            "stars_delta": row["stars_delta"],
            "forks_delta": row["forks_delta"],
            "sectors": decode_json(row["sectors"], []),
            "source": row["source"],
            "trend_score": row["trend_score"],
        }
    )
    return payload


def repo_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "owner": row["owner"],
        "name": row["name"],
        "url": row["url"],
        "description": row["description"],
        "language": row["language"],
        "topics": decode_json(row["topics"], []),
        "stars": row["stars"],
        "forks": row["forks"],
        "created_at": row["created_at"],
        "pushed_at": row["pushed_at"],
        "license": row["license"],
        "readme_excerpt": row["readme_excerpt"],
        "first_seen_at": row["first_seen_at"],
        "last_seen_at": row["last_seen_at"],
    }
