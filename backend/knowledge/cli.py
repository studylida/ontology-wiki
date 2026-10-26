"""Explicit administration commands; no account, schema or paid call on startup."""
from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os

from sqlalchemy import select

from knowledge.core.config import get_settings
from knowledge.core.database import get_session_factory
from knowledge.core.ids import new_id
from knowledge.registry import load_entities


async def execute(args):
    load_entities()
    if args.command == "migrate":
        from knowledge.migration.schema import migrate
        return await migrate(args.database_name)
    if args.command == "worker":
        from knowledge.jobs.worker import run_worker
        await run_worker(once=args.once)
        return {"worker": "stopped"}
    sessions = get_session_factory()
    if args.command == "create-user":
        from knowledge.identity.entities import User
        from knowledge.identity.security import hash_password
        password = os.environ.get("OW_BOOTSTRAP_PASSWORD") or getpass.getpass("New account password: ")
        if len(password) < 12:
            raise ValueError("Use at least 12 characters")
        async with sessions() as session, session.begin():
            if await session.scalar(select(User).where(User.username == args.username)):
                raise ValueError("User already exists; this command never overwrites an account")
            user = User(id=new_id("usr"), username=args.username, password_hash=hash_password(password),
                role=args.role, kind="service" if args.service else "user", permissions=args.permission,
                auto_wiki=get_settings().auto_wiki_default if not args.service else False)
            session.add(user)
            return {"id": user.id, "username": user.username, "role": user.role, "kind": user.kind}
    if args.command == "import-evaluation":
        from knowledge.migration.evaluation import import_evaluation
        return await import_evaluation(sessions, get_settings(), args)
    if args.command == "import-legacy":
        from knowledge.migration.legacy import import_legacy
        return await import_legacy(sessions, args.export, args.source_system, apply=args.apply)
    raise ValueError("Unknown command")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    migration = sub.add_parser("migrate")
    migration.add_argument("--database-name", required=True)
    user = sub.add_parser("create-user")
    user.add_argument("--username", required=True)
    user.add_argument("--role", choices=["user", "reviewer", "admin"], default="user")
    user.add_argument("--service", action="store_true")
    user.add_argument("--permission", action="append", default=[])
    worker = sub.add_parser("worker")
    worker.add_argument("--once", action="store_true")
    evaluation = sub.add_parser("import-evaluation")
    evaluation.add_argument("--corpus-zip", required=True)
    evaluation.add_argument("--evaluation-dir", required=True)
    evaluation.add_argument("--owner", required=True)
    evaluation.add_argument("--model", choices=["text-embedding-3-small", "text-embedding-3-large"], default="text-embedding-3-large")
    evaluation.add_argument("--approve-for-development", action="store_true", required=True)
    legacy = sub.add_parser("import-legacy")
    legacy.add_argument("--export", required=True)
    legacy.add_argument("--source-system", required=True)
    legacy.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(execute(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
