"""Real PostgreSQL and real Uvicorn processes; no production data or model calls."""
import asyncio
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from types import SimpleNamespace
import uuid

import asyncpg
import httpx
import pytest
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]


async def database_command(url, sql, *arguments, fetch=False):
    connection = await asyncpg.connect(url.replace("postgresql+asyncpg://", "postgresql://", 1))
    try:
        if fetch:
            return [dict(row) for row in await connection.fetch(sql, *arguments)]
        return await connection.execute(sql, *arguments)
    finally:
        await connection.close()


@pytest.fixture(scope="session")
def database_factory():
    base = os.environ.get("OW_TEST_DATABASE_URL")
    if not base:
        pytest.skip("Set OW_TEST_DATABASE_URL to a disposable local PostgreSQL database ending in _test")
    parsed = make_url(base)
    if parsed.host not in {"127.0.0.1", "localhost", "::1"} or not (parsed.database or "").endswith("_test"):
        pytest.fail("Foundation tests require an explicitly local *_test database; no external database is touched")

    @contextmanager
    def factory():
        name = "ow_foundation_" + uuid.uuid4().hex + "_test"
        url = parsed.set(database=name).render_as_string(hide_password=False)
        asyncio.run(database_command(base, f'CREATE DATABASE "{name}"'))
        try:
            yield SimpleNamespace(name=name, url=url,
                execute=lambda sql, *args: asyncio.run(database_command(url, sql, *args)),
                query=lambda sql, *args: asyncio.run(database_command(url, sql, *args, fetch=True)))
        finally:
            # Only the randomly named database created by this fixture is dropped.
            asyncio.run(database_command(base, "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=$1 AND pid <> pg_backend_pid()", name))
            asyncio.run(database_command(base, f'DROP DATABASE "{name}"'))
    return factory


def cli(environment, *args, expect=0):
    result = subprocess.run([sys.executable, "-m", "knowledge.cli", *args], cwd=ROOT,
                            env=environment, capture_output=True, text=True, timeout=45)
    if expect == 0:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, "Command unexpectedly succeeded"
    return result


class Server:
    def __init__(self, environment, directory):
        self.environment, self.directory = environment, directory
        self.process = None
        self.output = None
        self.client = None
        self.starts = 0

    def start(self):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.starts += 1
        self.log_path = self.directory / f"server-{self.starts}.log"
        self.output = self.log_path.open("w", encoding="utf-8")
        self.process = subprocess.Popen([sys.executable, "-m", "uvicorn", "knowledge.main:app",
            "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, env=self.environment,
            stdout=self.output, stderr=subprocess.STDOUT)
        self.client = httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=10, trust_env=False)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise AssertionError(self.log_path.read_text(encoding="utf-8"))
            try:
                if self.client.get("/api/v1/health").status_code == 200:
                    return
            except httpx.TransportError:
                pass
            time.sleep(.1)
        raise AssertionError("Server did not become ready: " + self.log_path.read_text(encoding="utf-8"))

    def stop(self):
        if self.client is not None:
            self.client.close()
            self.client = None
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        if self.output is not None:
            self.output.close()

    def restart(self):
        self.stop()
        self.start()

    def request(self, method, path, *, token=None, **kwargs):
        headers = {"Authorization": "Bearer " + token} if token else {}
        return self.client.request(method, "/api/v1" + path, headers=headers, **kwargs)


@pytest.fixture(scope="session")
def application(database_factory, tmp_path_factory):
    with database_factory() as database:
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "backend"),
            "OW_DATABASE_URL": database.url, "OW_AUTH_SECRET": secrets.token_hex(32),
            "OW_PROVIDER_MODE": "disabled", "OW_BOOTSTRAP_PASSWORD": secrets.token_urlsafe(24)}
        environment.pop("OPENAI_API_KEY", None)
        cli(environment, "migrate", "--database-name", database.name)
        for name, role in (("alice", "user"), ("bob", "user"), ("operator", "admin")):
            cli(environment, "create-user", "--username", name, "--role", role)
        server = Server(environment, tmp_path_factory.mktemp("foundation-process"))
        try:
            server.start()
            tokens = {}
            for name in ("alice", "bob", "operator"):
                response = server.request("POST", "/auth/login", json={
                    "username": name, "password": environment["OW_BOOTSTRAP_PASSWORD"]})
                assert response.status_code == 200, response.text
                tokens[name] = response.json()["accessToken"]
            yield SimpleNamespace(server=server, database=database, environment=environment, tokens=tokens)
        finally:
            server.stop()
