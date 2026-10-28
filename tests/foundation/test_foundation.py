import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import pytest

from conftest import ROOT, cli


def new_conversation(application, name="alice"):
    response = application.server.request("POST", "/conversations", token=application.tokens[name],
                                          json={"title": "사내 문헌 질문"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_real_login_schema_and_health(application):
    response = application.server.request("GET", "/health")
    assert response.status_code == 200
    assert response.json()["capabilities"] == ["authentication", "private_conversations", "message_storage"]
    tables = {row["tablename"] for row in application.database.query(
        "SELECT tablename FROM pg_tables WHERE schemaname='public'")}
    assert tables == {"knowledge_schema_migrations", "knowledge_users", "conversations", "messages"}
    columns = {row["column_name"] for row in application.database.query(
        "SELECT column_name FROM information_schema.columns WHERE table_schema='public'")}
    assert not columns.intersection({"auto_wiki", "response_mode", "extended", "next_settings"})
    me = application.server.request("GET", "/auth/me", token=application.tokens["alice"])
    assert me.status_code == 200 and me.json()["username"] == "alice"
    assert not any("wiki" in permission or "research" in permission for permission in me.json()["permissions"])
    assert me.headers["cache-control"] == "no-store"


def test_round_trip_and_real_server_restart(application):
    server, token = application.server, application.tokens["alice"]
    conversation = new_conversation(application)
    message = server.request("POST", f"/conversations/{conversation}/messages", token=token,
                             json={"content": "기록 보존을 확인하는 질문입니다."})
    assert message.status_code == 201 and message.json()["role"] == "user"
    changed = server.request("PATCH", f"/conversations/{conversation}", token=token,
                             json={"title": "저장 후 재시작"})
    assert changed.status_code == 200
    before = server.request("GET", f"/conversations/{conversation}", token=token).json()
    old_pid = server.process.pid
    server.restart()
    assert server.process.pid != old_pid
    after = server.request("GET", f"/conversations/{conversation}", token=token)
    assert after.status_code == 200 and after.json() == before
    assert after.json()["messages"][0]["id"] == message.json()["id"]
    assert len(after.json()["messages"]) == 1  # no fabricated assistant completion
    assert after.json()["title"] == "저장 후 재시작"
    rows = application.database.query("SELECT content FROM messages WHERE conversation_id=$1", conversation)
    assert rows == [{"content": "기록 보존을 확인하는 질문입니다."}]


@pytest.mark.parametrize("intruder", ["bob", "operator"])
def test_other_employee_and_admin_cannot_access_private_conversation(application, intruder):
    conversation = new_conversation(application)
    server, token = application.server, application.tokens[intruder]
    listed = server.request("GET", "/conversations", token=token)
    assert listed.status_code == 200
    assert conversation not in {item["id"] for item in listed.json()["items"]}
    for method, path, values in (
        ("GET", f"/conversations/{conversation}", {}),
        ("PATCH", f"/conversations/{conversation}", {"json": {"title": "변경 시도"}}),
        ("POST", f"/conversations/{conversation}/messages", {"json": {"content": "접근 시도"}}),
    ):
        response = server.request(method, path, token=token, **values)
        assert response.status_code == 404, response.text
    owned = server.request("GET", f"/conversations/{conversation}", token=application.tokens["alice"])
    assert owned.json()["title"] == "사내 문헌 질문" and owned.json()["messages"] == []


@pytest.mark.parametrize("path", ["/auth/me", "/conversations", "/conversations/unknown"])
def test_authentication_required(application, path):
    assert application.server.request("GET", path).status_code == 401
    assert application.server.request("GET", path, token="not-a-token").status_code == 401


def test_wrong_password_and_no_default_account(application):
    for name in ("alice", "admin", "nonexistent"):
        response = application.server.request("POST", "/auth/login", json={"username": name, "password": "wrong-password"})
        assert response.status_code == 401
    users = application.database.query("SELECT username FROM knowledge_users ORDER BY username")
    assert users == [{"username": "alice"}, {"username": "bob"}, {"username": "operator"}]


@pytest.mark.parametrize("body", [{"title": " "}, {"title": "a" * 301}, {"title": "x", "autoWiki": True},
                                  {"title": "x", "ownerId": "another-user"}, {"title": "\x00"}])
def test_conversation_contract_rejects_legacy_and_invalid_fields(application, body):
    assert application.server.request("POST", "/conversations", token=application.tokens["alice"], json=body).status_code == 422


@pytest.mark.parametrize("body", [{"content": " "}, {"content": "a" * 30001}, {"content": "\x00"},
                                  {"content": "x", "role": "assistant"}, {"content": "x", "extended": True}])
def test_message_contract_does_not_allow_spoofed_or_legacy_data(application, body):
    conversation = new_conversation(application)
    assert application.server.request("POST", f"/conversations/{conversation}/messages",
        token=application.tokens["alice"], json=body).status_code == 422


def test_blank_patch_rejected_and_default_title_works(application):
    server, token = application.server, application.tokens["alice"]
    response = server.request("POST", "/conversations", token=token, json={})
    assert response.status_code == 201 and response.json()["title"] == "새 대화"
    for body in ({}, {"title": None}, {"title": " "}, {"autoWiki": False}):
        assert server.request("PATCH", "/conversations/" + response.json()["id"], token=token, json=body).status_code == 422


def test_migration_is_idempotent_and_target_is_explicit(application):
    before = application.database.query("SELECT id FROM conversations ORDER BY id")
    result = cli(application.environment, "migrate", "--database-name", application.database.name)
    assert json.loads(result.stdout)["applied"] == []
    mismatch = cli(application.environment, "migrate", "--database-name", "wrong_database_test", expect=1)
    assert "must equal" in mismatch.stderr
    assert application.database.query("SELECT id FROM conversations ORDER BY id") == before
    duplicate = cli(application.environment, "create-user", "--username", "alice", expect=1)
    assert "already exists" in duplicate.stderr


def test_legacy_database_is_rejected_without_mutation(database_factory):
    with database_factory() as database:
        database.execute("CREATE TABLE old_data (value text); INSERT INTO old_data VALUES ('keep-me')")
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "OW_DATABASE_URL": database.url}
        failed = cli(environment, "migrate", "--database-name", database.name, expect=1)
        assert "not empty" in failed.stderr
        assert database.query("SELECT value FROM old_data") == [{"value": "keep-me"}]
        assert database.query("SELECT tablename FROM pg_tables WHERE schemaname='public'") == [{"tablename": "old_data"}]


def test_missing_schema_refuses_startup_without_seed_or_migration(database_factory):
    with database_factory() as database:
        environment = {**os.environ, "PYTHONPATH": str(ROOT / "backend"), "OW_DATABASE_URL": database.url,
                       "OW_AUTH_SECRET": secrets.token_hex(32), "OW_PROVIDER_MODE": "disabled"}
        result = subprocess.run([sys.executable, "-m", "uvicorn", "knowledge.main:app", "--port", "0"],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30)
        assert result.returncode != 0 and "Foundation schema missing" in result.stderr
        assert database.query("SELECT tablename FROM pg_tables WHERE schemaname='public'") == []


def test_revoked_identity_is_rechecked(application):
    database, token = application.database, application.tokens["bob"]
    try:
        database.execute("UPDATE knowledge_users SET is_active=false WHERE username='bob'")
        assert application.server.request("GET", "/auth/me", token=token).status_code == 401
        assert application.server.request("GET", "/conversations", token=token).status_code == 401
    finally:
        database.execute("UPDATE knowledge_users SET is_active=true WHERE username='bob'")


@pytest.mark.parametrize("path", ["/research/search", "/personal-wiki/organize", "/answer-runs", "/retrieval/search", "/index-jobs"])
def test_unimplemented_and_removed_endpoints_do_not_succeed(application, path):
    assert application.server.request("POST", path, token=application.tokens["alice"], json={}).status_code == 404


def test_runtime_does_not_import_optional_features_or_model_clients(application):
    program = '''import sys
from knowledge.main import app
from knowledge.registry import load_entities
from knowledge.core.database import Base
load_entities()
assert set(Base.metadata.tables) == {"knowledge_users", "conversations", "messages"}
for prefix in ("knowledge.personal_wiki", "knowledge.research", "knowledge.answers", "knowledge.rag", "knowledge.jobs", "knowledge.integrations"):
    assert not any(name == prefix or name.startswith(prefix + ".") for name in sys.modules), prefix
'''
    result = subprocess.run([sys.executable, "-c", program], cwd=ROOT, env=application.environment,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr
    paths = application.server.client.get("/openapi.json").json()["paths"]
    assert set(paths) == {"/api/v1/health", "/api/v1/auth/login", "/api/v1/auth/me",
                         "/api/v1/conversations", "/api/v1/conversations/{conversation_id}",
                         "/api/v1/conversations/{conversation_id}/messages"}
