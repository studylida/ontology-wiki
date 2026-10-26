"""Local launcher: read private .env, invoke server/CLI/tests without a shell."""
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[2]
env = {**os.environ, **{k: v for k, v in dotenv_values(root / '.env').items() if v is not None}}
env['PYTHONPATH'] = str(root / 'backend')
args = sys.argv[1:]
if not args:
    raise SystemExit('Usage: dev.py serve|worker|migrate|create-user|import-evaluation|import-legacy|test ...')
if args[0] == 'serve':
    command = [sys.executable, '-m', 'uvicorn', 'knowledge.main:app', '--host', '127.0.0.1', '--port', '8000', '--workers', '1', *args[1:]]
elif args[0] == 'test':
    command = [sys.executable, '-m', 'pytest', '--tb=short', *args[1:]]
else:
    command = [sys.executable, '-m', 'knowledge.cli', *args]
try:
    raise SystemExit(subprocess.call(command, cwd=root, env=env))
except KeyboardInterrupt:
    raise SystemExit(130) from None
