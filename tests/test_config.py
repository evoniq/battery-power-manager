from pathlib import Path

from ecoflow_tray.config import (
    Config,
    default_config_path,
    load_config,
    resolve_config_path,
)


def test_load_config_returns_defaults_when_file_missing(tmp_path: Path):
    cfg = load_config(tmp_path / "does-not-exist.toml")
    assert isinstance(cfg, Config)
    assert cfg.device.capacity_wh == 1024.0
    assert cfg.source.order == ("nut", "fake")
    assert cfg.alerts.low_battery_percent == 30.0


def test_load_config_overrides_from_toml(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
[device]
capacity_wh = 2048.0
serial_port_hint = "COM7"

[source]
order = ["serial", "nut", "fake"]
poll_interval_seconds = 5

[alerts]
low_battery_percent = 40
debounce_minutes = 10
""",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.device.capacity_wh == 2048.0
    assert cfg.device.serial_port_hint == "COM7"
    assert cfg.source.order == ("serial", "nut", "fake")
    assert cfg.source.poll_interval_seconds == 5
    assert cfg.alerts.low_battery_percent == 40
    assert cfg.alerts.debounce_minutes == 10


def test_unknown_keys_in_toml_are_ignored(tmp_path: Path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
[device]
capacity_wh = 1500.0
mystery_field = "ignored"

[alerts]
not_a_real_alert = 1
""",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg.device.capacity_wh == 1500.0
    assert cfg.alerts.low_battery_percent == 30.0  # default preserved


def test_resolve_config_path_prefers_explicit(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ECOFLOW_TRAY_CONFIG", str(tmp_path / "from_env.toml"))
    explicit = tmp_path / "explicit.toml"
    assert resolve_config_path(explicit) == explicit


def test_resolve_config_path_reads_env(tmp_path: Path, monkeypatch):
    target = tmp_path / "from_env.toml"
    monkeypatch.setenv("ECOFLOW_TRAY_CONFIG", str(target))
    assert resolve_config_path() == target


def test_default_config_path_returns_a_path(monkeypatch):
    monkeypatch.delenv("ECOFLOW_TRAY_CONFIG", raising=False)
    p = default_config_path()
    assert p.name == "config.toml"
    assert "ecoflow-tray" in p.parts
