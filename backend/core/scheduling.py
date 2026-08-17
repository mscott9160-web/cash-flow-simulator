import calendar
from datetime import date

from .business_days import federal_holidays
from .models import Bill, Flexibility


def allowed_bill_dates(bill: Bill, occurrence: date) -> list[date]:
    """Return the business-day dates a movable bill may use in its occurrence month."""
    if bill.flexibility == Flexibility.FIXED:
        return []
    if bill.flexibility == Flexibility.WINDOW:
        start_day = bill.window_start or occurrence.day
        end_day = bill.window_end or occurrence.day
    else:
        start_day = 1
        end_day = calendar.monthrange(occurrence.year, occurrence.month)[1]
    start_day = max(1, min(start_day, calendar.monthrange(occurrence.year, occurrence.month)[1]))
    end_day = max(start_day, min(end_day, calendar.monthrange(occurrence.year, occurrence.month)[1]))
    holidays = federal_holidays(occurrence.year)
    return [
        date(occurrence.year, occurrence.month, day)
        for day in range(start_day, end_day + 1)
        if date(occurrence.year, occurrence.month, day).weekday() < 5
        and date(occurrence.year, occurrence.month, day) not in holidays
    ]
