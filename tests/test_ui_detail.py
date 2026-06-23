from datetime import datetime, timezone

from ecoflow_tray.telemetry import Telemetry
from ecoflow_tray.ui.detail import build_detail_rows, build_window_title


def test_detail_rows_include_operator_battery_fields():
    t = Telemetry(
        source="fake",
        device_name="EcoFlow DELTA 3 Plus",
        connected=True,
        soc_percent=76,
        input_watts=320,
        output_watts=142,
        temperature_c=31.2,
        runtime_remaining_minutes=295.95,
        time_to_full_minutes=46.2,
        status="charging",
        updated_at=datetime(2026, 6, 13, 17, 0, tzinfo=timezone.utc),
    )

    rows = dict(build_detail_rows(t))

    assert rows["Device"] == "EcoFlow DELTA 3 Plus"
    assert rows["Connection"] == "Connected"
    assert rows["Battery"] == "76%"
    assert rows["Status"] == "Charging"
    assert rows["Runtime remaining"] == "4h 56m"
    assert rows["Source"] == "fake"
    assert "2026-06-13" in rows["Updated"]
    assert "Time to full" not in rows
    assert "Input" not in rows
    assert "Output / load" not in rows
    assert "Temperature" not in rows


def test_detail_rows_handle_missing_values_without_noise():
    rows = dict(build_detail_rows(Telemetry(source="nut", connected=False)))

    assert rows["Connection"] == "Disconnected"
    assert rows["Battery"] == "unknown"
    assert rows["Runtime remaining"] == "unknown"
    assert "Time to full" not in rows
    assert "Input" not in rows
    assert "Output / load" not in rows
    assert "Temperature" not in rows


def test_window_title_includes_device_and_soc_when_known():
    assert build_window_title(Telemetry(source="fake", connected=True, soc_percent=44)) == "Battery Power Manager — 44%"
    assert build_window_title(Telemetry(source="fake", connected=False)) == "Battery Power Manager — disconnected"
