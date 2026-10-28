"""Explicit setup and document-worker commands. No import or generation side effects."""
import argparse
import asyncio
import getpass
import json
import os
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from .core.config import get_settings
from .identity.entities import User
from .identity.security import hash_password
from .migration.schema import assert_current_schema, migrate
from .registry import load_entities


async def create_user(args):
    username = args.username.strip()
    if not username or len(username) > 128 or '\x00' in username:
        raise ValueError('username must contain 1..128 non-NUL characters')
    password = os.environ.get('OW_BOOTSTRAP_PASSWORD') or getpass.getpass('Password: ')
    if not 12 <= len(password) <= 1024:
        raise ValueError('Password must contain 12..1024 characters')
    encoded = await asyncio.to_thread(hash_password,password)
    engine = create_async_engine(get_settings().database_url)
    sessions = async_sessionmaker(engine,expire_on_commit=False,autoflush=False)
    try:
        async with sessions() as session, session.begin():
            await assert_current_schema(session)
            if await session.scalar(select(User.id).where(User.username == username)):
                raise ValueError('Username already exists; existing accounts are not overwritten')
            user = User(username=username,password_hash=encoded,role=args.role)
            session.add(user)
            await session.flush()
            result = {'id':user.id,'username':user.username,'role':user.role}
        return result
    except IntegrityError as exc:
        raise ValueError('Could not create account; existing accounts are not overwritten') from exc
    finally:
        await engine.dispose()


def parser():
    result = argparse.ArgumentParser(description='Knowledge assistant setup and shared-document worker')
    commands = result.add_subparsers(dest='command',required=True)
    migration = commands.add_parser('migrate',help='Apply v3 migrations without deleting data')
    migration.add_argument('--database-name',required=True)
    user = commands.add_parser('create-user',help='Create an employee account explicitly')
    user.add_argument('--username',required=True)
    user.add_argument('--role',choices=('user','admin'),default='user')
    worker = commands.add_parser('worker',help='Process queued document jobs without generation or ontology')
    worker.add_argument('--once',action='store_true')
    return result


async def run(args):
    load_entities()
    if args.command == 'migrate':
        return await migrate(args.database_name)
    if args.command == 'worker':
        from .jobs.worker import run_worker
        return await run_worker(once=args.once)
    return await create_user(args)


def main():
    arguments = parser().parse_args()
    try:
        result = asyncio.run(run(arguments))
    except (ValueError,RuntimeError) as exc:
        raise SystemExit(str(exc)) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
