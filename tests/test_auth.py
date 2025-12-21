import os
import pytest
from app import app, db
from models import User, RefreshToken
from flask_jwt_extended import decode_token
from unittest.mock import patch

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_SECRET_KEY'] = 'test-secret'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def test_register_success(client):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User",
        "birthdate": "2000-01-01"
    }
    res = client.post("/api/auth/register", json=data)
    assert res.status_code == 201
    assert "user_id" in res.json
    user = User.query.filter_by(username="testuser").first()
    assert user is not None
    assert user.id == res.json["user_id"]  # UUID string


def test_register_duplicate_username(client):
    user = User(id="123e4567-e89b-12d3-a456-426614174000", username="testuser", email="other@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    res = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "new@example.com",
        "password": "password123"
    })
    assert res.status_code == 400
    assert "Username already exists" in res.json["msg"]


def test_register_invalid_birthdate(client):
    res = client.post("/api/auth/register", json={
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password123",
        "birthdate": "01-01-2000"
    })
    assert res.status_code == 400
    assert "Invalid birthdate format" in res.json["msg"]


def test_login_success(client):
    user = User(id="123e4567-e89b-12d3-a456-426614174001", username="loginuser", email="login@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    res = client.post("/api/auth/login", json={
        "username": "loginuser",
        "password": "password123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json
    token = res.json["access_token"]
    decoded = decode_token(token)
    assert decoded["sub"] == user.id  # UUID string

    # Check that refresh token was stored
    refresh = RefreshToken.query.filter_by(user_id=user.id).first()
    assert refresh is not None


def test_login_bad_credentials(client):
    res = client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": "wrongpass"
    })
    assert res.status_code == 401
    assert "Bad credentials" in res.json["msg"]


def test_me_route(client):
    user = User(id="123e4567-e89b-12d3-a456-426614174002", username="meuser", email="me@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Get JWT
    login_res = client.post("/api/auth/login", json={
        "username": "meuser",
        "password": "password123"
    })
    token = login_res.json["access_token"]

    # Access protected route
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json["username"] == "meuser"


# Mock Google OAuth for testing
@patch("app.google.authorize_redirect")
def test_google_login_redirect(mock_redirect, client):
    mock_redirect.return_value = b"redirected"
    res = client.get("/api/auth/google/login")
    assert res.data == b"redirected"


@patch("app.google.authorize_access_token")
@patch("app.google.parse_id_token")
def test_google_auth_new_user(mock_parse, mock_token, client):
    mock_token.return_value = {"access_token": "fake-token"}
    mock_parse.return_value = {"email": "google@example.com", "name": "Google User", "sub": "google-uuid"}

    res = client.get("/api/auth/google/auth")
    assert res.status_code == 200
    assert "access_token" in res.json
    user = User.query.filter_by(email="google@example.com").first()
    assert user is not None
    assert user.is_oauth is True
    assert user.google_id == "google-uuid"
