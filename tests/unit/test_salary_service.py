"""Unit tests for salary service."""

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.contact import Contact, ContactType
from backend.schemas.salary import SalaryCreate


async def _make_employee(db: AsyncSession, nom: str = "Dupont", prenom: str = "Jean") -> Contact:
    c = Contact(type=ContactType.CLIENT, nom=nom, prenom=prenom)
    db.add(c)
    await db.flush()
    return c


@pytest.mark.asyncio
async def test_create_salary_minimal(db_session: AsyncSession) -> None:
    """Creating a salary with minimal data persists correctly."""
    from backend.services.salary_service import create_salary

    employee = await _make_employee(db_session)
    payload = SalaryCreate(
        employee_id=employee.id,
        month="2025-01",
        hours=Decimal("151.67"),
        gross=Decimal("1800.00"),
        employee_charges=Decimal("252.00"),
        employer_charges=Decimal("756.00"),
        tax=Decimal("90.00"),
        net_pay=Decimal("1458.00"),
    )
    salary = await create_salary(db_session, payload)

    assert salary.id is not None
    assert salary.month == "2025-01"
    assert salary.gross == Decimal("1800.00")
    assert salary.net_pay == Decimal("1458.00")


@pytest.mark.asyncio
async def test_salary_total_cost_property(db_session: AsyncSession) -> None:
    """total_cost = gross + employer_charges."""
    from backend.services.salary_service import create_salary

    employee = await _make_employee(db_session, "Martin", "Sophie")
    payload = SalaryCreate(
        employee_id=employee.id,
        month="2025-02",
        hours=Decimal("100.00"),
        gross=Decimal("2000.00"),
        employee_charges=Decimal("280.00"),
        employer_charges=Decimal("840.00"),
        tax=Decimal("100.00"),
        net_pay=Decimal("1620.00"),
    )
    salary = await create_salary(db_session, payload)

    assert salary.total_cost == Decimal("2840.00")


@pytest.mark.asyncio
async def test_list_salaries_empty(db_session: AsyncSession) -> None:
    """Listing salaries returns empty list when none exist."""
    from backend.services.salary_service import list_salaries

    result = await list_salaries(db_session)
    assert result == []


