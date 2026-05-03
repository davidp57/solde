"""Integration tests for GET /api/help/manual and GET /api/help/changelog."""

from pathlib import Path
from unittest.mock import patch

from httpx import AsyncClient


class TestGetHelpManual:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/help/manual")
        assert response.status_code == 401

    async def test_returns_markdown_text(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/help/manual", headers=auth_headers)
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    async def test_returns_404_when_file_missing(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        with patch("backend.routers.chat._MANUEL_PATH", Path("/nonexistent/manuel.md")):
            response = await client.get("/api/help/manual", headers=auth_headers)
        assert response.status_code == 404


class TestGetHelpChangelog:
    async def test_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/help/changelog")
        assert response.status_code == 401

    async def test_any_authenticated_role_can_access(
        self,
        client: AsyncClient,
        auth_headers: dict,
        readonly_auth_headers: dict,
        secretaire_auth_headers: dict,
        tresorier_auth_headers: dict,
    ) -> None:
        for headers in (
            auth_headers,
            readonly_auth_headers,
            secretaire_auth_headers,
            tresorier_auth_headers,
        ):
            response = await client.get("/api/help/changelog", headers=headers)
            assert response.status_code == 200

    async def test_returns_plain_text(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/help/changelog", headers=auth_headers)
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    async def test_returns_markdown_content(self, client: AsyncClient, auth_headers: dict) -> None:
        response = await client.get("/api/help/changelog", headers=auth_headers)
        assert response.status_code == 200
        # The changelog-user.md file contains version headings
        assert "##" in response.text or "Version" in response.text

    async def test_returns_404_when_file_missing(
        self, client: AsyncClient, auth_headers: dict
    ) -> None:
        with patch(
            "backend.routers.chat._CHANGELOG_USER_PATH",
            Path("/nonexistent/changelog-user.md"),
        ):
            response = await client.get("/api/help/changelog", headers=auth_headers)
        assert response.status_code == 404
