"""Spike rule: a PM2.5 reading that is huge AND far above the same station's previous reading."""

SPIKE_MIN = 300          # only readings at or above this are checked
SPIKE_FACTOR = 4         # ...and more than this many times the previous reading
SPIKE_WINDOW_HOURS = 3   # previous reading must be this recent to compare


def is_spike(value, previous, min_value=SPIKE_MIN, factor=SPIKE_FACTOR):
    """True if value is a sensor-style spike. With no usable previous reading we can't judge, so False."""
    if previous is None or previous <= 0:
        return False
    return value >= min_value and value > factor * previous