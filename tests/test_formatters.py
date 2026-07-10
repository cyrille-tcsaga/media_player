from utils.formatters import format_duration


def test_zero():
    assert format_duration(0) == "00:00"


def test_seconds_only():
    assert format_duration(59_000) == "00:59"


def test_exactly_one_minute():
    assert format_duration(60_000) == "01:00"


def test_minutes_and_seconds():
    assert format_duration(125_000) == "02:05"


def test_over_an_hour_stays_mm_ss():
    assert format_duration(3_661_000) == "61:01"


def test_negative_clamped_to_zero():
    assert format_duration(-500) == "00:00"
