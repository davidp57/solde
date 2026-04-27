"""Integration tests for the contacts API."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType


class TestListContacts:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.get("/api/contacts/")
        assert response.status_code == 401

    async def test_returns_empty_list(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/contacts/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_created_contacts(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Dupont"},
            headers=auth_headers,
        )
        response = await client.get("/api/contacts/", headers=auth_headers)
        assert len(response.json()) == 1

    async def test_filter_by_type(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Client"},
            headers=auth_headers,
        )
        await client.post(
            "/api/contacts/",
            json={"type": "fournisseur", "nom": "Fournisseur"},
            headers=auth_headers,
        )
        response = await client.get("/api/contacts/?type=client", headers=auth_headers)
        data = response.json()
        assert len(data) == 1
        assert data[0]["nom"] == "Client"

    async def test_search_by_name(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Dupont"},
            headers=auth_headers,
        )
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Martin"},
            headers=auth_headers,
        )
        response = await client.get("/api/contacts/?search=dup", headers=auth_headers)
        assert len(response.json()) == 1

    async def test_default_limit_is_100(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        db_session.add_all(
            [Contact(type=ContactType.CLIENT, nom=f"Client {index:03d}") for index in range(101)]
        )
        await db_session.commit()

        response = await client.get("/api/contacts/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 100

    async def test_limit_param_is_capped_at_1000(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
    ):
        response = await client.get("/api/contacts/?limit=1001", headers=auth_headers)
        assert response.status_code == 422

    async def test_readonly_user_cannot_list_contacts(
        self, client: AsyncClient, readonly_auth_headers: dict
    ):
        response = await client.get("/api/contacts/", headers=readonly_auth_headers)
        assert response.status_code == 403


class TestCreateContact:
    async def test_creates_contact(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Dupont", "prenom": "Jean"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nom"] == "Dupont"
        assert data["id"] is not None
        assert data["is_active"] is True

    async def test_requires_nom(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_requires_auth(self, client: AsyncClient):
        response = await client.post("/api/contacts/", json={"type": "client", "nom": "Test"})
        assert response.status_code == 401

    async def test_readonly_user_cannot_create(
        self, client: AsyncClient, db_session, auth_headers: dict
    ):
        from backend.models.user import User, UserRole
        from backend.services.auth import hash_password

        ro_user = User(
            username="readonly",
            email="ro@test.com",
            password_hash=hash_password("pass1234567890"),
            role=UserRole.READONLY,
            is_active=True,
        )
        db_session.add(ro_user)
        await db_session.commit()

        login = await client.post(
            "/api/auth/login",
            data={"username": "readonly", "password": "pass1234567890"},
        )
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.post(
            "/api/contacts/", json={"type": "client", "nom": "Test"}, headers=headers
        )
        assert response.status_code == 403


class TestGetContact:
    async def test_returns_contact(self, client: AsyncClient, auth_headers: dict):
        created = await client.post(
            "/api/contacts/",
            json={"type": "fournisseur", "nom": "ACME"},
            headers=auth_headers,
        )
        contact_id = created.json()["id"]
        response = await client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["nom"] == "ACME"

    async def test_returns_404_for_unknown(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/contacts/99999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateContact:
    async def test_partial_update(self, client: AsyncClient, auth_headers: dict):
        created = await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Ancien"},
            headers=auth_headers,
        )
        contact_id = created.json()["id"]
        response = await client.put(
            f"/api/contacts/{contact_id}",
            json={"nom": "Nouveau"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["nom"] == "Nouveau"
        assert response.json()["type"] == "client"  # unchanged

    async def test_returns_404_for_unknown(self, client: AsyncClient, auth_headers: dict):
        response = await client.put("/api/contacts/99999", json={"nom": "X"}, headers=auth_headers)
        assert response.status_code == 404


class TestImportContactEmails:
    async def test_requires_auth(self, client: AsyncClient):
        response = await client.post("/api/contacts/import-emails", json=[])
        assert response.status_code == 401

    async def test_updates_contact_without_email(self, client: AsyncClient, auth_headers: dict):
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Dupont", "prenom": "Jean"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/contacts/import-emails",
            json=[{"nom": "Dupont Jean", "email": "jean@example.com"}],
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 1
        assert data["not_found"] == 0
        assert data["already_has_email"] == 0
        assert data["updated_indices"] == [0]
        assert data["not_found_indices"] == []
        assert data["already_has_email_indices"] == []

    async def test_not_found_returns_zero_updates(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/contacts/import-emails",
            json=[{"nom": "Inconnu Total", "email": "x@example.com"}],
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["not_found"] == 1
        assert response.json()["updated"] == 0
        assert response.json()["not_found_indices"] == [0]
        assert response.json()["updated_indices"] == []

    async def test_indices_reflect_row_positions(self, client: AsyncClient, auth_headers: dict):
        """Indices in the result must match the row positions in the input array."""
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Bertrand", "prenom": "Sophie"},
            headers=auth_headers,
        )
        await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "Martin", "prenom": "Luc", "email": "luc@example.com"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/contacts/import-emails",
            json=[
                {"nom": "Inconnu", "email": "x@example.com"},  # idx 0 → not_found
                {"nom": "Sophie Bertrand", "email": "s@example.com"},  # idx 1 → updated
                {"nom": "Martin Luc", "email": "luc2@example.com"},  # idx 2 → already_has_email
            ],
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["updated_indices"] == [1]
        assert data["not_found_indices"] == [0]
        assert data["already_has_email_indices"] == [2]

    async def test_empty_list_returns_zero(self, client: AsyncClient, auth_headers: dict):
        response = await client.post(
            "/api/contacts/import-emails",
            json=[],
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["rows_processed"] == 0


class TestDeleteContact:
    async def test_soft_delete(self, client: AsyncClient, auth_headers: dict):
        created = await client.post(
            "/api/contacts/",
            json={"type": "client", "nom": "À supprimer"},
            headers=auth_headers,
        )
        contact_id = created.json()["id"]
        response = await client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
        assert response.status_code == 204

        # Still accessible by id
        get_response = await client.get(f"/api/contacts/{contact_id}", headers=auth_headers)
        assert get_response.json()["is_active"] is False

        # Not in default list
        list_response = await client.get("/api/contacts/", headers=auth_headers)
        assert all(c["id"] != contact_id for c in list_response.json())

    async def test_returns_404_for_unknown(self, client: AsyncClient, auth_headers: dict):
        response = await client.delete("/api/contacts/99999", headers=auth_headers)
        assert response.status_code == 404
