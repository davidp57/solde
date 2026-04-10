"""Unit tests for the accounting accounts service."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.accounting_account import AccountType
from backend.schemas.accounting_account import (
    AccountingAccountCreate,
    AccountingAccountUpdate,
)
from backend.services.accounting_account import (
    create_account,
    get_account,
    get_account_by_number,
    list_accounts,
    seed_default_accounts,
    update_account,
)


class TestSeedDefaultAccounts:
    async def test_seeds_24_accounts(self, db_session: AsyncSession):
        inserted = await seed_default_accounts(db_session)
        assert inserted == 24

    async def test_idempotent_second_call(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        inserted = await seed_default_accounts(db_session)
        assert inserted == 0

    async def test_accounts_are_queryable_after_seed(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        assert len(accounts) == 24


class TestListAccounts:
    async def test_filter_by_type_produit(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        produits = await list_accounts(db_session, type=AccountType.PRODUIT)
        assert all(a.type == AccountType.PRODUIT for a in produits)
        assert len(produits) > 0

    async def test_filter_by_type_charge(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        charges = await list_accounts(db_session, type=AccountType.CHARGE)
        assert all(a.type == AccountType.CHARGE for a in charges)

    async def test_sorted_by_number(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        numbers = [a.number for a in accounts]
        assert numbers == sorted(numbers)

    async def test_excludes_inactive(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        account = accounts[0]
        await update_account(
            db_session, account, AccountingAccountUpdate(is_active=False)
        )
        active = await list_accounts(db_session)
        assert len(active) == 23

    async def test_includes_inactive_when_requested(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        await update_account(
            db_session, accounts[0], AccountingAccountUpdate(is_active=False)
        )
        all_accounts = await list_accounts(db_session, active_only=False)
        assert len(all_accounts) == 24


class TestGetAccount:
    async def test_get_by_id(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        account = await get_account(db_session, accounts[0].id)
        assert account is not None
        assert account.id == accounts[0].id

    async def test_get_by_number(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        account = await get_account_by_number(db_session, "512100")
        assert account is not None
        assert account.label == "Compte courant"

    async def test_returns_none_for_unknown(self, db_session: AsyncSession):
        result = await get_account(db_session, 99999)
        assert result is None


class TestCreateAccount:
    async def test_creates_custom_account(self, db_session: AsyncSession):
        payload = AccountingAccountCreate(
            number="999999", label="Compte test", type=AccountType.CHARGE
        )
        account = await create_account(db_session, payload)
        assert account.id is not None
        assert account.is_default is False
        assert account.number == "999999"

    async def test_is_active_by_default(self, db_session: AsyncSession):
        payload = AccountingAccountCreate(
            number="888888", label="Test", type=AccountType.PRODUIT
        )
        account = await create_account(db_session, payload)
        assert account.is_active is True


class TestUpdateAccount:
    async def test_update_label(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        updated = await update_account(
            db_session, accounts[0], AccountingAccountUpdate(label="Nouveau libellé")
        )
        assert updated.label == "Nouveau libellé"

    async def test_deactivate_account(self, db_session: AsyncSession):
        await seed_default_accounts(db_session)
        accounts = await list_accounts(db_session)
        updated = await update_account(
            db_session, accounts[0], AccountingAccountUpdate(is_active=False)
        )
        assert updated.is_active is False
