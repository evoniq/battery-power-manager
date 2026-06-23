from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Any

from .alerts import AlertConfig


@dataclass(frozen=True)
class DeviceConfig:
    name: str = "EcoFlow DELTA 3 Plus"
    capacity_wh: float = 1024.0
    usable_factor: float = 0.90
    # VID/PID for the EcoFlow MI_01 serial interface (see PROJECT_CONTEXT.md).
    usb_vid: int = 0x3746
    usb_pid: int = 0xFFFF
    serial_port_hint: str | None = None  # e.g. "COM7"; None -> auto-detect


@dataclass(frozen=True)
class SourceConfig:
    # Ordered list of adapters to try; first connected wins.
    order: tuple[str, ...] = ("nut", "fake")
    nut_upsc_path: str = "upsc"
    nut_device: str = "nutdev1@127.0.0.1"
    poll_interval_seconds: float = 10.0


@dataclass(frozen=True)
class Config:
    device: DeviceConfig = field(default_factory=DeviceConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    alerts: AlertConfig = field(default_factory=AlertConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "device": asdict(self.device),
            "source": {**asdict(self.source), "order": list(self.source.order)},
            "alerts": asdict(self.alerts),
        }


def default_config_path() -> Path:
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / "ecoflow-tray" / "config.toml"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "ecoflow-tray" / "config.toml"


def resolve_config_path(explicit: str | os.PathLike[str] | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("ECOFLOW_TRAY_CONFIG")
    if env:
        return Path(env)
    return default_config_path()


def load_config(path: str | os.PathLike[str] | None = None) -> Config:
    """Load config from TOML file. Missing or empty file -> defaults.

    Unknown keys are ignored so older binaries keep working with newer files.
    """
    resolved = resolve_config_path(path)
    if not resolved.exists():
        return Config()
    raw = resolved.read_text(encoding="utf-8-sig")
    data = tomllib.loads(raw)
    return _from_dict(data)


def _from_dict(data: dict[str, Any]) -> Config:
    device = _coerce_section(DeviceConfig, data.get("device", {}))
    source_raw = dict(data.get("source", {}))
    if "order" in source_raw and isinstance(source_raw["order"], list):
        source_raw["order"] = tuple(str(x) for x in source_raw["order"])
    source = _coerce_section(SourceConfig, source_raw)
    alerts = _coerce_section(AlertConfig, data.get("alerts", {}))
    return Config(device=device, source=source, alerts=alerts)


def _coerce_section(cls, raw: dict[str, Any]):
    allowed = {f.name for f in fields(cls)}
    clean = {k: v for k, v in raw.items() if k in allowed}
    base = cls()
    if not clean:
        return base
    if hasattr(base, "__dataclass_fields__") and getattr(cls, "__dataclass_params__").frozen:
        return replace(base, **clean)
    for k, v in clean.items():
        setattr(base, k, v)
    return base
