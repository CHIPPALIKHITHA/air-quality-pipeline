from datetime import datetime, timedelta, timezone

from alert_rules import should_alert

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=timezone.utc)


def ago(hours):
    return NOW - timedelta(hours=hours)


def test_two_high_fresh_readings_alert():
    ok, _ = should_alert([(ago(1), 100), (ago(2), 95)], NOW)
    assert ok


def test_single_reading_does_not_alert():
    ok, _ = should_alert([(ago(1), 400)], NOW)
    assert not ok


def test_one_high_one_moderate_does_not_alert():
    ok, _ = should_alert([(ago(1), 100), (ago(2), 80)], NOW)
    assert not ok


def test_old_data_does_not_alert():
    ok, _ = should_alert([(ago(5), 100), (ago(6), 95)], NOW)
    assert not ok


def test_readings_too_far_apart_do_not_alert():
    ok, _ = should_alert([(ago(1), 100), (ago(10), 95)], NOW)
    assert not ok


def test_cooldown():
    readings = [(ago(1), 100), (ago(2), 95)]
    assert not should_alert(readings, NOW, last_alert_at=ago(2))[0]
    assert should_alert(readings, NOW, last_alert_at=ago(7))[0]