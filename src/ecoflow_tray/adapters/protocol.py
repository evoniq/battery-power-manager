from __future__ import annotations
from typing import Protocol
from ecoflow_tray.telemetry import Telemetry

class TelemetryAdapter(Protocol):
    def read(self) -> Telemetry: ...
