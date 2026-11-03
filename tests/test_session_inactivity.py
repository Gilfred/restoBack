import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_session
from app.models.user import User
from app.models.role import Role
from app.models.session import Session as UserSession
from app.core.security import get_password_hash, create_access_token
from app.core.config import settings
from app.services import auth_service
from app.db.base_class import Base

# Setup in-memory sqlite for integration session tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_session():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def create_test_user(db, email="test@example.com", password="password123", role_name="WAITER"):
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        role = Role(id=uuid4(), name=role_name, description="Role")
        db.add(role)
        db.commit()

    user = User(
        id=uuid4(),
        email=email,
        name="Test User",
        password=get_password_hash(password),
        isActive=True,
        roles=[role]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_login_creates_session_and_returns_tokens(client, db):
    user = create_test_user(db, email="login_test@example.com")

    response = client.post("/auth/login", json={
        "email": "login_test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert response.cookies.get("session_token") is not None
    assert response.cookies.get("refresh_token") is not None

    # Verify session in DB
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()
    assert session is not None
    assert session.isRevoked is False
    assert session.lastActivity is not None
    assert session.refreshTokenHash == auth_service.hash_refresh_token(data["refresh_token"])
    # Expiration absolue est dans 7 jours
    exp = session.expiresAt
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    assert exp > datetime.now(timezone.utc) + timedelta(days=6)

def test_authenticated_activity_updates_last_activity(client, db):
    user = create_test_user(db, email="activity_test@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "activity_test@example.com",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    # Artificially set lastActivity to 2 minutes ago (greater than 60s update interval)
    initial_activity = datetime.now(timezone.utc) - timedelta(minutes=2)
    session.lastActivity = initial_activity
    db.commit()

    # User accesses a protected resource
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    db.refresh(session)

    # Activity must be updated to recent time
    last_act = session.lastActivity
    if last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    assert last_act > initial_activity

def test_session_valid_under_30_minutes_inactivity(client, db):
    user = create_test_user(db, email="valid_inactivity@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "valid_inactivity@example.com",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    # Set last activity to 15 minutes ago (well below 30 minutes)
    session.lastActivity = datetime.now(timezone.utc) - timedelta(minutes=15)
    db.commit()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

def test_session_expired_after_30_minutes_inactivity(client, db):
    user = create_test_user(db, email="expired_inactivity@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "expired_inactivity@example.com",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    # Set last activity to 31 minutes ago
    session.lastActivity = datetime.now(timezone.utc) - timedelta(minutes=31)
    db.commit()

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 401
    assert "Session expirée pour inactivité" in response.json()["detail"]

def test_refresh_token_succeeds_when_active_and_does_not_update_last_activity(client, db):
    user = create_test_user(db, email="refresh_active@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "refresh_active@example.com",
        "password": "password123"
    })
    refresh_token = login_resp.json()["refresh_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    # Set last activity to 10 minutes ago
    fixed_activity = datetime.now(timezone.utc) - timedelta(minutes=10)
    session.lastActivity = fixed_activity
    db.commit()

    # Call /auth/refresh with refresh_token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    new_refresh_token = data["refresh_token"]
    assert new_refresh_token != refresh_token  # Rotation occurred

    db.refresh(session)
    # CRITICAL: refresh MUST NOT update lastActivity!
    last_act = session.lastActivity
    if last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    # The lastActivity timestamp should remain effectively unchanged (within 1 second)
    assert abs((last_act - fixed_activity).total_seconds()) < 2

def test_refresh_token_refused_when_inactive_over_30_minutes(client, db):
    user = create_test_user(db, email="refresh_inactive@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "refresh_inactive@example.com",
        "password": "password123"
    })
    refresh_token = login_resp.json()["refresh_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    # Inactive since 35 minutes
    session.lastActivity = datetime.now(timezone.utc) - timedelta(minutes=35)
    db.commit()

    # Even with automatic refresh attempts, session must be rejected!
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401
    assert "Session expirée pour inactivité" in response.json()["detail"]

def test_refresh_token_reuse_rejected(client, db):
    user = create_test_user(db, email="reuse_token@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "reuse_token@example.com",
        "password": "password123"
    })
    initial_refresh = login_resp.json()["refresh_token"]

    # First refresh: succeeds
    resp1 = client.post("/auth/refresh", json={"refresh_token": initial_refresh})
    assert resp1.status_code == 200
    rotated_refresh = resp1.json()["refresh_token"]

    # Attempt to reuse initial refresh token: MUST fail
    resp2 = client.post("/auth/refresh", json={"refresh_token": initial_refresh})
    assert resp2.status_code == 401

    # Using the new rotated token succeeds
    resp3 = client.post("/auth/refresh", json={"refresh_token": rotated_refresh})
    assert resp3.status_code == 200

def test_logout_revokes_session(client, db):
    user = create_test_user(db, email="logout_test@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "logout_test@example.com",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    refresh_token = login_resp.json()["refresh_token"]

    # Access works
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"}).status_code == 200

    # Logout
    logout_resp = client.post("/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
    assert logout_resp.status_code == 200

    # Access is now forbidden
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 401

    # Refresh is also forbidden
    refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401

def test_failed_login_does_not_affect_sessions(client, db):
    user = create_test_user(db, email="failed_login@example.com")
    # Bad credentials
    response = client.post("/auth/login", json={
        "email": "failed_login@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    sessions = db.query(UserSession).filter(UserSession.userId == user.id).all()
    assert len(sessions) == 0

def test_multiple_users_have_independent_sessions(client, db):
    user1 = create_test_user(db, email="user1@example.com")
    user2 = create_test_user(db, email="user2@example.com")

    # Login both users
    resp1 = client.post("/auth/login", json={"email": "user1@example.com", "password": "password123"})
    token1 = resp1.json()["access_token"]

    resp2 = client.post("/auth/login", json={"email": "user2@example.com", "password": "password123"})
    token2 = resp2.json()["access_token"]

    session1 = db.query(UserSession).filter(UserSession.userId == user1.id).first()
    session2 = db.query(UserSession).filter(UserSession.userId == user2.id).first()

    # Expire user1 session only
    session1.lastActivity = datetime.now(timezone.utc) - timedelta(minutes=40)
    db.commit()

    # User 1 is expired
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token1}"}).status_code == 401

    # User 2 is still active
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token2}"}).status_code == 200

def test_technical_request_does_not_update_activity(client, db):
    user = create_test_user(db, email="tech_req@example.com")
    login_resp = client.post("/auth/login", json={
        "email": "tech_req@example.com",
        "password": "password123"
    })
    access_token = login_resp.json()["access_token"]
    session = db.query(UserSession).filter(UserSession.userId == user.id).first()

    old_activity = datetime.now(timezone.utc) - timedelta(minutes=5)
    session.lastActivity = old_activity
    db.commit()

    # Technical request with header X-Technical-Request: true
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-Technical-Request": "true"
        }
    )
    assert response.status_code == 200
    db.refresh(session)
    last_act = session.lastActivity
    if last_act.tzinfo is None:
        last_act = last_act.replace(tzinfo=timezone.utc)
    assert abs((last_act - old_activity).total_seconds()) < 2
