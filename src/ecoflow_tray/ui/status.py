from __future__ import annotations

from ..telemetry import Telemetry, format_minutes


def build_status_text(t: Telemetry) -> str:
    """Single-line summary suitable for tray menu header or stdout."""
    if not t.connected:
        return "Battery: disconnected"
    soc = f"{t.soc_percent:.0f}%" if t.soc_percent is not None else "?%"
    if t.status == "charging":
        eta = format_minutes(t.time_to_full_minutes)
        return f"Battery: {soc} charging, full in {eta}"
    if t.status == "discharging":
        runtime = format_minutes(t.runtime_remaining_minutes)
        return f"Battery: {soc} discharging, {runtime} left"
    return f"Battery: {soc} idle"


def build_tooltip(t: Telemetry) -> str:
    """Short operator-facing tray hover tooltip.

    Keep diagnostics such as model name, telemetry source, and timestamps out of
    the hover text; operators only need charge, state, and useful ETA/runtime.
    """
    return build_status_text(t)


def _w(value: float | None) -> str:
    return f"{value:.0f} W" if value is not None else "? W"
