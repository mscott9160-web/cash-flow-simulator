from datetime import date
from decimal import Decimal

from backend.core.models import Account, Bill, Flexibility, IncomeSource, RecurrenceRule, RecurrenceType
from backend.storage import ScenarioStore


def test_sqlite_repository_preserves_items_overrides_and_ownership(tmp_path):
    store = ScenarioStore(str(tmp_path / "repository.sqlite"))
    account_id = store.create_account(Account(Decimal("100.00"), date(2025, 1, 1)), user_id=7)
    income_id = store.create_income(
        account_id,
        IncomeSource("Pay", Decimal("500.00"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 1, 2))),
    )
    bill_id = store.create_bill(
        account_id,
        Bill("Rent", Decimal("200.00"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 1, 3)), Flexibility.WINDOW, window_start=3, window_end=5),
        enabled=False,
    )

    assert income_id != bill_id
    assert store.get_account(account_id, user_id=7) == Account(Decimal("100.00"), date(2025, 1, 1))
    assert store.get_account(account_id, user_id=8) is None
    assert store.get_items(account_id, "bill") == []
    assert store.list_items(account_id, "bill")[0].enabled is False
    assert store.set_item_enabled(account_id, bill_id, "bill", True)
    assert len(store.get_items(account_id, "bill")) == 1

    override_id = store.create_override(account_id, bill_id, date(2025, 1, 3), date(2025, 1, 5))
    assert override_id is not None
    assert store.get_core_overrides(account_id)[0].bill_id == bill_id
    assert store.delete_override(account_id, override_id)
    assert not store.delete_override(account_id, override_id)
