from datetime import date, timedelta
from decimal import Decimal

from .business_days import shift_business_day
from .models import Account, Bill, BillOccurrenceOverride, Event, EventKind, Flexibility, IncomeSource, ProjectedDay
from .recurrence import expand_recurrence


def _amount(value: Decimal, variance_pct: Decimal) -> Decimal:
    return value * (Decimal("1") + variance_pct / Decimal("100"))


def project(
    account: Account,
    incomes: list[IncomeSource],
    bills: list[Bill],
    horizon_days: int,
    overrides: tuple[BillOccurrenceOverride, ...] = (),
) -> list[ProjectedDay]:
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least 1")
    if horizon_days > 3660:
        raise ValueError("horizon_days cannot exceed 3660")
    end = account.as_of + timedelta(days=horizon_days - 1)
    events: dict[date, list[Event]] = {}
    for income in incomes:
        for source_date in expand_recurrence(income.recurrence, account.as_of, end):
            posted = shift_business_day(source_date, -1)
            if account.as_of <= posted <= end:
                events.setdefault(posted, []).append(Event(income.name, _amount(income.amount, income.variance_pct), source_date, posted, EventKind.INCOME))
    for bill in bills:
        for source_date in expand_recurrence(bill.recurrence, account.as_of, end):
            posted = shift_business_day(source_date, 1) if bill.flexibility == Flexibility.FIXED else source_date
            for override in overrides:
                if (
                    override.occurrence_date == source_date
                    and override.bill_name == bill.name
                    and (override.bill_id is None or override.bill_id == bill.item_id)
                ):
                    posted = override.new_date
                    break
            if account.as_of <= posted <= end:
                events.setdefault(posted, []).append(Event(bill.name, -_amount(bill.amount, bill.variance_pct), source_date, posted, EventKind.BILL))
    result: list[ProjectedDay] = []
    balance = account.starting_balance
    for offset in range(horizon_days):
        day = account.as_of + timedelta(days=offset)
        day_events = tuple(sorted(events.get(day, []), key=lambda event: event.name))
        result.append(ProjectedDay(day, balance, day_events, balance + sum((event.amount for event in day_events), Decimal("0"))))
        balance = result[-1].closing_balance
    return result
