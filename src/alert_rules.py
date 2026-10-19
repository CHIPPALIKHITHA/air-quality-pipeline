from datetime import timedelta

from aqi import pm25_category, is_alert_level
from config import MAX_LIVE_LAG_HOURS

CONFIRM_READINGS = 2        # how many recent readings must all be high
MAX_GAP_HOURS = 3           # those readings must be this close together
COOLDOWN_HOURS = 6          # no repeat alert for the same station within this


def should_alert(readings, now, last_alert_at=None):
    """readings: list of (measured_at, pm25_value), newest first.
    Returns (True/False, reason)."""
    if len(readings) < CONFIRM_READINGS:
        return False, "not enough readings to confirm"

    if now - readings[0][0] > timedelta(hours=MAX_LIVE_LAG_HOURS):
        return False, "latest reading is too old"

    recent = readings[:CONFIRM_READINGS]
    if recent[0][0] - recent[-1][0] > timedelta(hours=MAX_GAP_HOURS):
        return False, "readings are too far apart to confirm"

    if not all(is_alert_level(pm25_category(v)) for _, v in recent):
        return False, "not high in every recent reading"

    if last_alert_at and now - last_alert_at < timedelta(hours=COOLDOWN_HOURS):
        return False, "alert already sent recently"

    return True, "high PM2.5 confirmed"