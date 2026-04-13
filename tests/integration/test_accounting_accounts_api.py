"""Integration tests for the accounting accounts API."""

from httpx import AsyncClient


class TestSeedAccounts:
    async def test_seed_inserts_40_accounts(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["inserted"] == 40

    async def test_seed_is_idempotent(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        response = await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        assert response.json()["inserted"] == 0

    async def test_requires_admin_or_tresorier(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        secretaire = User(
            username="secretaire",
            email="sec@test.com",
            password_hash=hash_password("pass1234567890"),
            role=UserRole.SECRETAIRE,
            is_active=True,
        )
        db_session.add(secretaire)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "secretaire", "password": "pass1234567890"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.post("/api/accounting/accounts/seed", headers=headers)
        assert response.status_code == 403


class TestListAccounts:
    async def test_returns_empty_before_seed(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/accounting/accounts/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_only_active_accounts_after_seed(
        self, client: AsyncClient, auth_headers: dict
    ):
        await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        response = await client.get("/api/accounting/accounts/", headers=auth_headers)
        assert len(response.json()) == 36

    async def test_can_include_inactive_accounts_after_seed(
        self, client: AsyncClient, auth_headers: dict
    ):
        await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        response = await client.get(
            "/api/accounting/accounts/?active_only=false", headers=auth_headers
        )
        data = response.json()
        assert len(data) == 40
        indexed = {account["number"]: account for account in data}
        assert indexed["401103"]["is_active"] is False
        assert indexed["416001"]["is_active"] is False

    async def test_filter_by_type(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/accounting/accounts/seed", headers=auth_headers)
        response = await client.get("/api/accounting/accounts/?type=produit", headers=auth_headers)
        data = response.json()
        assert all(a["type"] == "produit" for a in data)


class TestCreateAccount:
    async def test_creates_account(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/accounting/accounts/",
            json={"number": "999999", "label": "Compte test", "type": "charge"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["number"] == "999999"
        assert data["is_default"] is False

    async def test_rejects_duplicate_number(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/accounting/accounts/",
            json={"number": "999999", "label": "Premier", "type": "charge"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/accounting/accounts/",
            json={"number": "999999", "label": "Doublon", "type": "charge"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    async def test_rejects_non_digit_number(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/accounting/accounts/",
            json={"number": "ABC123", "label": "Test", "type": "charge"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestUpdateAccount:
    async def test_update_label(self, client: AsyncClient, auth_headers: dict):
        created = await client.post(
            "/api/accounting/accounts/",
            json={"number": "777777", "label": "Ancien libellé", "type": "actif"},
            headers=auth_headers,
        )
        account_id = created.json()["id"]
        response = await client.put(
            f"/api/accounting/accounts/{account_id}",
            json={"label": "Nouveau libellé"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Nouveau libellé"

    async def test_returns_404_for_unknown(self, client: AsyncClient, auth_headers: dict):
        response = await client.put(
            "/api/accounting/accounts/99999",
            json={"label": "X"},
            headers=auth_headers,
        )
        assert response.status_code == 404
