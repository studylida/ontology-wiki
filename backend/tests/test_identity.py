import pytest

from knowledge.core.errors import AppError
from knowledge.identity.entities import User
from knowledge.identity.service import IdentityService
from knowledge.identity.security import hash_password, verify_password


def test_password_hash_is_salted_and_never_equals_plaintext():
    first, second = hash_password("private-value"), hash_password("private-value")
    assert first != second
    assert verify_password("private-value", first)
    assert not verify_password("wrong", first)
    assert not verify_password("private-value", "malformed")


@pytest.mark.asyncio
async def test_service_account_has_only_explicit_scopes(seed_user):
    service = await seed_user("limited-service", kind="service", role="admin", permissions=["ontology:read"])
    assert service.permissions == {"ontology:read"}
    with pytest.raises(AppError) as error:
        service.require("rag:answer")
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_token_revocation_is_checked_against_database(sessions, settings, principal):
    identity = IdentityService(sessions, settings)
    login = await identity.login("test-user", "test-only-password")
    assert (await identity.authenticate(login["accessToken"])).id == principal.id
    async with sessions() as session, session.begin():
        user = await session.get(User, principal.id)
        user.token_version += 1
    with pytest.raises(AppError) as error:
        await identity.authenticate(login["accessToken"])
    assert error.value.code == "IDENTITY_REVOKED"


@pytest.mark.asyncio
async def test_login_failure_does_not_echo_password(client, principal):
    response = await client.post("/api/v1/auth/login", json={"username": "test-user", "password": "sensitive-wrong-secret"})
    assert response.status_code == 401
    assert "sensitive-wrong-secret" not in response.text
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
