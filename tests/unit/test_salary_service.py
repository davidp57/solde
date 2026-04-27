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


# ---------------------------------------------------------------------------
# get_previous_salary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_previous_salary_returns_most_recent(db_session: AsyncSession) -> None:
    """get_previous_salary returns the salary with the lexicographically latest month."""
    from backend.services.salary_service import create_salary, get_previous_salary

    employee = await _make_employee(db_session, "Durand", "Lucie")
    for month, gross in [("2025-01", Decimal("1500.00")), ("2025-03", Decimal("1600.00"))]:
        await create_salary(
            db_session,
            SalaryCreate(
                employee_id=employee.id,
                month=month,
                hours=Decimal("151.67"),
                gross=gross,
                employee_charges=Decimal("200.00"),
                employer_charges=Decimal("600.00"),
                tax=Decimal("0.00"),
                net_pay=Decimal("1300.00"),
            ),
        )

    result = await get_previous_salary(db_session, employee.id)
    assert result is not None
    assert result.employee_id == employee.id
    assert result.gross == Decimal("1600.00")  # most recent month (2025-03)


@pytest.mark.asyncio
async def test_get_previous_salary_returns_none_when_no_salary(db_session: AsyncSession) -> None:
    """get_previous_salary returns None when the employee has no salary."""
    from backend.services.salary_service import get_previous_salary

    employee = await _make_employee(db_session, "Absent", "Nobody")
    result = await get_previous_salary(db_session, employee.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_previous_salary_cdd_fields(db_session: AsyncSession) -> None:
    """get_previous_salary preserves brut_declared/conges_payes/precarite for CDD rows."""
    from backend.services.salary_service import create_salary, get_previous_salary

    employee = await _make_employee(db_session, "Martin", "Chloe")
    await create_salary(
        db_session,
        SalaryCreate(
            employee_id=employee.id,
            month="2025-06",
            hours=Decimal("8.00"),
            gross=Decimal("242.00"),
            employee_charges=Decimal("51.00"),
            employer_charges=Decimal("97.00"),
            tax=Decimal("0.00"),
            net_pay=Decimal("191.00"),
            brut_declared=Decimal("200.00"),
            conges_payes=Decimal("20.00"),
            precarite=Decimal("22.00"),
        ),
    )

    result = await get_previous_salary(db_session, employee.id)
    assert result is not None
    assert result.brut_declared == Decimal("200.00")
    assert result.conges_payes == Decimal("20.00")
    assert result.precarite == Decimal("22.00")


# ---------------------------------------------------------------------------
# get_workforce_cost
# ---------------------------------------------------------------------------


async def _make_contractor(
    db_session: AsyncSession, nom: str = "Prestataire", prenom: str = "AE"
) -> Contact:
    from backend.models.contact import ContactType

    c = Contact(type=ContactType.FOURNISSEUR, nom=nom, prenom=prenom, is_contractor=True)
    db_session.add(c)
    await db_session.flush()
    return c


_invoice_counter = 0


async def _make_ae_invoice(
    db_session: AsyncSession,
    contact_id: int,
    date_str: str,
    total: Decimal,
    hours: Decimal | None = None,
) -> None:
    import datetime

    from backend.models.invoice import Invoice, InvoiceStatus, InvoiceType

    global _invoice_counter
    _invoice_counter += 1
    inv = Invoice(
        number=f"AE-TEST-{_invoice_counter:04d}",
        type=InvoiceType.FOURNISSEUR,
        contact_id=contact_id,
        date=datetime.date.fromisoformat(date_str),
        total_amount=total,
        status=InvoiceStatus.PAID,
        hours=hours,
    )
    db_session.add(inv)
    await db_session.flush()


@pytest.mark.asyncio
async def test_get_workforce_cost_employee_salaries(db_session: AsyncSession) -> None:
    """get_workforce_cost returns CDI and CDD salary rows."""
    from backend.models.contact import ContractType
    from backend.services.salary_service import create_salary, get_workforce_cost

    cdi_emp = await _make_employee(db_session, "Legrand", "Paul")
    cdi_emp.contract_type = ContractType.CDI
    cdd_emp = await _make_employee(db_session, "Wolff", "Anna")
    cdd_emp.contract_type = ContractType.CDD
    await db_session.flush()

    for emp, gross in [(cdi_emp, Decimal("1800.00")), (cdd_emp, Decimal("242.00"))]:
        await create_salary(
            db_session,
            SalaryCreate(
                employee_id=emp.id,
                month="2025-04",
                hours=Decimal("151.67") if emp is cdi_emp else Decimal("8.00"),
                gross=gross,
                employee_charges=Decimal("200.00"),
                employer_charges=Decimal("600.00"),
                tax=Decimal("0.00"),
                net_pay=Decimal("1000.00"),
            ),
        )

    rows = await get_workforce_cost(db_session)
    assert len(rows) == 2
    types = {r.person_type for r in rows}
    assert types == {"CDI", "CDD"}


@pytest.mark.asyncio
async def test_get_workforce_cost_month_filter(db_session: AsyncSession) -> None:
    """get_workforce_cost respects from_month and to_month."""
    from backend.services.salary_service import create_salary, get_workforce_cost

    employee = await _make_employee(db_session, "Roux", "Elise")
    for month in ["2025-01", "2025-03", "2025-06"]:
        await create_salary(
            db_session,
            SalaryCreate(
                employee_id=employee.id,
                month=month,
                hours=Decimal("100.00"),
                gross=Decimal("1500.00"),
                employee_charges=Decimal("200.00"),
                employer_charges=Decimal("600.00"),
                tax=Decimal("0.00"),
                net_pay=Decimal("1300.00"),
            ),
        )

    rows = await get_workforce_cost(db_session, from_month="2025-02", to_month="2025-05")
    assert len(rows) == 1
    assert rows[0].month == "2025-03"


@pytest.mark.asyncio
async def test_get_workforce_cost_includes_ae_invoices(db_session: AsyncSession) -> None:
    """get_workforce_cost includes AE contractor invoices with hourly_cost when hours set."""
    from backend.services.salary_service import get_workforce_cost

    contractor = await _make_contractor(db_session, "Bernard", "Marc")
    await _make_ae_invoice(
        db_session,
        contact_id=contractor.id,
        date_str="2025-05-10",
        total=Decimal("300.00"),
        hours=Decimal("20.00"),
    )

    rows = await get_workforce_cost(db_session, from_month="2025-05", to_month="2025-05")
    ae_rows = [r for r in rows if r.person_type == "AE"]
    assert len(ae_rows) == 1
    assert ae_rows[0].total_cost == Decimal("300.00")
    assert ae_rows[0].hourly_cost == Decimal("15.00")  # 300 / 20


@pytest.mark.asyncio
async def test_get_workforce_cost_ae_month_filter_sql(db_session: AsyncSession) -> None:
    """AE invoices outside from_month/to_month are excluded (SQL-level filter)."""
    from backend.services.salary_service import get_workforce_cost

    contractor = await _make_contractor(db_session, "Petit", "Sophie")
    for date_str, amount in [
        ("2025-03-15", Decimal("200.00")),  # outside range
        ("2025-05-20", Decimal("400.00")),  # inside range
    ]:
        await _make_ae_invoice(
            db_session,
            contact_id=contractor.id,
            date_str=date_str,
            total=amount,
        )

    rows = await get_workforce_cost(db_session, from_month="2025-05", to_month="2025-05")
    ae_rows = [r for r in rows if r.person_type == "AE"]
    assert len(ae_rows) == 1
    assert ae_rows[0].amount == Decimal("400.00")
