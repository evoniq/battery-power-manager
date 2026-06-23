from __future__ import annotations
from .protocol import TelemetryAdapter
from ecoflow_tray.telemetry import Telemetry, now_utc


class FakeAdapter(TelemetryAdapter):
    def read(self) -> Telemetry:
        return Telemetry(source="fake", connected=True, soc_percent=76, input_watts=0, output_watts=142, updated_at=now_utc()).with_estimates()
