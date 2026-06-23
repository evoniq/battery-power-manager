from ecoflow_tray.telemetry import Telemetry, format_minutes


def test_estimates_runtime_from_soc_capacity_and_output_watts():
    t = Telemetry(source="test", connected=True, soc_percent=50, output_watts=100).with_estimates(capacity_wh=1000, usable_factor=0.9)
    assert round(t.runtime_remaining_minutes) == 270
    assert t.status == "discharging"


def test_estimates_time_to_full_when_charging():
    t = Telemetry(source="test", connected=True, soc_percent=75, input_watts=250, output_watts=0).with_estimates(capacity_wh=1000)
    assert round(t.time_to_full_minutes) == 60
    assert t.status == "charging"


def test_format_minutes_human_readable():
    assert format_minutes(None) == "unknown"
    assert format_minutes(59) == "59m"
    assert format_minutes(61) == "1h 1m"
