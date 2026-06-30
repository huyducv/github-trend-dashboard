# Local GitHub Trend Intelligence Dashboard

A local intelligence dashboard for tracking rising GitHub repositories and developer topics.

## What it does

- Syncs repositories from the free GitHub API.
- Stores local daily snapshots in SQLite.
- Ranks repositories by star growth, forks, and recency.
- Groups repositories into editable sectors such as AI agents, developer tools, data analytics, security, and infrastructure.
- Provides a React dashboard for scanning trends and drilling into repository details.

## Quick Start

### Backend

```bash
conda env create -f environment.yml
conda activate gh-db
cd backend
cp ../.env.example .env
uvicorn app.main:app --reload --port 8001
```

Optional `.env` values:

```bash
GITHUB_TOKEN=ghp_your_token
GITHUB_USERNAME=your_github_username
DATABASE_PATH=./trend_dashboard.sqlite3
```

Then trigger a sync:

```bash
python -m app.cli sync
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, usually `http://localhost:5173`.

## Notes

- GitHub API access is free. A token is optional but strongly recommended for rate limits.
- V1 uses GitHub API only. Hacker News, Reddit, and AI summaries are intentionally left for later.
- README summaries are lightweight excerpts, not LLM-generated summaries.
