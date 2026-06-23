from datetime import datetime, timezone, timedelta
from ecoflow_tray.alerts import AlertConfig, AlertEngine
from ecoflow_tray.telemetry import Telemetry


def test_low_battery_alert_is_debounced():
    engine = AlertEngine(AlertConfig(low_battery_percent=30, debounce_minutes=15))
    at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    t = Telemetry(source="test", connected=True, soc_percent=20)
    assert [a.key for a in engine.evaluate(t, at)] == ["battery_low"]
    assert engine.evaluate(t, at + timedelta(minutes=5)) == []
    assert [a.key for a in engine.evaluate(t, at + timedelta(minutes=16))] == ["battery_low"]


def test_disconnected_alert():
    engine = AlertEngine()
    alerts = engine.evaluate(Telemetry(source="test", connected=False))
    assert alerts[0].key == "disconnected"
