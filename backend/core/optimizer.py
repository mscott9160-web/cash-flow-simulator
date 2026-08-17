from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .models import Account, Bill, BillOccurrenceOverride, IncomeSource
from .projection import project
from .recurrence import expand_recurrence
from .scheduling import allowed_bill_dates


@dataclass(frozen=True)
class BillMove:
    bill_name: str
    original_date: date
    new_date: date


@dataclass(frozen=True)
class OptimizationResult:
    moves: tuple[BillMove, ...]
    before_min_balance: Decimal
    after_min_balance: Decimal
    before_negative_days: int
    after_negative_days: int
    recommendation: str


def _metrics(series: list) -> tuple[Decimal, int]:
    return min(day.closing_balance for day in series), sum(day.closing_balance < 0 for day in series)


def _replace_override(
    overrides: tuple[BillOccurrenceOverride, ...],
    bill_name: str,
    occurrence_date: date,
    new_date: date,
    bill_id: int | None = None,
) -> tuple[BillOccurrenceOverride, ...]:
    replacement = BillOccurrenceOverride(bill_name, occurrence_date, new_date, bill_id)
    result: list[BillOccurrenceOverride] = []
    replaced = False
    for override in overrides:
        if (
            override.bill_name == bill_name
            and override.occurrence_date == occurrence_date
            and (override.bill_id is None or override.bill_id == bill_id)
        ):
            result.append(replacement)
            replaced = True
        else:
            result.append(override)
    if not replaced:
        result.append(replacement)
    return tuple(result)


def _recommendation(moves: tuple[BillMove, ...], before: Decimal, after: Decimal, before_negative: int, after_negative: int) -> str:
    if not moves:
        if before_negative == 0:
            return "No scheduling changes are needed; the projected balance never goes negative."
        return "No allowed bill-date move improves the projected minimum balance."
    move_text = "; ".join(
        f"move {move.bill_name} from {move.original_date.isoformat()} to {move.new_date.isoformat()}"
        for move in moves
    )
    return (
        f"Recommendation: {move_text}. This changes the minimum closing balance from {before} to {after} "
        f"and negative days from {before_negative} to {after_negative}."
    )


def optimize_schedule(
    account: Account,
    incomes: list[IncomeSource],
    bills: list[Bill],
    horizon_days: int,
    overrides: tuple[BillOccurrenceOverride, ...] = (),
) -> OptimizationResult:
    baseline = project(account, incomes, bills, horizon_days, overrides)
    before_min, before_negative = _metrics(baseline)
    current_overrides = overrides
    moves: list[BillMove] = []
    current_min, current_negative = before_min, before_negative
    end = account.as_of + timedelta(days=horizon_days - 1)

    while current_negative:
        best: tuple[tuple[Decimal, int], BillMove, tuple[BillOccurrenceOverride, ...]] | None = None
        for bill in bills:
            for occurrence in expand_recurrence(bill.recurrence, account.as_of, end):
                current_date = occurrence
                for override in current_overrides:
                    if (
                        override.bill_name == bill.name
                        and override.occurrence_date == occurrence
                        and (override.bill_id is None or override.bill_id == bill.item_id)
                    ):
                        current_date = override.new_date
                        break
                for candidate_date in allowed_bill_dates(bill, occurrence):
                    if candidate_date == current_date or not account.as_of <= candidate_date <= end:
                        continue
                    trial_overrides = _replace_override(current_overrides, bill.name, occurrence, candidate_date, bill.item_id)
                    trial_series = project(account, incomes, bills, horizon_days, trial_overrides)
                    trial_min, trial_negative = _metrics(trial_series)
                    trial_score = (trial_min, -trial_negative)
                    current_score = (current_min, -current_negative)
                    if trial_score <= current_score:
                        continue
                    move = BillMove(bill.name, occurrence, candidate_date)
                    if best is None or trial_score > best[0]:
                        best = (trial_score, move, trial_overrides)

        if best is None:
            break
        _, move, current_overrides = best
        moves.append(move)
        current_min, current_negative = _metrics(project(account, incomes, bills, horizon_days, current_overrides))

    move_tuple = tuple(moves)
    return OptimizationResult(
        moves=move_tuple,
        before_min_balance=before_min,
        after_min_balance=current_min,
        before_negative_days=before_negative,
        after_negative_days=current_negative,
        recommendation=_recommendation(move_tuple, before_min, current_min, before_negative, current_negative),
    )


optimize = optimize_schedule