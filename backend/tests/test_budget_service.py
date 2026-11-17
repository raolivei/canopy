"""BudgetService: CRUD invariants and period status on the calculation contract."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.db.models.budget import BudgetPeriodType
from backend.db.models.fx_rate import FxRate
from backend.db.models.transaction import Transaction as TransactionModel
from backend.models.budget import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCreate, BudgetUpdate
from backend.services.budget_service import BudgetNotFound, BudgetService, CategoryNotFound, DuplicateCategory


def tx(
    db, when: datetime, amount: str, tx_type: str = "expense", *, currency: str = "CAD", category: str | None = None
):
    db.add(
        TransactionModel(
            description=f"{tx_type} {amount}",
            amount=Decimal(amount),
            currency=currency,
            type=tx_type,
            date=when,
            category=category,
        )
    )


@pytest.fixture
def monthly_budget(db):
    return BudgetService(db).create_budget(
        BudgetCreate(
            name="Household",
            amount=Decimal("2000.00"),
            categories=[
                BudgetCategoryCreate(category_name="Groceries", amount_limit=Decimal("600.00")),
                BudgetCategoryCreate(category_name="Dining", amount_limit=Decimal("200.00")),
            ],
        )
    )


def test_create_get_update_delete_round_trip(db, monthly_budget):
    service = BudgetService(db)
    assert monthly_budget.period == BudgetPeriodType.MONTHLY
    assert [c.category_name for c in monthly_budget.categories] == ["Groceries", "Dining"]

    updated = service.update_budget(monthly_budget.id, BudgetUpdate(amount=Decimal("2500.00"), name="Home"))
    assert (updated.name, updated.amount) == ("Home", Decimal("2500.00"))

    service.delete_budget(monthly_budget.id)
    assert [b.id for b in service.list_budgets()] == []
    assert [b.id for b in service.list_budgets(active_only=False)] == [monthly_budget.id]

    with pytest.raises(BudgetNotFound):
        service.get_budget(999)


def test_duplicate_category_names_are_rejected(db, monthly_budget):
    service = BudgetService(db)
    with pytest.raises(DuplicateCategory):
        service.add_category(
            monthly_budget.id, BudgetCategoryCreate(category_name="Groceries", amount_limit=Decimal("1"))
        )
    with pytest.raises(DuplicateCategory):
        service.create_budget(
            BudgetCreate(
                name="Dup",
                amount=Decimal("10"),
                categories=[
                    BudgetCategoryCreate(category_name="A", amount_limit=Decimal("1")),
                    BudgetCategoryCreate(category_name="A", amount_limit=Decimal("2")),
                ],
            )
        )


def test_update_and_delete_category(db, monthly_budget):
    service = BudgetService(db)
    dining = next(c for c in monthly_budget.categories if c.category_name == "Dining")

    renamed = service.update_category(monthly_budget.id, dining.id, BudgetCategoryUpdate(category_name="Restaurants"))
    assert renamed.category_name == "Restaurants"
    with pytest.raises(DuplicateCategory):
        service.update_category(monthly_budget.id, dining.id, BudgetCategoryUpdate(category_name="Groceries"))

    service.delete_category(monthly_budget.id, dining.id)
    assert [c.category_name for c in service.get_budget(monthly_budget.id).categories] == ["Groceries"]
    with pytest.raises(CategoryNotFound):
        service.delete_category(monthly_budget.id, dining.id)


def test_status_uses_calendar_month_and_excludes_transfers(db, monthly_budget):
    tx(db, datetime(2026, 1, 31, 23, 30), "-100.00", category="Groceries")  # last day counts
    tx(db, datetime(2026, 2, 1, 0, 0), "-999.00", category="Groceries")  # next month does not
    tx(db, datetime(2026, 1, 10), "-50.00", category="Dining")
    tx(db, datetime(2026, 1, 11), "-75.00", category="Fuel")  # not a budget category, still spend
    tx(db, datetime(2026, 1, 12), "-500.00", "transfer", category="Groceries")
    tx(db, datetime(2026, 1, 13), "3000.00", "income", category="Salary")
    db.commit()

    status = BudgetService(db).get_budget_status(monthly_budget.id, "2026-01")

    assert (status["period_start"], status["period_end"]) == (date(2026, 1, 1), date(2026, 1, 31))
    assert status["total_spent"] == Decimal("225.00")
    assert status["remaining"] == Decimal("1775.00")
    assert status["status"] == "under"
    by_name = {c["category_name"]: c for c in status["categories"]}
    assert by_name["Groceries"]["actual_spent"] == Decimal("100.00")
    assert by_name["Groceries"]["remaining"] == Decimal("500.00")
    assert by_name["Dining"]["percentage_used"] == pytest.approx(25.0)
    assert status["fx_complete"] is True


def test_status_thresholds(db, monthly_budget):
    tx(db, datetime(2026, 3, 2), "-1700.00", category="Groceries")  # 85% of 2000, 283% of 600
    db.commit()
    status = BudgetService(db).get_budget_status(monthly_budget.id, "2026-03")
    assert status["status"] == "warning"
    assert {c["category_name"]: c["status"] for c in status["categories"]} == {"Groceries": "over", "Dining": "under"}


def test_status_defaults_to_today_month(db, monthly_budget):
    status = BudgetService(db).get_budget_status(monthly_budget.id, today=date(2026, 6, 15))
    assert (status["period_start"], status["period_end"]) == (date(2026, 6, 1), date(2026, 6, 30))


def test_yearly_budget_period(db):
    budget = BudgetService(db).create_budget(
        BudgetCreate(name="Annual", amount=Decimal("12000.00"), period=BudgetPeriodType.YEARLY)
    )
    tx(db, datetime(2026, 1, 5), "-100.00")
    tx(db, datetime(2026, 12, 31, 20, 0), "-200.00")
    tx(db, datetime(2027, 1, 1), "-400.00")
    db.commit()

    status = BudgetService(db).get_budget_status(budget.id, "2026-07")

    assert (status["period_start"], status["period_end"]) == (date(2026, 1, 1), date(2026, 12, 31))
    assert status["total_spent"] == Decimal("300.00")


def test_usd_spend_is_unconverted_without_rate_and_converted_with_one(db, monthly_budget):
    tx(db, datetime(2026, 4, 3), "-100.00", category="Groceries", currency="USD")
    tx(db, datetime(2026, 4, 4), "-10.00", category="Groceries")
    db.commit()
    service = BudgetService(db)

    before = service.get_budget_status(monthly_budget.id, "2026-04")
    assert before["total_spent"] == Decimal("10.00")
    assert before["fx_complete"] is False
    assert before["unconverted"]["USD"]["expenses"] == Decimal("100.00")
    assert before["spent_by_currency"]["USD"]["expenses"] == Decimal("100.00")

    db.add(FxRate(pair="USDCAD", as_of_date=date(2026, 4, 30), rate=Decimal("1.40000000"), source="bank_of_canada"))
    db.commit()
    after = service.get_budget_status(monthly_budget.id, "2026-04")
    assert after["total_spent"] == Decimal("150.00")
    assert after["fx_complete"] is True
    assert after["fx"][0]["as_of"] == date(2026, 4, 30)
    groceries = next(c for c in after["categories"] if c["category_name"] == "Groceries")
    assert groceries["actual_spent"] == Decimal("150.00")


def test_status_rejects_bad_month(db, monthly_budget):
    with pytest.raises(ValueError):
        BudgetService(db).get_budget_status(monthly_budget.id, "2026-4")