@pytest.mark.asyncio
async def test_list_salaries_filter_by_employee(db_session: AsyncSession) -> None:
    """list_salaries can filter by employee_id."""
    from backend.services.salary_service import create_salary, list_salaries

    emp1 = await _make_employee(db_session, "Dupont", "Paul")
    emp2 = await _make_employee(db_session, "Durand", "Marie")

    for emp in [emp1, emp2]:
        payload = SalaryCreate(
            employee_id=emp.id,
            month="2025-03",
            hours=Decimal("151.67"),
            gross=Decimal("1500.00"),
            employee_charges=Decimal("200.00"),
            employer_charges=Decimal("600.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("1300.00"),
        )
        await create_salary(db_session, payload)

    result = await list_salaries(db_session, employee_id=emp1.id)
    assert len(result) == 1
    assert result[0].employee_id == emp1.id


@pytest.mark.asyncio
async def test_list_salaries_filter_by_month_range(db_session: AsyncSession) -> None:
    """list_salaries can filter salaries to a fiscal-year month range."""
    from backend.services.salary_service import create_salary, list_salaries

    employee = await _make_employee(db_session, "Dupont", "Paul")

    for month in ["2024-07", "2024-08", "2025-07", "2025-08"]:
        payload = SalaryCreate(
            employee_id=employee.id,
            month=month,
            hours=Decimal("151.67"),
            gross=Decimal("1500.00"),
            employee_charges=Decimal("200.00"),
            employer_charges=Decimal("600.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("1300.00"),
        )
        await create_salary(db_session, payload)

    result = await list_salaries(db_session, from_month="2024-08", to_month="2025-07")

    assert [salary.month for salary in result] == ["2025-07", "2024-08"]


@pytest.mark.asyncio
async def test_delete_salary(db_session: AsyncSession) -> None:
    """Deleting a salary removes it from the DB."""
    from backend.services.salary_service import create_salary, delete_salary, get_salary

    employee = await _make_employee(db_session)
    payload = SalaryCreate(
        employee_id=employee.id,
        month="2025-04",
        hours=Decimal("80.00"),
        gross=Decimal("1000.00"),
        employee_charges=Decimal("140.00"),
        employer_charges=Decimal("420.00"),
        tax=Decimal("0.00"),
        net_pay=Decimal("860.00"),
    )
    salary = await create_salary(db_session, payload)
    salary_id = salary.id

    await delete_salary(db_session, salary)

    assert await get_salary(db_session, salary_id) is None


@pytest.mark.asyncio
async def test_monthly_summary(db_session: AsyncSession) -> None:
    """get_monthly_summary aggregates correctly."""
    from backend.services.salary_service import create_salary, get_monthly_summary

    employee = await _make_employee(db_session)
    for _i in range(3):
        payload = SalaryCreate(
            employee_id=employee.id,
            month="2025-05",
            hours=Decimal("50.00"),
            gross=Decimal("1000.00"),
            employee_charges=Decimal("100.00"),
            employer_charges=Decimal("300.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("900.00"),
        )
        await create_salary(db_session, payload)

    rows = await get_monthly_summary(db_session)
    assert len(rows) >= 1
    may_row = next((r for r in rows if r.month == "2025-05"), None)
    assert may_row is not None
    assert may_row.count == 3
    assert Decimal(str(may_row.total_gross)) == Decimal("3000.00")


@pytest.mark.asyncio
async def test_monthly_summary_filter_by_month_range(db_session: AsyncSession) -> None:
    """get_monthly_summary can be limited to a fiscal-year month range."""
    from backend.services.salary_service import create_salary, get_monthly_summary

    employee = await _make_employee(db_session)
    for month in ["2024-07", "2024-08", "2025-07", "2025-08"]:
        payload = SalaryCreate(
            employee_id=employee.id,
            month=month,
            hours=Decimal("50.00"),
            gross=Decimal("1000.00"),
            employee_charges=Decimal("100.00"),
            employer_charges=Decimal("300.00"),
            tax=Decimal("10.00"),
            net_pay=Decimal("890.00"),
        )
        await create_salary(db_session, payload)

    rows = await get_monthly_summary(db_session, from_month="2024-08", to_month="2025-07")

    assert [row.month for row in rows] == ["2025-07", "2024-08"]


@pytest.mark.asyncio
async def test_month_validator_invalid(db_session: AsyncSession) -> None:
    """SalaryCreate raises on invalid month format."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SalaryCreate(
            employee_id=1,
            month="janvier 2025",
            hours=Decimal("100.00"),
            gross=Decimal("1000.00"),
            employee_charges=Decimal("100.00"),
            employer_charges=Decimal("300.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("900.00"),
        )


@pytest.mark.asyncio
async def test_list_salaries_filter_by_month(db_session: AsyncSession) -> None:
    """list_salaries can filter by exact month."""
    from backend.services.salary_service import create_salary, list_salaries

    employee = await _make_employee(db_session, "Dupont", "Paul")
    for m in ["2025-01", "2025-02"]:
        await create_salary(
            db_session,
            SalaryCreate(
                employee_id=employee.id,
                month=m,
                hours=Decimal("100.00"),
                gross=Decimal("1500.00"),
                employee_charges=Decimal("200.00"),
                employer_charges=Decimal("600.00"),
                tax=Decimal("0.00"),
                net_pay=Decimal("1300.00"),
            ),
        )

    result = await list_salaries(db_session, month="2025-01")
    assert len(result) == 1
    assert result[0].month == "2025-01"


@pytest.mark.asyncio
async def test_update_salary(db_session: AsyncSession) -> None:
    """update_salary modifies only provided fields."""
    from backend.schemas.salary import SalaryUpdate
    from backend.services.salary_service import create_salary, update_salary

    employee = await _make_employee(db_session, "Dupont", "Paul")
    salary = await create_salary(
        db_session,
        SalaryCreate(
            employee_id=employee.id,
            month="2025-03",
            hours=Decimal("100.00"),
            gross=Decimal("1500.00"),
            employee_charges=Decimal("200.00"),
            employer_charges=Decimal("600.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("1300.00"),
        ),
    )

    updated = await update_salary(
        db_session,
        salary,
        SalaryUpdate(gross=Decimal("2000.00"), net_pay=Decimal("1700.00")),
    )
    assert updated.gross == Decimal("2000.00")
    assert updated.net_pay == Decimal("1700.00")
    assert updated.hours == Decimal("100.00")  # unchanged


@pytest.mark.asyncio
async def test_employee_display_name() -> None:
    """_employee_display_name returns prenom + nom."""
    from backend.services.salary_service import _employee_display_name

    assert _employee_display_name(None) is None
    c = Contact(type=ContactType.CLIENT, nom="Dupont", prenom="Jean")
    assert _employee_display_name(c) == "Jean Dupont"
    c2 = Contact(type=ContactType.CLIENT, nom="Solo", prenom=None)
    assert _employee_display_name(c2) == "Solo"
