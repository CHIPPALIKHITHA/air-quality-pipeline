from spike import is_spike


def test_big_jump_is_a_spike():
    assert is_spike(491, 95)


def test_high_value_after_high_value_is_not_a_spike():
    assert not is_spike(380, 250)       # a real severe episode builds up gradually


def test_below_minimum_is_never_a_spike():
    assert not is_spike(250, 20)


def test_no_previous_reading_is_not_a_spike():
    assert not is_spike(491, None)


def test_exactly_four_times_is_not_a_spike():
    assert not is_spike(400, 100)       # must be MORE than the factor