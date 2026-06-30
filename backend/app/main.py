from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import get_connection, init_db
from .github_client import GitHubClient
from .service import dashboard, repo_detail, sync_repositories, topics
from .taxonomy import sector_payload


@asynccontextmanager
async def lifespan(_: FastAPI):
    with get_connection() as conn:
        init_db(conn)
    yield


app = FastAPI(title="Local GitHub Trend Intelligence Dashboard", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/sync")
async def sync() -> dict:
    settings = get_settings()
    client = GitHubClient(settings)
    try:
        with get_connection() as conn:
            return await sync_repositories(conn, client)
    finally:
        await client.close()


@app.get("/api/dashboard")
def get_dashboard(
    sector: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    with get_connection() as conn:
        return dashboard(conn, sector=sector, limit=limit)


@app.get("/api/repos/{owner}/{name}")
def get_repo(owner: str, name: str) -> dict:
    with get_connection() as conn:
        repo = repo_detail(conn, owner, name)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@app.get("/api/topics")
def get_topics() -> dict:
    with get_connection() as conn:
        return topics(conn)


@app.get("/api/config/sectors")
def get_sectors() -> dict:
    return {"sectors": sector_payload()}
