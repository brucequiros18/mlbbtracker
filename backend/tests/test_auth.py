"""App accounts: Google-only sign-in, profile setup and sessions.

Everything here is offline: the Google verifier is faked, so no token is ever
sent to Google. The real verifier (signature, issuer, audience, expiry) is
tested against a locally generated RSA key in `test_google_verifier`.
"""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.v1.deps import get_auth_service
from app.core.config import get_settings
from app.core.errors import GoogleTokenInvalidError
from app.core.security import hash_password, hash_token, verify_password
from app.db.base import Base
from app.db.models import User, UserSession
from app.integrations.google_auth import GoogleIdentity
from app.main import create_app
from app.services.auth_service import AuthService

GOOD_TOKEN = "good-google-token-" + "x" * 40
BAD_TOKEN = "bad-google-token-" + "x" * 40

IDENTITY = GoogleIdentity(
    subject="google-sub-1",
    email="ash@example.com",
    email_verified=True,
    name="Ash",
    picture="https://img.example/ash.png",
)


class FakeGoogleVerifier:
    def __init__(self) -> None:
        self.identity = IDENTITY
        self.calls = 0

    async def verify(self, credential: str) -> GoogleIdentity:
        self.calls += 1
        if credential != GOOD_TOKEN:
            raise GoogleTokenInvalidError("Google sign-in could not be verified.")
        return self.identity


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "MLBB_GOOGLE_CLIENT_ID", "test-client.apps.googleusercontent.com"
    )
    get_settings.cache_clear()
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    verifier = FakeGoogleVerifier()
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(
        get_settings(), factory, verifier=verifier
    )
    with TestClient(app) as client:
        yield client, factory, verifier
    get_settings.cache_clear()


def _sign_in(client) -> str:
    resp = client.post("/api/v1/auth/google", json={"credential": GOOD_TOKEN})
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["sessionToken"]


def _register(client, token: str, **overrides):
    body = {
        "username": "AshKetchum",
        "mlbbId": "123456789",
        "password": "correct horse battery",
    }
    body.update(overrides)
    return client.post(
        "/api/v1/auth/register",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )


# -- Configuration -----------------------------------------------------------


def test_config_reports_google_enabled(auth_client):
    client, _, _ = auth_client
    resp = client.get("/api/v1/auth/config")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["googleSignInEnabled"] is True
    assert data["googleClientId"] == "test-client.apps.googleusercontent.com"
    assert data["minPasswordLength"] == 8


