from datetime import date, timedelta


_FIXED_HOLIDAYS = ((1, 1), (6, 19), (7, 4), (11, 11), (12, 25))


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def _nth_weekday(year: int, month: int, weekday: int, occurrence: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + (occurrence - 1) * 7)


def federal_holidays(year: int) -> set[date]:
    holidays = {_observed(date(year, month, day)) for month, day in _FIXED_HOLIDAYS}
    holidays.update({
        _nth_weekday(year, 1, 0, 3),
        _nth_weekday(year, 2, 0, 3),
        date(year, 5, 31) - timedelta(days=(date(year, 5, 31).weekday() - 0) % 7),
        _nth_weekday(year, 9, 0, 1),
        _nth_weekday(year, 10, 0, 2),
        _nth_weekday(year, 11, 3, 4),
    })
    return holidays


def shift_business_day(day: date, direction: int) -> date:
    holidays = federal_holidays(day.year) | federal_holidays(day.year + (1 if direction > 0 else -1))
    shifted = day
    while shifted.weekday() >= 5 or shifted in holidays:
        shifted += timedelta(days=direction)
    return shifted
