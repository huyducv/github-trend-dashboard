import argparse
import asyncio

from .config import get_settings
from .db import get_connection, init_db
from .github_client import GitHubClient
from .service import sync_repositories


async def run_sync() -> None:
    settings = get_settings()
    client = GitHubClient(settings)
    try:
        with get_connection() as conn:
            init_db(conn)
            result = await sync_repositories(conn, client)
            print(result)
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local GitHub trend dashboard tools")
    parser.add_argument("command", choices=["sync"])
    args = parser.parse_args()
    if args.command == "sync":
        asyncio.run(run_sync())


if __name__ == "__main__":
    main()