def test_unconfigured_server_says_so(tmp_path, monkeypatch):
    monkeypatch.delenv("MLBB_GOOGLE_CLIENT_ID", raising=False)
    get_settings.cache_clear()
    engine = create_engine(f"sqlite:///{tmp_path / 'nodb.db'}", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    app = create_app()
    app.dependency_overrides[get_auth_service] = lambda: AuthService(
        get_settings(), factory, verifier=None
    )
    with TestClient(app) as client:
        config = client.get("/api/v1/auth/config")
        assert config.status_code == 200
        assert config.json()["data"]["googleSignInEnabled"] is False
        assert config.json()["data"]["googleClientId"] is None

        resp = client.post("/api/v1/auth/google", json={"credential": GOOD_TOKEN})
        assert resp.status_code == 503
        assert resp.json()["code"] == "GOOGLE_NOT_CONFIGURED"
    get_settings.cache_clear()


# -- Google sign-in ----------------------------------------------------------


def test_google_sign_in_creates_account_without_profile(auth_client):
    client, _, _ = auth_client
    resp = client.post("/api/v1/auth/google", json={"credential": GOOD_TOKEN})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sessionToken"]
    assert data["isNewUser"] is True
    user = data["user"]
    assert user["email"] == "ash@example.com"
    assert user["googleName"] == "Ash"
    assert user["username"] is None
    assert user["mlbbId"] is None
    assert user["profileComplete"] is False
    # Never verified: the MLBB ID is typed in by the player.
    assert user["mlbbIdVerified"] is False


def test_google_sign_in_twice_reuses_the_account(auth_client):
    client, factory, verifier = auth_client
    first = client.post("/api/v1/auth/google", json={"credential": GOOD_TOKEN})
    second = client.post("/api/v1/auth/google", json={"credential": GOOD_TOKEN})
    assert first.json()["data"]["isNewUser"] is True
    assert second.json()["data"]["isNewUser"] is False
    assert first.json()["data"]["user"]["id"] == second.json()["data"]["user"]["id"]
    assert first.json()["data"]["sessionToken"] != second.json()["data"]["sessionToken"]
    assert verifier.calls == 2
    with factory() as session:
        assert len(session.scalars(select(User)).all()) == 1
        assert len(session.scalars(select(UserSession)).all()) == 2


def test_google_sign_in_rejects_invalid_token(auth_client):
    client, factory, _ = auth_client
    resp = client.post("/api/v1/auth/google", json={"credential": BAD_TOKEN})
    assert resp.status_code == 401
    assert resp.json()["code"] == "GOOGLE_TOKEN_INVALID"
    with factory() as session:
        assert session.scalars(select(User)).all() == []


# -- Registration ------------------------------------------------------------


def test_register_completes_the_profile(auth_client):
    client, factory, _ = auth_client
    token = _sign_in(client)
    resp = _register(client, token)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["username"] == "AshKetchum"
    assert data["mlbbId"] == "123456789"
    assert data["profileComplete"] is True
    assert data["mlbbIdVerified"] is False

    with factory() as session:
        user = session.scalar(select(User))
        assert user is not None
        # The password is hashed, never stored in plaintext.
        assert user.password_hash is not None
        assert "correct horse battery" not in user.password_hash
        assert user.password_hash.startswith("scrypt$")
        assert verify_password("correct horse battery", user.password_hash)


def test_register_requires_a_session(auth_client):
    client, _, _ = auth_client
    resp = client.post(
        "/api/v1/auth/register",
        json={
            "username": "AshKetchum",
            "mlbbId": "123456789",
            "password": "correct horse battery",
        },
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "AUTH_REQUIRED"


def test_register_rejects_duplicate_username_case_insensitively(auth_client):
    client, _, verifier = auth_client
    first = _sign_in(client)
    assert _register(client, first, username="AshKetchum").status_code == 200

    verifier.identity = GoogleIdentity(
        subject="google-sub-2",
        email="misty@example.com",
        email_verified=True,
        name="Misty",
        picture=None,
    )
    second = _sign_in(client)
    resp = _register(client, second, username="ashketchum")
    assert resp.status_code == 409
    assert resp.json()["code"] == "USERNAME_TAKEN"


def test_register_rejects_a_second_profile(auth_client):
    client, _, _ = auth_client
    token = _sign_in(client)
    assert _register(client, token).status_code == 200
    resp = _register(client, token, username="SomeoneElse")
    assert resp.status_code == 409
    assert resp.json()["code"] == "PROFILE_ALREADY_COMPLETE"


@pytest.mark.parametrize(
    "body",
    [
        {"username": "ab"},
        {"username": "has space"},
        {"username": "Ash-Ketchum"},
        {"mlbbId": "12ab"},
        {"mlbbId": "123"},
        {"password": "short"},
    ],
)
def test_register_validates_input(auth_client, body):
    client, _, _ = auth_client
    token = _sign_in(client)
    assert _register(client, token, **body).status_code == 422


# -- Session ----------------------------------------------------------------


def test_me_returns_the_account(auth_client):
    client, _, _ = auth_client
    token = _sign_in(client)
    resp = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "ash@example.com"
    assert resp.json()["meta"]["note"].startswith("MLBB ID is self-declared")


def test_me_rejects_unknown_and_expired_tokens(auth_client):
    client, factory, _ = auth_client
    unknown = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer nope"}
    )
    assert unknown.status_code == 401
    assert unknown.json()["code"] == "AUTH_REQUIRED"

    token = _sign_in(client)
    with factory() as session:
        row = session.scalar(select(UserSession))
        assert row is not None
        row.expires_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)
        session.commit()
    expired = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert expired.status_code == 401
    assert expired.json()["code"] == "AUTH_REQUIRED"


def test_logout_forgets_the_session(auth_client):
    client, factory, _ = auth_client
    token = _sign_in(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 200
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    with factory() as session:
        # Only the session row is gone; the account stays.
        assert session.scalars(select(UserSession)).all() == []
        assert len(session.scalars(select(User)).all()) == 1


# -- Profile edits -----------------------------------------------------------


def test_update_requires_the_app_password(auth_client):
    client, factory, _ = auth_client
    token = _sign_in(client)
    assert _register(client, token).status_code == 200

    wrong = client.patch(
        "/api/v1/auth/me",
        json={"username": "NewName", "currentPassword": "not my password"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert wrong.status_code == 403
    assert wrong.json()["code"] == "INVALID_PASSWORD"

    with factory() as session:
        assert session.scalar(select(User)).username == "AshKetchum"


def test_update_changes_profile_and_password(auth_client):
    client, factory, _ = auth_client
    token = _sign_in(client)
    assert _register(client, token).status_code == 200

    resp = client.patch(
        "/api/v1/auth/me",
        json={
            "username": "AshMaster",
            "mlbbId": "987654321",
            "currentPassword": "correct horse battery",
            "newPassword": "a brand new passphrase",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["username"] == "AshMaster"
    assert data["mlbbId"] == "987654321"

    with factory() as session:
        user = session.scalar(select(User))
        assert verify_password("a brand new passphrase", user.password_hash)
        assert not verify_password("correct horse battery", user.password_hash)


# -- Security primitives -----------------------------------------------------


def test_password_hashing_roundtrip():
    encoded = hash_password("s3cret passphrase")
    assert encoded.startswith("scrypt$")
    assert verify_password("s3cret passphrase", encoded)
    assert not verify_password("S3cret passphrase", encoded)
    assert not verify_password("", encoded)
    assert not verify_password("s3cret passphrase", None)
    assert not verify_password("s3cret passphrase", "not-a-hash")
    assert not verify_password("s3cret passphrase", "scrypt$x$y$z$a$b")


def test_hashes_are_salted():
    assert hash_password("same password") != hash_password("same password")


def test_session_tokens_are_not_stored_raw(auth_client):
    client, factory, _ = auth_client
    token = _sign_in(client)
    with factory() as session:
        row = session.scalar(select(UserSession))
        assert row is not None
        assert row.token_hash == hash_token(token)
        assert row.token_hash != token
