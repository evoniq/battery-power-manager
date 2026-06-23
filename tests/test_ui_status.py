from datetime import datetime, timezone

from ecoflow_tray.telemetry import Telemetry
from ecoflow_tray.ui import build_status_text, build_tooltip


def test_status_text_disconnected():
    t = Telemetry(source="test", connected=False)
    assert "disconnected" in build_status_text(t)


def test_status_text_discharging_shows_runtime_without_load_noise():
    t = Telemetry(
        source="test",
        connected=True,
        soc_percent=75,
        output_watts=120,
    ).with_estimates(capacity_wh=1024)
    line = build_status_text(t)
    assert "75%" in line
    assert "discharging" in line
    assert "left" in line
    assert "load" not in line
    assert "120 W" not in line


def test_status_text_charging_shows_eta_without_input_noise():
    t = Telemetry(
        source="test",
        connected=True,
        soc_percent=20,
        input_watts=200,
        output_watts=0,
    ).with_estimates(capacity_wh=1024)
    line = build_status_text(t)
    assert "20%" in line
    assert "charging" in line
    assert "full in" in line
    assert "200 W" not in line


def test_tooltip_is_operator_facing_without_model_or_timestamp():
    when = datetime(2026, 6, 13, 12, 0, tzinfo=timezone.utc)
    t = Telemetry(
        source="test",
        device_name="EF-UPS-RIVER 3 Plus",
        connected=True,
        soc_percent=50,
        runtime_remaining_minutes=125,
        status="discharging",
        updated_at=when,
    )
    tip = build_tooltip(t)
    assert tip == "Battery: 50% discharging, 2h 5m left"
    assert "EF-UPS" not in tip
    assert "2026-06-13" not in tip
    assert "Updated" not in tip


def test_tray_module_does_not_import_pystray_at_module_load():
    # Importing the module must not require pystray/pillow.
    from ecoflow_tray.ui import tray  # noqa: F401

    assert hasattr(tray, "run_tray")
    assert hasattr(tray, "TrayDependenciesMissing")
