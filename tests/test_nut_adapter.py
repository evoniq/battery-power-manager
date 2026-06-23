from ecoflow_tray.adapters.nut import _parse_upsc, _resolve_upsc_path, _subprocess_no_window_kwargs, _telemetry_from_nut


def test_parse_upsc_key_value_output():
    data = _parse_upsc("battery.charge: 88\nbattery.runtime: 7200\nups.status: OL CHRG\n")
    assert data["battery.charge"] == "88"


def test_nut_values_map_to_telemetry():
    t = _telemetry_from_nut({"battery.charge": "88", "battery.runtime": "7200", "battery.temperature": "29", "ups.status": "OL CHRG", "input.realpower": "300", "device.model": "EF-UPS-RIVER 3 Plus"})
    assert t.connected is True
    assert t.device_name == "EF-UPS-RIVER 3 Plus"
    assert t.soc_percent == 88
    assert t.runtime_remaining_minutes == 7200
    assert t.temperature_c == 29
    assert t.status == "charging"


def test_ecoflow_river3_plus_power_manager_live_shape():
    t = _telemetry_from_nut({
        "battery.charge": "100",
        "battery.runtime": "2559",
        "device.mfr": "EcoFlow",
        "device.model": "EF-UPS-RIVER 3 Plus",
        "driver.name": "usbhid-ups",
        "driver.version.data": "ECOFLOW HID 0.1",
        "ups.realpower.nominal": "286",
        "ups.status": "OL",
    })
    assert t.connected is True
    assert t.device_name == "EF-UPS-RIVER 3 Plus"
    assert t.soc_percent == 100
    assert round(t.runtime_remaining_minutes or 0, 1) == 2559.0
    assert t.output_watts is None
    assert t.status == "online"


def test_subprocess_no_window_kwargs_empty_off_windows(monkeypatch):
    monkeypatch.setattr("ecoflow_tray.adapters.nut.sys.platform", "darwin")

    assert _subprocess_no_window_kwargs() == {}


def test_subprocess_no_window_kwargs_hides_windows_console(monkeypatch):
    import subprocess

    class FakeStartupInfo:
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = None

    monkeypatch.setattr("ecoflow_tray.adapters.nut.sys.platform", "win32")
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(subprocess, "STARTF_USESHOWWINDOW", 1, raising=False)
    monkeypatch.setattr(subprocess, "SW_HIDE", 0, raising=False)
    monkeypatch.setattr(subprocess, "STARTUPINFO", FakeStartupInfo, raising=False)

    kwargs = _subprocess_no_window_kwargs()

    assert kwargs["creationflags"] == 0x08000000
    assert kwargs["startupinfo"].dwFlags == 1
    assert kwargs["startupinfo"].wShowWindow == 0


def test_resolve_upsc_path_prefers_bundled_client(monkeypatch, tmp_path):
    exe = tmp_path / "BatteryPowerManager.exe"
    exe.write_text("", encoding="utf-8")
    bundled = tmp_path / "nut" / "x86_64-w64-mingw32-nut-server" / "bin" / "upsc.exe"
    bundled.parent.mkdir(parents=True)
    bundled.write_text("", encoding="utf-8")
    monkeypatch.setattr("ecoflow_tray.adapters.nut.sys.executable", str(exe))

    assert _resolve_upsc_path("upsc") == str(bundled)


def test_resolve_upsc_path_keeps_explicit_override():
    assert _resolve_upsc_path("C:/custom/upsc.exe") == "C:/custom/upsc.exe"
