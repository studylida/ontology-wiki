"""Local launcher: read private .env, invoke server/CLI/tests without a shell."""
import os
from pathlib import Path
import subprocess
import sys

from dotenv import dotenv_values

root = Path(__file__).resolve().parents[2]
env = {**os.environ, **{k: v for k, v in dotenv_values(root / '.env').items() if v is not None}}
args = sys.argv[1:]
if args and args[0] in ('serve', 'worker'):
    env.update({k: v for k, v in dotenv_values(root / '.env.rag.local', encoding='utf-8-sig').items() if v is not None
                and (k == 'OW_PDF_PARSER' or k.startswith(('OW_RERANKER_', 'OW_RETRIEVAL_', 'OW_LIGHTRAG_', 'OW_DOCLING_')))})
env['PYTHONPATH'] = str(root / 'backend')
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
