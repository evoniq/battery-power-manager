from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from .telemetry import Telemetry


@dataclass(frozen=True)
class Alert:
    key: str
    severity: str
    message: str


@dataclass
class AlertConfig:
    low_battery_percent: float = 30.0
    critical_battery_percent: float = 15.0
    low_runtime_minutes: float = 30.0
    max_output_watts: float | None = None
    debounce_minutes: float = 15.0


@dataclass
class AlertEngine:
    config: AlertConfig = field(default_factory=AlertConfig)
    _last_sent: dict[str, datetime] = field(default_factory=dict)

    def evaluate(self, telemetry: Telemetry, at: datetime | None = None) -> list[Alert]:
        at = at or datetime.now(timezone.utc)
        candidates: list[Alert] = []
        if not telemetry.connected:
            candidates.append(Alert("disconnected", "warning", "EcoFlow device disconnected or telemetry unavailable"))
        soc = telemetry.soc_percent
        if soc is not None:
            if soc <= self.config.critical_battery_percent:
                candidates.append(Alert("battery_critical", "critical", f"EcoFlow battery critical: {soc:.0f}%"))
            elif soc <= self.config.low_battery_percent:
                candidates.append(Alert("battery_low", "warning", f"EcoFlow battery low: {soc:.0f}%"))
        runtime = telemetry.runtime_remaining_minutes
        if runtime is not None and runtime <= self.config.low_runtime_minutes:
            candidates.append(Alert("runtime_low", "warning", f"EcoFlow runtime low: {runtime:.0f} min remaining"))
        max_w = self.config.max_output_watts
        out_w = telemetry.output_watts
        if max_w is not None and out_w is not None and out_w >= max_w:
            candidates.append(Alert("load_high", "warning", f"EcoFlow load high: {out_w:.0f} W"))
        return [a for a in candidates if self._allow(a.key, at)]

    def _allow(self, key: str, at: datetime) -> bool:
        last = self._last_sent.get(key)
        if last and at - last < timedelta(minutes=self.config.debounce_minutes):
            return False
        self._last_sent[key] = at
        return True
