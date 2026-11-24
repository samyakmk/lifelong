from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .catalog import DRAW_TIMEZONE, PLAN

DRAW_ZONE = ZoneInfo(DRAW_TIMEZONE)


def timestamp(at=None):
    return (at or datetime.now(UTC)).astimezone(UTC).isoformat(timespec="seconds")


def draw_date(value):
    if "T" not in value:
        return value[:10]
    return datetime.fromisoformat(value).astimezone(DRAW_ZONE).date().isoformat()


def visit_time(value):
    if not value:
        return "—"
    if len(value) == 10:
        return datetime.fromisoformat(value).strftime("%b %d, %Y")
    at = datetime.fromisoformat(value)
    at = at if at.tzinfo else at.replace(tzinfo=UTC)
    local = at.astimezone(DRAW_ZONE)
    return f"{local:%b %d, %Y} · " + local.strftime("%I:%M %p %Z").lstrip("0")


def seed_slots(db):
    center_id = db.execute("SELECT id FROM draw_centers WHERE code = ?", (PLAN.draw_center_code,)).fetchone()[0]
    today = datetime.now(DRAW_ZONE).date()
    rows = []
    for days_ahead in range(1, 15):
        day = today + timedelta(days=days_ahead)
        if day.weekday() < 5:
            rows.extend(
                (center_id, timestamp(datetime.combine(day, clock, DRAW_ZONE)))
                for clock in (time(9), time(10, 30), time(14))
            )
    db.executemany("INSERT OR IGNORE INTO draw_slots (draw_center_id, starts_at) VALUES (?, ?)", rows)
