# backend/tests/test_auth.py
"""Tests for authentication endpoints"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User


class TestAuth:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful user registration"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/register/",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["balance"] == settings.START_BALANCE
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, test_user: User):
        """Test registration with duplicate email"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/register/",
            json={
                "email": "test@example.com",
                "username": "anotheruser",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user: User):
        """Test registration with duplicate username"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/register/",
            json={
                "email": "another@example.com",
                "username": "testuser",
                "password": "password123"
            }
        )
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        """Test registration with short password"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/register/",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short"
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user: User):
        """Test successful login"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/login/",
            json={
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, test_user: User):
        """Test login with wrong password"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/login/",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        response = await client.post(
            f"{settings.API_V1_PREFIX}/auth/login/",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, auth_headers: dict):
        """Test getting current user info"""
        response = await client.get(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth"""
        response = await client.get(f"{settings.API_V1_PREFIX}/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile(self, client, auth_headers: dict):
        """Test updating user profile"""
        response = await client.patch(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=auth_headers,
            json={
                "default_api_id": "99999",
                "language": "ru"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["default_api_id"] == "99999"
        assert data["language"] == "ru"

    @pytest.mark.asyncio
    async def test_update_profile_invalid_language(self, client, auth_headers: dict):
        """Test updating profile with invalid language"""
        response = await client.patch(
            f"{settings.API_V1_PREFIX}/auth/me",
            headers=auth_headers,
            json={"language": "invalid"}
        )
        assert response.status_code == 400
