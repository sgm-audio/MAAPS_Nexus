"""
Tests for authentication module
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.user_db import UserDatabase, pwd_context


def test_password_hashing():
    """Test password hashing functionality"""
    db = UserDatabase()

    password = "test_password_123"
    hashed = db.hash_password(password)

    # Hash should be different from plain text
    assert hashed != password

    # Should be able to verify correct password
    assert db.verify_password(password, hashed)

    # Should reject incorrect password
    assert not db.verify_password("wrong_password", hashed)


def test_user_creation():
    """Test user creation"""
    db = UserDatabase()

    # Create a new user
    user = db.create_user("testuser", "testpass", "test@example.com")

    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password != "testpass"  # Should be hashed

    # User should exist in database
    assert db.user_exists("testuser")

    # Should not allow duplicate username
    with pytest.raises(ValueError):
        db.create_user("testuser", "anotherpass")


def test_user_authentication():
    """Test user authentication"""
    db = UserDatabase()

    # Create a test user
    db.create_user("authtest", "mypassword")

    # Valid credentials should authenticate
    user = db.authenticate("authtest", "mypassword")
    assert user is not None
    assert user.username == "authtest"

    # Invalid password should fail
    user = db.authenticate("authtest", "wrongpassword")
    assert user is None

    # Non-existent user should fail
    user = db.authenticate("nonexistent", "password")
    assert user is None


def test_default_users_debug_only(monkeypatch):
    """Default admin/demo users are seeded only when DEBUG=true"""
    monkeypatch.setenv("DEBUG", "true")
    db = UserDatabase()

    assert db.user_exists("admin")
    assert db.authenticate("admin", "admin123") is not None
    assert db.user_exists("demo")
    assert db.authenticate("demo", "demo123") is not None


def test_no_default_users_without_debug(monkeypatch):
    """Production (DEBUG unset/false) must not seed admin/demo"""
    monkeypatch.setenv("DEBUG", "false")
    db = UserDatabase()

    assert not db.user_exists("admin")
    assert not db.user_exists("demo")
    assert db.get_user_count() == 0


def test_get_user(monkeypatch):
    """Test getting user by username"""
    monkeypatch.setenv("DEBUG", "true")
    db = UserDatabase()

    user = db.get_user("admin")
    assert user is not None
    assert user.username == "admin"

    user = db.get_user("nonexistent")
    assert user is None


def test_user_count(monkeypatch):
    """Test user count with DEBUG seed"""
    monkeypatch.setenv("DEBUG", "true")
    db = UserDatabase()

    assert db.get_user_count() >= 2  # admin and demo users


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
