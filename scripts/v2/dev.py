"""Development entry points for implemented capabilities."""
import os
from pathlib import Path
import subprocess
import sys
from dotenv import dotenv_values
ROOT = Path(__file__).resolve().parents[2]


def main():
    args = sys.argv[1:]
    if not args or args[0] not in {'serve','worker','migrate','create-user','test'}:
        raise SystemExit('usage: dev.py serve|worker|migrate|create-user|test')
    environment = {**{k:v for k,v in dotenv_values(ROOT / '.env').items() if v is not None},**os.environ}
    environment['PYTHONPATH'] = str(ROOT / 'backend')
    command,rest = args[0],args[1:]
    if command == 'serve':
        invocation = [sys.executable,'-m','uvicorn','knowledge.main:app','--host','127.0.0.1','--port','8000',*rest]
    elif command == 'test':
        invocation = [sys.executable,'-m','pytest','tests/foundation','tests/unit','tests/evaluation',*rest]
    else:
        invocation = [sys.executable,'-m','knowledge.cli',command,*rest]
    raise SystemExit(subprocess.call(invocation,cwd=ROOT,env=environment))


if __name__ == '__main__':
    main()
