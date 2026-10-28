"""Development entry points for the implemented foundation stage."""
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def main():
    args = sys.argv[1:]
    if not args or args[0] not in {"serve", "migrate", "create-user", "test"}:
        raise SystemExit("usage: dev.py serve|migrate|create-user|test (worker/ingestion/answers arrive in later stages)")
    # Explicit environment takes precedence: tests never inherit a production
    # database or provider key from the repository's .env by accident.
    environment = {**{k: v for k, v in dotenv_values(ROOT / ".env").items() if v is not None}, **os.environ}
    environment["PYTHONPATH"] = str(ROOT / "backend")
    command, rest = args[0], args[1:]
    if command == "serve":
        invocation = [sys.executable, "-m", "uvicorn", "knowledge.main:app", "--host", "127.0.0.1", "--port", "8000", *rest]
    elif command == "test":
        invocation = [sys.executable, "-m", "pytest", "tests/foundation", *rest]
    else:
        invocation = [sys.executable, "-m", "knowledge.cli", command, *rest]
    raise SystemExit(subprocess.call(invocation, cwd=ROOT, env=environment))


if __name__ == "__main__":
    main()
