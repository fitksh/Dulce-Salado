from zoneinfo import ZoneInfo

from django.utils import timezone

from .models import OpeningInterval

BUSINESS_TIME_ZONE = ZoneInfo("America/Argentina/Buenos_Aires")


def business_hours(business, now=None):
    if not business or not business.hours_initialized:
        return {"initialized": False, "open": False, "label": "Horarios no disponibles", "week": [], "data": {"initialized": False, "intervals": []}}
    intervals = list(business.opening_intervals.all())
    current = timezone.localtime(now or timezone.now(), BUSINESS_TIME_ZONE)
    opened = any(row.weekday == current.weekday() and row.opens_at <= current.time() < row.closes_at for row in intervals)
    return {
        "initialized": True, "open": opened, "label": "Abierto" if opened else "Cerrado",
        "week": [{"day": label, "intervals": [row for row in intervals if row.weekday == day]} for day, label in OpeningInterval.Weekday.choices],
        "data": {"initialized": True, "intervals": [{"day": row.weekday, "opens": row.opens_at.isoformat(), "closes": row.closes_at.isoformat()} for row in intervals]},
    }
