from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .config import Settings


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str
    url: str
    description: str | None
    language: str | None
    topics: list[str]
    stars: int
    forks: int
    created_at: str | None
    pushed_at: str | None
    license: str | None
    readme_excerpt: str | None
    source: str


class GitHubClient:
    def __init__(self, settings: Settings):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "local-trend-dashboard",
        }
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
        self._client = httpx.AsyncClient(base_url="https://api.github.com", headers=headers, timeout=20)
        self._settings = settings

    async def close(self) -> None:
        await self._client.aclose()

    async def discover_repos(self) -> list[GitHubRepo]:
        repos: dict[str, GitHubRepo] = {}
        for sector_query in discovery_queries():
            items = await self.search_repositories(sector_query["query"], sector_query["source"])
            for repo in items:
                repos[f"{repo.owner}/{repo.name}".lower()] = repo

        if self._settings.github_username:
            for repo in await self.starred_repositories(self._settings.github_username):
                repos[f"{repo.owner}/{repo.name}".lower()] = repo

        return list(repos.values())

    async def search_repositories(self, query: str, source: str) -> list[GitHubRepo]:
        response = await self._client.get(
            "/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": self._settings.github_max_results_per_query,
            },
        )
        response.raise_for_status()
        data = response.json()
        repos = []
        for item in data.get("items", []):
            repos.append(await self._repo_from_item(item, source))
        return repos

    async def starred_repositories(self, username: str) -> list[GitHubRepo]:
        response = await self._client.get(f"/users/{username}/starred", params={"per_page": 50, "sort": "updated"})
        response.raise_for_status()
        repos = []
        for item in response.json():
            repos.append(await self._repo_from_item(item, "starred"))
        return repos

    async def _repo_from_item(self, item: dict[str, Any], source: str) -> GitHubRepo:
        owner = item.get("owner", {}).get("login", "")
        name = item.get("name", "")
        topics = item.get("topics") or []
        if not topics and owner and name:
            topics = await self._repo_topics(owner, name)

        readme_excerpt = await self._readme_excerpt(owner, name) if owner and name else None

        return GitHubRepo(
            owner=owner,
            name=name,
            url=item.get("html_url", ""),
            description=item.get("description"),
            language=item.get("language"),
            topics=topics,
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            created_at=item.get("created_at"),
            pushed_at=item.get("pushed_at"),
            license=(item.get("license") or {}).get("spdx_id"),
            readme_excerpt=readme_excerpt,
            source=source,
        )

    async def _repo_topics(self, owner: str, name: str) -> list[str]:
        response = await self._client.get(f"/repos/{owner}/{name}/topics")
        if response.status_code >= 400:
            return []
        return response.json().get("names", [])

    async def _readme_excerpt(self, owner: str, name: str) -> str | None:
        response = await self._client.get(f"/repos/{owner}/{name}/readme")
        if response.status_code >= 400:
            return None
        content = response.json().get("content")
        if not content:
            return None
        try:
            decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
        except ValueError:
            return None
        clean_lines = []
        for line in decoded.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped and not stripped.startswith(("!", "[!", "<")):
                clean_lines.append(stripped)
            if sum(len(line) for line in clean_lines) > 900:
                break
        return " ".join(clean_lines)[:1000] or None


def discovery_queries() -> list[dict[str, str]]:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    return [
        {"source": "sector:ai-agents", "query": f"topic:ai-agent pushed:>{since}"},
        {"source": "sector:ai-agents", "query": f"agents llm in:description,readme pushed:>{since}"},
        {"source": "sector:ai-infra", "query": f"rag embeddings in:description,readme pushed:>{since}"},
        {"source": "sector:developer-tools", "query": f"cli developer-tools in:description,readme pushed:>{since}"},
        {"source": "sector:data-analytics", "query": f"analytics dashboard in:description,readme pushed:>{since}"},
        {"source": "sector:cloud-devops", "query": f"kubernetes observability in:description,readme pushed:>{since}"},
        {"source": "sector:security", "query": f"security scanner in:description,readme pushed:>{since}"},
    ]
