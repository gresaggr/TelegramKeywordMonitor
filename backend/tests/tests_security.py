# backend/tests/test_security.py
"""Tests for security functions"""
import pytest
from jose import jwt
from datetime import datetime, timedelta, timezone

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash
)
from app.core.config import settings


class TestSecurity:
    """Test security utilities"""

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_password_hashing_long_password(self):
        """Test hashing very long password (bcrypt limit)"""
        password = "a" * 100  # Longer than 72 bytes
        hashed = get_password_hash(password)

        # Should still work due to truncation
        assert verify_password(password, hashed) is True

    def test_create_access_token(self):
        """Test JWT token creation"""
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert int(payload["sub"]) == user_id
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        """Test JWT token creation with custom expiry"""
        user_id = 123
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data={"sub": str(user_id)}, expires_delta=expires_delta)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Check expiry is approximately 30 minutes from now
        time_diff = (exp_time - now).total_seconds()
        assert 29 * 60 < time_diff < 31 * 60

    def test_token_expiry(self):
        """Test expired token"""
        user_id = 123
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data={"sub": str(user_id)}, expires_delta=expires_delta)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_invalid_token(self):
        """Test invalid token"""
        with pytest.raises(jwt.JWTError):
            jwt.decode("invalid.token.here", settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    def test_token_wrong_secret(self):
        """Test token with wrong secret"""
        user_id = 123
        token = create_access_token(data={"sub": str(user_id)})

        with pytest.raises(jwt.JWTError):
            jwt.decode(token, "wrong_secret", algorithms=[settings.ALGORITHM])
