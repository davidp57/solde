"""Unit tests for the settings service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.settings import AppSettingsUpdate
from backend.services.settings import get_settings, update_settings


class TestGetSettings:
    async def test_returns_defaults_when_no_row_exists(self, db_session: AsyncSession):
        settings = await get_settings(db_session)

        assert settings.id == 1
        assert settings.association_name == "Mon Association"
        assert settings.fiscal_year_start_month == 8
        assert settings.smtp_host is None
        assert settings.smtp_port == 587
        assert settings.smtp_use_tls is True

    async def test_creates_row_on_first_call(self, db_session: AsyncSession):
        await get_settings(db_session)
        # Second call should return the same row, not create a duplicate
        settings = await get_settings(db_session)
        assert settings.id == 1

    async def test_returns_persisted_values(self, db_session: AsyncSession):
        settings = await get_settings(db_session)
        settings.association_name = "Test Asso"
        await db_session.commit()

        reloaded = await get_settings(db_session)
        assert reloaded.association_name == "Test Asso"


class TestUpdateSettings:
    async def test_partial_update_association_name(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(association_name="Nouvelle Asso")
        settings = await update_settings(db_session, payload)

        assert settings.association_name == "Nouvelle Asso"
        # Other fields unchanged
        assert settings.fiscal_year_start_month == 8

    async def test_update_smtp_fields(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(
            smtp_host="smtp.example.com",
            smtp_port=465,
            smtp_user="user@example.com",
            smtp_password="secret",
            smtp_from_email="noreply@example.com",
            smtp_use_tls=False,
        )
        settings = await update_settings(db_session, payload)

        assert settings.smtp_host == "smtp.example.com"
        assert settings.smtp_port == 465
        assert settings.smtp_user == "user@example.com"
        assert settings.smtp_from_email == "noreply@example.com"
        assert settings.smtp_use_tls is False

    async def test_update_fiscal_year_start_month(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(fiscal_year_start_month=1)
        settings = await update_settings(db_session, payload)
        assert settings.fiscal_year_start_month == 1

    async def test_excludes_unset_fields(self, db_session: AsyncSession):
        # Set initial state
        await update_settings(
            db_session, AppSettingsUpdate(association_name="Asso A", smtp_port=465)
        )

        # Update only one field — the other must remain unchanged
        settings = await update_settings(db_session, AppSettingsUpdate(association_name="Asso B"))
        assert settings.association_name == "Asso B"
        assert settings.smtp_port == 465

    async def test_creates_row_if_not_exists(self, db_session: AsyncSession):
        payload = AppSettingsUpdate(association_name="Nouvelle Asso")
        settings = await update_settings(db_session, payload)
        assert settings.id == 1
