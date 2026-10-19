from aqi import pm25_category, pm10_category, is_alert_level


def test_pm25_boundaries():
    assert pm25_category(0) == "Good"
    assert pm25_category(30) == "Good"
    assert pm25_category(30.1) == "Satisfactory"
    assert pm25_category(60) == "Satisfactory"
    assert pm25_category(90) == "Moderate"
    assert pm25_category(91) == "Poor"
    assert pm25_category(120) == "Poor"
    assert pm25_category(120.5) == "Very Poor"
    assert pm25_category(250) == "Very Poor"
    assert pm25_category(250.1) == "Severe"


def test_pm10_boundaries():
    assert pm10_category(50) == "Good"
    assert pm10_category(100) == "Satisfactory"
    assert pm10_category(250) == "Moderate"
    assert pm10_category(350) == "Poor"
    assert pm10_category(430) == "Very Poor"
    assert pm10_category(431) == "Severe"


def test_alert_level():
    assert not is_alert_level("Moderate")
    assert is_alert_level("Poor")
    assert is_alert_level("Severe")