"""Run the real research UI/API with memory-only storage and existing credentials.

Pass --env-file explicitly: the application normally resolves .env from cwd.
This runner never copies settings or credentials into the isolated checkout.
"""
import argparse
import os
from pathlib import Path
import sys

from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18004)
    args = parser.parse_args()
    if not args.env_file.is_file():
        parser.error("The explicit settings file does not exist.")
    load_dotenv(args.env_file, override=False)
    # Set these before importing any application module: startup creates tables/users.
    os.environ.update(DB_ENGINE="sqlite", SQLITE_DATABASE_URL="sqlite+aiosqlite:///:memory:",
                      USE_IN_MEMORY_REDIS="true", DEBUG="false")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from backend.app.core.config import settings
    if not settings.OPENAI_API_KEY:
        parser.error("Research requires configured OpenAI credentials; no model fallback is used.")
    assert settings.active_db_url == "sqlite+aiosqlite:///:memory:"
    assert settings.USE_IN_MEMORY_REDIS
    from backend.app.main import app
    import uvicorn
    print(f"ISOLATED LIVE: memory DB/cache; real search and {settings.RESEARCH_MODEL}; loopback only", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
