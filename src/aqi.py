# Category limits from the CPCB National AQI (24-hour averages, ug/m3).
# A value above the last limit is "Severe".
PM25_LIMITS = [(30, "Good"), (60, "Satisfactory"), (90, "Moderate"),
               (120, "Poor"), (250, "Very Poor")]
PM10_LIMITS = [(50, "Good"), (100, "Satisfactory"), (250, "Moderate"),
               (350, "Poor"), (430, "Very Poor")]

ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]


def _category(value, limits):
    for upper, name in limits:
        if value <= upper:
            return name
    return "Severe"


def pm25_category(value):
    return _category(value, PM25_LIMITS)


def pm10_category(value):
    return _category(value, PM10_LIMITS)


def is_alert_level(category):
    """True for Poor, Very Poor and Severe."""
    return ORDER.index(category) >= ORDER.index("Poor")