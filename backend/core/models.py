from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class RecurrenceType(str, Enum):
    ONCE = "ONCE"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    SEMI_MONTHLY = "SEMI_MONTHLY"
    MONTHLY = "MONTHLY"


class Flexibility(str, Enum):
    FIXED = "FIXED"
    WINDOW = "WINDOW"
    FLEXIBLE = "FLEXIBLE"


class EventKind(str, Enum):
    INCOME = "income"
    BILL = "bill"


@dataclass(frozen=True)
class RecurrenceRule:
    kind: RecurrenceType
    anchor: date
    day_of_month: int | None = None
    second_day_of_month: int | None = None


@dataclass(frozen=True)
class Account:
    starting_balance: Decimal
    as_of: date


@dataclass(frozen=True)
class IncomeSource:
    name: str
    amount: Decimal
    recurrence: RecurrenceRule
    variance_pct: Decimal = Decimal("0")


@dataclass(frozen=True)
class Bill:
    name: str
    amount: Decimal
    recurrence: RecurrenceRule
    flexibility: Flexibility
    variance_pct: Decimal = Decimal("0")
    window_start: int | None = None
    window_end: int | None = None
    item_id: int | None = None


@dataclass(frozen=True)
class BillOccurrenceOverride:
    bill_name: str
    occurrence_date: date
    new_date: date
    bill_id: int | None = None


@dataclass(frozen=True)
class Event:
    name: str
    amount: Decimal
    source_date: date
    posted_date: date
    kind: EventKind


@dataclass(frozen=True)
class ProjectedDay:
    date: date
    opening_balance: Decimal
    events: tuple[Event, ...]
    closing_balance: Decimal
