import calendar
from datetime import date, timedelta

from .models import RecurrenceRule, RecurrenceType


def _safe_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def expand_recurrence(rule: RecurrenceRule, start: date, end: date) -> list[date]:
    dates: list[date] = []
    if rule.kind == RecurrenceType.ONCE:
        return [rule.anchor] if start <= rule.anchor <= end else []
    if rule.kind in (RecurrenceType.WEEKLY, RecurrenceType.BIWEEKLY):
        step = 7 if rule.kind == RecurrenceType.WEEKLY else 14
        current = rule.anchor
        while current < start:
            current += timedelta(days=step)
        while current <= end:
            dates.append(current)
            current += timedelta(days=step)
        return dates
    current_month = date(start.year, start.month, 1)
    while current_month <= end:
        if rule.kind == RecurrenceType.SEMI_MONTHLY:
            days = (rule.day_of_month or 1, rule.second_day_of_month or 15)
        else:
            days = (rule.day_of_month or rule.anchor.day,)
        for day in days:
            occurrence = _safe_date(current_month.year, current_month.month, day)
            if start <= occurrence <= end and occurrence >= rule.anchor:
                dates.append(occurrence)
        current_month = _safe_date(current_month.year + (current_month.month == 12), current_month.month % 12 + 1, 1)
    return sorted(set(dates))
