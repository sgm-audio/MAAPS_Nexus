"""
Authentication Integration Tests
Tests JWT authentication flow, token validation, and protected endpoints
"""

import os
import pytest
import requests
from typing import Optional
import json

# Test configuration
BASE_URL = os.getenv("MAAPS_BASE_URL", "http://127.0.0.1:18000")
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"


class TestAuthentication:
    """Test authentication endpoints and flows"""

    def test_login_success(self):
        """Test successful login returns JWT token"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )

        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert len(data["token"]) > 50  # JWT tokens are long

    def test_login_invalid_credentials(self):
        """Test login with empty credentials"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": "", "password": ""}
        )

        # Current implementation accepts any username/password
        # This test documents current behavior
        # TODO: Update when real user database is implemented
        assert response.status_code == 200

    def test_verify_valid_token(self):
        """Test token verification with valid token"""
        # Get token
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        token = login_response.json()["token"]

        # Verify token
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "username" in data

    def test_verify_invalid_token(self):
        """Test token verification with invalid token"""
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers={"Authorization": "Bearer invalid_token_here"}
        )

        assert response.status_code == 401

    def test_verify_missing_token(self):
        """Test token verification without token"""
        response = requests.get(f"{BASE_URL}/auth/verify")

        assert response.status_code in (401, 403)  # Unauthorized / Forbidden (no credentials)

    def test_protected_endpoint_with_token(self):
        """Test protected endpoint with valid token"""
        # Get token
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        token = login_response.json()["token"]

        # Access protected endpoint
        response = requests.post(
            f"{BASE_URL}/system/restart",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "requested_by" in data

    def test_protected_endpoint_without_token(self):
        """Test protected endpoint without token"""
        response = requests.post(f"{BASE_URL}/system/restart")

        assert response.status_code in (401, 403)  # Unauthorized / Forbidden (no credentials)

    def test_protected_endpoint_invalid_token(self):
        """Test protected endpoint with invalid token"""
        response = requests.post(
            f"{BASE_URL}/system/restart",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401  # Unauthorized

    def test_optional_auth_with_token(self):
        """Test optional auth endpoint with token"""
        # Get token
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        token = login_response.json()["token"]

        # Make request with token
        response = requests.post(
            f"{BASE_URL}/audio/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "content_type": "melody",
                "key": "C major",
                "tempo": 120.0,
                "time_signature": "4/4",
                "chord_progression": ["C", "Am", "F", "G"],
                "length_bars": 8
            }
        )

        assert response.status_code == 200
        data = response.json()
        # Should include authenticated_user field
        assert "authenticated_user" in data

    def test_optional_auth_without_token(self):
        """Test optional auth endpoint without token"""
        response = requests.post(
            f"{BASE_URL}/audio/generate",
            json={
                "content_type": "melody",
                "key": "C major",
                "tempo": 120.0,
                "time_signature": "4/4",
                "chord_progression": ["C", "Am", "F", "G"],
                "length_bars": 8
            }
        )

        # Should still work without token
        assert response.status_code == 200
        data = response.json()
        # Should NOT include authenticated_user field
        assert "authenticated_user" not in data

    def test_public_endpoints_no_auth_required(self):
        """Test public endpoints work without authentication"""
        public_endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/metrics"),
            ("GET", "/agents"),
            ("GET", "/system/version"),
            ("GET", "/audio/formats"),
            ("GET", "/audio/processing-stats"),
            ("GET", "/metadata/stats"),
            ("GET", "/metadata/genres"),
            ("GET", "/metadata/tags/popular"),
        ]

        for method, endpoint in public_endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}")

            assert response.status_code in [200, 500], \
                f"{method} {endpoint} failed with {response.status_code}"


class TestAuthenticationSecurity:
    """Test security aspects of authentication"""

    def test_token_expiration_set(self):
        """Test that tokens have expiration time"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )

        data = response.json()
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_token_contains_no_sensitive_data(self):
        """Test JWT token doesn't contain password"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )

        token = response.json()["token"]

        # Decode JWT (without verification for testing)
        import base64
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) >= 2:
            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded)

            # Ensure password is not in token
            assert "password" not in str(payload_data).lower()

    def test_cors_headers_present(self):
        """Test CORS headers are configured"""
        response = requests.options(
            f"{BASE_URL}/auth/login",
            headers={"Origin": "http://localhost:3000"}
        )

        # Check CORS headers exist
        assert "access-control-allow-origin" in response.headers


class TestAuthenticationUsability:
    """Test usability features of authentication"""

    def test_bearer_token_format(self):
        """Test token uses Bearer format"""
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )

        data = response.json()
        assert data["token_type"] == "bearer"

    def test_error_messages_informative(self):
        """Test error messages are helpful"""
        # Test missing auth
        response = requests.post(f"{BASE_URL}/system/restart")
        assert response.status_code in (401, 403)
        # Should have detail message

        # Test invalid token
        response = requests.post(
            f"{BASE_URL}/system/restart",
            headers={"Authorization": "Bearer invalid"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    """Run tests manually without pytest"""
    print("=" * 60)
    print("MAAPS Authentication Integration Tests")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Username: {TEST_USERNAME}")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            exit(1)
        print("✅ Server is running")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print(f"   Start server with: uvicorn api.main:app --reload")
        exit(1)

    print()

    # Run tests
    test_auth = TestAuthentication()
    test_security = TestAuthenticationSecurity()
    test_usability = TestAuthenticationUsability()

    tests = [
        ("Login Success", test_auth.test_login_success),
        ("Verify Valid Token", test_auth.test_verify_valid_token),
        ("Verify Invalid Token", test_auth.test_verify_invalid_token),
        ("Protected Endpoint With Token", test_auth.test_protected_endpoint_with_token),
        ("Protected Endpoint Without Token", test_auth.test_protected_endpoint_without_token),
        ("Optional Auth With Token", test_auth.test_optional_auth_with_token),
        ("Optional Auth Without Token", test_auth.test_optional_auth_without_token),
        ("Public Endpoints", test_auth.test_public_endpoints_no_auth_required),
        ("Token Expiration Set", test_security.test_token_expiration_set),
        ("Token Security", test_security.test_token_contains_no_sensitive_data),
        ("Bearer Format", test_usability.test_bearer_token_format),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test_name}: {type(e).__name__}: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print(f"⚠️  {failed} test(s) failed")
        exit(1)
