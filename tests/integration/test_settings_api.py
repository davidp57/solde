"""Integration tests for GET/PUT /api/settings."""

from httpx import AsyncClient


class TestGetSettings:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/settings/")
        assert response.status_code == 401

    async def test_requires_admin_role(self, client: AsyncClient, auth_headers: dict):
        # auth_headers fixture uses an ADMIN user, so this should succeed
        response = await client.get("/api/settings/", headers=auth_headers)
        assert response.status_code == 200

    async def test_returns_default_settings(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()

        assert data["association_name"] == "Mon Association"
        assert data["fiscal_year_start_month"] == 8
        assert data["smtp_host"] is None
        assert data["smtp_port"] == 587
        assert data["smtp_use_tls"] is True

    async def test_does_not_expose_smtp_password(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()
        assert "smtp_password" not in data


class TestUpdateSettings:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.put("/api/settings/", json={"association_name": "X"})
        assert response.status_code == 401

    async def test_update_association_name(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.put(
            "/api/settings/",
            json={"association_name": "Soutien Scolaire Test"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["association_name"] == "Soutien Scolaire Test"

    async def test_update_persists(self, client: AsyncClient, auth_headers: dict):
        await client.put(
            "/api/settings/",
            json={"association_name": "Asso Persistée"},
            headers=auth_headers,
        )
        response = await client.get("/api/settings/", headers=auth_headers)
        assert response.json()["association_name"] == "Asso Persistée"

    async def test_partial_update_preserves_other_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        # First update
        await client.put(
            "/api/settings/",
            json={"fiscal_year_start_month": 9, "association_name": "Asso Testing"},
            headers=auth_headers,
        )
        # Second partial update — only one field
        await client.put(
            "/api/settings/",
            json={"association_name": "Asso Updated"},
            headers=auth_headers,
        )
        response = await client.get("/api/settings/", headers=auth_headers)
        data = response.json()
        assert data["association_name"] == "Asso Updated"
        assert data["fiscal_year_start_month"] == 9  # unchanged

    async def test_invalid_fiscal_year_month(
        self, client: AsyncClient, auth_headers: dict
    ):
        response = await client.put(
            "/api/settings/",
            json={"fiscal_year_start_month": 13},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_invalid_smtp_port(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={"smtp_port": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_update_smtp_settings(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/settings/",
            json={
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_user": "test@gmail.com",
                "smtp_from_email": "noreply@test.com",
                "smtp_use_tls": True,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["smtp_host"] == "smtp.gmail.com"
        assert data["smtp_user"] == "test@gmail.com"


class TestNonAdminAccess:
    async def test_tresorier_cannot_access_settings(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        tresorier = User(
            username="tresorier",
            email="tresorier@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TRESORIER,
            is_active=True,
        )
        db_session.add(tresorier)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "tresorier", "password": "password123"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.get("/api/settings/", headers=headers)
        assert response.status_code == 403
