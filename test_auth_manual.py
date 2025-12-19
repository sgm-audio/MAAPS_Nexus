#!/usr/bin/env python3
"""
Manual test script for authentication
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from api.user_db import UserDatabase


def test_authentication():
    """Test the authentication system"""
    print("Testing User Authentication System")
    print("=" * 50)

    db = UserDatabase()

    # Test 1: Password hashing
    print("\n1. Testing password hashing...")
    password = "test_password_123"
    hashed = db.hash_password(password)
    print(f"   Original: {password}")
    print(f"   Hashed: {hashed[:50]}...")
    assert hashed != password, "Password should be hashed"
    assert db.verify_password(password, hashed), "Should verify correct password"
    assert not db.verify_password("wrong", hashed), "Should reject wrong password"
    print("   ✓ Password hashing works correctly")

    # Test 2: Default users
    print("\n2. Testing default users...")
    assert db.user_exists("admin"), "Admin user should exist"
    assert db.user_exists("demo"), "Demo user should exist"
    print(f"   ✓ Found {db.get_user_count()} users in database")

    # Test 3: Authentication with valid credentials
    print("\n3. Testing authentication with valid credentials...")
    user = db.authenticate("admin", "admin123")
    assert user is not None, "Should authenticate valid credentials"
    assert user.username == "admin", "Should return correct user"
    print("   ✓ Admin login successful")

    user = db.authenticate("demo", "demo123")
    assert user is not None, "Should authenticate demo user"
    print("   ✓ Demo login successful")

    # Test 4: Authentication with invalid credentials
    print("\n4. Testing authentication with invalid credentials...")
    user = db.authenticate("admin", "wrongpassword")
    assert user is None, "Should reject invalid password"
    print("   ✓ Correctly rejected wrong password")

    user = db.authenticate("nonexistent", "password")
    assert user is None, "Should reject non-existent user"
    print("   ✓ Correctly rejected non-existent user")

    # Test 5: Creating new user
    print("\n5. Testing user creation...")
    new_user = db.create_user("testuser", "testpass123", "test@example.com")
    assert new_user.username == "testuser", "User should be created"
    assert db.user_exists("testuser"), "User should exist in database"
    print("   ✓ New user created successfully")

    # Test 6: Authenticate new user
    print("\n6. Testing new user authentication...")
    user = db.authenticate("testuser", "testpass123")
    assert user is not None, "Should authenticate new user"
    assert user.email == "test@example.com", "User data should be correct"
    print("   ✓ New user authenticated successfully")

    # Test 7: Duplicate user prevention
    print("\n7. Testing duplicate user prevention...")
    try:
        db.create_user("testuser", "anotherpass")
        assert False, "Should not allow duplicate username"
    except ValueError as e:
        print(f"   ✓ Correctly prevented duplicate: {e}")

    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


if __name__ == "__main__":
    try:
        test_authentication()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
