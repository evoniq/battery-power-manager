from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class Telemetry:
    source: str
    device_name: str = "EcoFlow DELTA 3 Plus"
    connected: bool = False
    soc_percent: float | None = None
    input_watts: float | None = None
    output_watts: float | None = None
    battery_watts: float | None = None
    temperature_c: float | None = None
    runtime_remaining_minutes: float | None = None
    time_to_full_minutes: float | None = None
    status: str = "unknown"
    updated_at: datetime | None = None
    raw: dict | None = None

    def with_estimates(self, capacity_wh: float = 1024.0, usable_factor: float = 0.90) -> "Telemetry":
        runtime = self.runtime_remaining_minutes
        ttf = self.time_to_full_minutes
        soc = self.soc_percent
        output_w = self.output_watts or 0.0
        input_w = self.input_watts or 0.0
        if soc is not None and runtime is None and output_w > 5:
            remaining_wh = capacity_wh * max(0.0, min(100.0, soc)) / 100.0 * usable_factor
            runtime = remaining_wh / output_w * 60.0
        if soc is not None and ttf is None and input_w > 5 and soc < 100:
            missing_wh = capacity_wh * (100.0 - max(0.0, min(100.0, soc))) / 100.0
            ttf = missing_wh / input_w * 60.0
        status = self.status
        if status == "unknown":
            if input_w > 5 and (input_w >= output_w):
                status = "charging"
            elif output_w > 5:
                status = "discharging"
            elif self.connected:
                status = "idle"
        return Telemetry(**{**self.__dict__, "runtime_remaining_minutes": _finite_or_none(runtime), "time_to_full_minutes": _finite_or_none(ttf), "status": status})


def _finite_or_none(value: float | None) -> float | None:
    return value if value is not None and isfinite(value) else None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def format_minutes(minutes: float | None) -> str:
    if minutes is None:
        return "unknown"
    if minutes < 1:
        return "<1m"
    total = int(round(minutes))
    h, m = divmod(total, 60)
    return f"{h}h {m}m" if h else f"{m}m"
