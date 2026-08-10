import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from app.main import app
from app.database import get_session
from app.models.user import User

@pytest.fixture
def client():
    return TestClient(app)

@patch("app.services.auth_service.get_user_by_email")
@patch("app.services.auth_service.create_password_reset_token")
@patch("app.services.email_service.send_password_reset_email")
def test_forgot_password_user_exists(mock_send_email, mock_create_token, mock_get_user, client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    # Mock user exists
    mock_user = User(
        id="123e4567-e89b-12d3-a456-426614174000",
        email="test@example.com",
        name="Test User",
        password="hashedpassword",
        isActive=True,
    )
    mock_get_user.return_value = mock_user
    mock_create_token.return_value = "mocked-token-123"

    # Call forgot-password endpoint
    response = client.post("/auth/forgot-password", json={"email": "test@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "If an account exists with this email, a reset link has been sent."

    mock_get_user.assert_called_once_with(db_mock, "test@example.com")
    mock_create_token.assert_called_once_with(db_mock, "test@example.com")
    mock_send_email.assert_called_once()
    assert "mocked-token-123" in mock_send_email.call_args[1]["reset_link"]

@patch("app.services.auth_service.get_user_by_email")
@patch("app.services.auth_service.create_password_reset_token")
@patch("app.services.email_service.send_password_reset_email")
def test_forgot_password_user_not_exists(mock_send_email, mock_create_token, mock_get_user, client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    # Mock user does not exist
    mock_get_user.return_value = None

    # Call forgot-password endpoint
    response = client.post("/auth/forgot-password", json={"email": "nonexistent@example.com"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "If an account exists with this email, a reset link has been sent."

    mock_get_user.assert_called_once_with(db_mock, "nonexistent@example.com")
    mock_create_token.assert_not_called()
    mock_send_email.assert_not_called()

@patch("app.services.auth_service.reset_password")
def test_reset_password_success(mock_reset_password, client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    mock_reset_password.return_value = True

    response = client.post("/auth/reset-password", json={"token": "valid-token", "new_password": "NewSecurePassword123!"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["message"] == "Password successfully reset"
    mock_reset_password.assert_called_once_with(db_mock, "valid-token", "NewSecurePassword123!")

@patch("app.services.auth_service.reset_password")
def test_reset_password_invalid_token(mock_reset_password, client):
    db_mock = MagicMock()
    app.dependency_overrides[get_session] = lambda: db_mock

    mock_reset_password.return_value = False

    response = client.post("/auth/reset-password", json={"token": "invalid-token", "new_password": "NewSecurePassword123!"})
    app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"
    mock_reset_password.assert_called_once_with(db_mock, "invalid-token", "NewSecurePassword123!")
