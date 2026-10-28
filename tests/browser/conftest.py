"""Chromium against the built UI, real HTTP/PostgreSQL and document worker. Providers alone are fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import time
from types import SimpleNamespace
import httpx
import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('foundation_support', ROOT / 'tests/foundation/conftest.py')
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)
database_factory = support.database_factory

@pytest.fixture
def browser_app(database_factory, tmp_path):
    with database_factory() as database:
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'OW_DATABASE_URL': database.url,
            'OW_AUTH_SECRET': secrets.token_hex(32), 'OW_BOOTSTRAP_PASSWORD': secrets.token_urlsafe(24),
            'OW_PROVIDER_MODE': 'fixture', 'OW_STORAGE_PATH': str(tmp_path / 'raw'), 'OW_PDF_PARSER': 'legacy'}
        env.pop('OPENAI_API_KEY', None)
        support.cli(env, 'migrate', '--database-name', database.name)
        for name in ('alice', 'bob'):
            support.cli(env, 'create-user', '--username', name)
        server = support.Server(env, tmp_path)
        frontend = None
        output = (tmp_path / 'frontend.log').open('w')
        try:
            server.start()
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0)); port = listener.getsockname()[1]
            frontend = subprocess.Popen(['npm', 'run', 'preview', '--', '--port', str(port), '--strictPort'],
                cwd=ROOT / 'frontend', env={**env, 'OW_API_PROXY_TARGET': str(server.client.base_url)},
                stdout=output, stderr=subprocess.STDOUT)
            url = f'http://127.0.0.1:{port}'
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if frontend.poll() is not None:
                    raise AssertionError((tmp_path / 'frontend.log').read_text())
                try:
                    if httpx.get(url, trust_env=False).status_code == 200: break
                except httpx.TransportError: pass
                time.sleep(.1)
            else: raise AssertionError('Frontend did not start')
            with sync_playwright() as engine:
                browser = engine.chromium.launch()
                context = browser.new_context(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
                page = context.new_page(); page.set_default_timeout(15000)
                errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
                try:
                    yield SimpleNamespace(page=page, context=context, url=url, server=server, database=database,
                        environment=env, work=lambda: json.loads(support.cli(env, 'worker', '--once').stdout), directory=tmp_path)
                    assert not errors, errors
                finally:
                    artifacts = Path(os.environ.get('RUNNER_TEMP', str(tmp_path))) / 'browser-artifacts'
                    artifacts.mkdir(exist_ok=True)
                    page.screenshot(path=str(artifacts / (tmp_path.name + '.png')), full_page=True)
                    context.close(); browser.close()
        finally:
            if frontend:
                frontend.terminate()
                try: frontend.wait(timeout=10)
                except subprocess.TimeoutExpired: frontend.kill(); frontend.wait()
            output.close(); server.stop()
