"""
User Database Module
Simple user management with password hashing

In production, this should be replaced with a proper database backend.
"""

from passlib.context import CryptContext
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User:
    """User model"""
    def __init__(self, username: str, hashed_password: str, email: Optional[str] = None):
        self.username = username
        self.hashed_password = hashed_password
        self.email = email


class UserDatabase:
    """
    Simple in-memory user database

    In production, replace this with a proper database backend
    like PostgreSQL, MySQL, or MongoDB.
    """

    def __init__(self):
        self.users: Dict[str, User] = {}
        self._initialize_default_users()

    def _initialize_default_users(self):
        """Initialize with some default users for testing"""
        # Default admin user
        self.create_user("admin", "admin123", "admin@example.com")

        # Default demo user
        self.create_user("demo", "demo123", "demo@example.com")

        logger.info(f"Initialized user database with {len(self.users)} default users")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def create_user(self, username: str, password: str, email: Optional[str] = None) -> User:
        """
        Create a new user

        Args:
            username: Username
            password: Plain text password (will be hashed)
            email: Optional email address

        Returns:
            User object

        Raises:
            ValueError: If username already exists
        """
        if username in self.users:
            raise ValueError(f"User '{username}' already exists")

        hashed_password = self.hash_password(password)
        user = User(username, hashed_password, email)
        self.users[username] = user

        logger.info(f"Created user: {username}")
        return user

    def get_user(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: Username

        Returns:
            User object or None if not found
        """
        return self.users.get(username)

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password

        Args:
            username: Username
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user(username)

        if user is None:
            logger.warning(f"Authentication failed: User '{username}' not found")
            return None

        if not self.verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            return None

        logger.info(f"Authentication successful: {username}")
        return user

    def user_exists(self, username: str) -> bool:
        """Check if user exists"""
        return username in self.users

    def get_user_count(self) -> int:
        """Get total number of users"""
        return len(self.users)


# Singleton instance
user_db = UserDatabase()
