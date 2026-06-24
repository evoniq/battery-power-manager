from __future__ import annotations
from pathlib import Path
import subprocess
import sys
from ecoflow_tray.telemetry import Telemetry, now_utc


def _subprocess_no_window_kwargs() -> dict[str, int]:
    """Hide transient Windows console windows for polling subprocesses.

    The GUI polls NUT every few seconds. On Windows, launching ``upsc.exe`` from a
    windowed PyInstaller app can briefly flash a console/cmd window on every
    poll. ``CREATE_NO_WINDOW`` is Windows-only and harmlessly omitted elsewhere.
    """
    if sys.platform != "win32":
        return {}
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {"creationflags": creationflags, "startupinfo": startupinfo}


class NutAdapter:
    def __init__(self, upsc_path: str = "upsc", device: str = "nutdev1@127.0.0.1", timeout: float = 5.0):
        self.upsc_path = _resolve_upsc_path(upsc_path)
        self.device = device
        self.timeout = timeout

    def read(self) -> Telemetry:
        try:
            proc = subprocess.run(
                [self.upsc_path, self.device],
                text=True,
                capture_output=True,
                timeout=self.timeout,
                **_subprocess_no_window_kwargs(),
            )
        except Exception as exc:
            return Telemetry(source="nut", connected=False, status="error", raw={"error": str(exc)}, updated_at=now_utc())
        if proc.returncode != 0:
            return Telemetry(source="nut", connected=False, status="error", raw={"stderr": proc.stderr.strip(), "stdout": proc.stdout.strip()}, updated_at=now_utc())
        data = _parse_upsc(proc.stdout)
        return _telemetry_from_nut(data)


def _resolve_upsc_path(upsc_path: str) -> str:
    """Prefer bundled NUT client when installed next to the frozen app."""
    if upsc_path != "upsc":
        return upsc_path
    executable_dir = Path(sys.executable).resolve().parent
    bundled = executable_dir / "nut/mingw64/bin/upsc.exe"
    if bundled.exists():
        return str(bundled)
    return upsc_path


def _parse_upsc(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def _num(data: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        if key in data:
            try:
                return float(data[key])
            except ValueError:
                return None
    return None


def _telemetry_from_nut(data: dict[str, str]) -> Telemetry:
    status_raw = data.get("ups.status", "").upper()
    input_w = _num(data, "input.realpower", "input.power")
    output_w = _num(data, "output.realpower", "output.power", "ups.realpower")
    load_percent = _num(data, "ups.load")
    nominal_w = _num(data, "ups.realpower.nominal")
    if output_w is None and load_percent is not None and nominal_w is not None:
        output_w = nominal_w * max(0.0, load_percent) / 100.0

    status = "unknown"
    if "OL" in status_raw and "CHRG" in status_raw:
        status = "charging"
    elif "OB" in status_raw or "DISCHRG" in status_raw:
        status = "discharging"
    elif status_raw == "OL":
        status = "online"
    elif status_raw:
        status = status_raw.lower()

    runtime = _num(data, "battery.runtime")
    # EcoFlow RIVER 3 Plus via the bundled ECOFLOW HID NUT driver exposes
    # battery.runtime in minutes, despite the generic NUT convention being
    # seconds. Do not divide this value: with little/no load, values like 2320
    # correctly mean multi-day runtime, not 38 minutes.
    runtime_minutes = runtime
    model = data.get("device.model") or data.get("ups.model") or "EcoFlow UPS"
    return Telemetry(
        source="nut",
        device_name=model,
        connected=True,
        soc_percent=_num(data, "battery.charge"),
        input_watts=input_w,
        output_watts=output_w,
        temperature_c=_num(data, "battery.temperature", "device.temperature", "ups.temperature"),
        runtime_remaining_minutes=runtime_minutes,
        status=status,
        updated_at=now_utc(),
        raw=data,
    ).with_estimates()
