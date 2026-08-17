from datetime import date
from decimal import Decimal

from backend.core.models import Account, Bill, Flexibility, IncomeSource, RecurrenceRule, RecurrenceType
from backend.core.projection import project
from backend.core.recurrence import expand_recurrence
from backend.core.business_days import federal_holidays, shift_business_day
from backend.core.scheduling import allowed_bill_dates
from backend.core.optimizer import optimize_schedule


def test_biweekly_has_26_events_in_a_year():
    rule = RecurrenceRule(RecurrenceType.BIWEEKLY, date(2025, 1, 3))
    assert len(expand_recurrence(rule, date(2025, 1, 1), date(2025, 12, 31))) == 26


def test_semi_monthly_has_24_events_in_a_year():
    rule = RecurrenceRule(RecurrenceType.SEMI_MONTHLY, date(2025, 1, 1), 1, 15)
    assert len(expand_recurrence(rule, date(2025, 1, 1), date(2025, 12, 31))) == 24


def test_projection_folds_daily_balance_and_shifts_income_earlier():
    account = Account(Decimal("100"), date(2025, 6, 13))
    income = IncomeSource("Paycheck", Decimal("500"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 14)))
    bill = Bill("Rent", Decimal("200"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 16)), Flexibility.FIXED)
    series = project(account, [income], [bill], 5)
    assert series[0].date == date(2025, 6, 13)
    assert series[0].closing_balance == Decimal("600")
    assert series[3].closing_balance == Decimal("400")


def test_variable_bill_projects_at_high_end():
    account = Account(Decimal("1000"), date(2025, 6, 1))
    bill = Bill("Power", Decimal("100"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 2)), Flexibility.FLEXIBLE, Decimal("20"))
    assert project(account, [], [bill], 3)[1].closing_balance == Decimal("880")


def test_window_bill_exposes_only_business_days_inside_its_window():
    bill = Bill(
        "Card payment",
        Decimal("300"),
        RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 22)),
        Flexibility.WINDOW,
        window_start=18,
        window_end=22,
    )
    assert allowed_bill_dates(bill, date(2025, 6, 22)) == [date(2025, 6, 18), date(2025, 6, 20)]


def test_flexible_bill_exposes_business_days_for_the_full_month():
    bill = Bill(
        "Savings transfer",
        Decimal("100"),
        RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 1)),
        Flexibility.FLEXIBLE,
    )
    dates = allowed_bill_dates(bill, date(2025, 6, 1))
    assert dates[0] == date(2025, 6, 2)
    assert dates[-1] == date(2025, 6, 30)
    assert len(dates) == 20


def test_fixed_bill_has_no_movable_candidates():
    bill = Bill(
        "Rent",
        Decimal("1500"),
        RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 16)),
        Flexibility.FIXED,
    )
    assert allowed_bill_dates(bill, date(2025, 6, 16)) == []


def test_projection_rejects_invalid_horizons():
    account = Account(Decimal("100"), date(2025, 1, 1))
    for horizon in (0, -1, 3661):
        try:
            project(account, [], [], horizon)
        except ValueError:
            pass
        else:
            raise AssertionError(f"horizon {horizon} should be rejected")


def test_monthly_recurrence_clamps_february_and_leap_day():
    rule = RecurrenceRule(RecurrenceType.MONTHLY, date(2024, 1, 31))
    dates = expand_recurrence(rule, date(2024, 1, 1), date(2024, 3, 31))
    assert dates == [date(2024, 1, 31), date(2024, 2, 29), date(2024, 3, 31)]


def test_biweekly_anchor_before_window_keeps_fourteen_day_cadence():
    rule = RecurrenceRule(RecurrenceType.BIWEEKLY, date(2024, 12, 27))
    dates = expand_recurrence(rule, date(2025, 1, 1), date(2025, 1, 31))
    assert dates == [date(2025, 1, 10), date(2025, 1, 24)]


def test_holiday_calendar_and_observed_shift_are_explicit():
    assert date(2025, 1, 20) in federal_holidays(2025)
    assert date(2025, 6, 19) in federal_holidays(2025)
    assert date(2026, 7, 3) in federal_holidays(2026)
    assert shift_business_day(date(2025, 6, 19), 1) == date(2025, 6, 20)


def test_optimizer_never_moves_fixed_bills():
    account = Account(Decimal("0"), date(2025, 6, 2))
    bill = Bill("Rent", Decimal("100"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 2)), Flexibility.FIXED)

    result = optimize_schedule(account, [], [bill], 5)

    assert result.moves == ()
    assert result.before_negative_days == 5
    assert result.after_min_balance == result.before_min_balance


def test_optimizer_moves_window_bill_to_fix_negative_day():
    account = Account(Decimal("50"), date(2025, 6, 2))
    income = IncomeSource("Paycheck", Decimal("100"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 5)))
    bill = Bill(
        "Card payment",
        Decimal("100"),
        RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 3)),
        Flexibility.WINDOW,
        window_start=3,
        window_end=5,
    )

    result = optimize_schedule(account, [income], [bill], 5)

    assert result.moves == (result.moves[0],)
    assert result.moves[0].new_date == date(2025, 6, 5)
    assert result.before_negative_days == 2
    assert result.after_negative_days == 0
    assert result.after_min_balance == Decimal("50")


def test_optimizer_reports_no_improvement_when_only_allowed_dates_are_worse():
    account = Account(Decimal("50"), date(2025, 6, 2))
    bill = Bill(
        "Card payment",
        Decimal("100"),
        RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 3)),
        Flexibility.WINDOW,
        window_start=3,
        window_end=3,
    )

    result = optimize_schedule(account, [], [bill], 5)

    assert result.moves == ()
    assert result.before_min_balance == Decimal("-50")
    assert "No allowed bill-date move" in result.recommendation


def test_optimizer_greedily_applies_multiple_moves():
    account = Account(Decimal("100"), date(2025, 6, 2))
    income = IncomeSource("Paycheck", Decimal("200"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 5)))
    bills = [
        Bill("First", Decimal("150"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 3)), Flexibility.WINDOW, window_start=3, window_end=4),
        Bill("Second", Decimal("100"), RecurrenceRule(RecurrenceType.ONCE, date(2025, 6, 4)), Flexibility.WINDOW, window_start=4, window_end=5),
    ]

    result = optimize_schedule(account, [income], bills, 5)

    assert len(result.moves) == 2
    assert {move.bill_name for move in result.moves} == {"First", "Second"}
    assert result.after_negative_days < result.before_negative_days
