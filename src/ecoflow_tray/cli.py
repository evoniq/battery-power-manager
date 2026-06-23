from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from ecoflow_tray.adapters.fake import FakeAdapter
from ecoflow_tray.adapters.nut import NutAdapter
from ecoflow_tray.adapters.serial_detect import list_serial_ports, pick_port
from ecoflow_tray.config import load_config, resolve_config_path
from ecoflow_tray.telemetry import format_minutes
from ecoflow_tray.ui import build_status_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EcoFlow Tray telemetry CLI")
    parser.add_argument("--config", help="Path to config.toml (overrides $ECOFLOW_TRAY_CONFIG)")
    parser.add_argument("--fake", action="store_true", help="Use fake telemetry")
    parser.add_argument("--nut-upsc", help="Path to upsc executable (overrides config)")
    parser.add_argument("--nut-device", help="NUT device@host (overrides config)")
    parser.add_argument("--once", action="store_true", help="Read once and print JSON instead of launching the tray")
    parser.add_argument("--list-ports", action="store_true", help="List detected serial ports and exit")
    parser.add_argument("--show-config", action="store_true", help="Print effective config as JSON and exit")
    parser.add_argument("--tray", action="store_true", help="Launch tray UI (requires `tray` extra)")
    parser.add_argument("--detail-window", action="store_true", help="Open detail GUI window without tray (uses Tkinter)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)

    if args.show_config:
        payload = {"config_path": str(resolve_config_path(args.config)), **cfg.to_dict()}
        print(json.dumps(payload, indent=2, default=str))
        return 0

    if args.list_ports:
        ports = list_serial_ports()
        chosen = pick_port(ports, cfg.device.usb_vid, cfg.device.usb_pid, cfg.device.serial_port_hint)
        payload = {
            "ports": [asdict(p) for p in ports],
            "ecoflow_match": asdict(chosen) if chosen else None,
            "vid_pid_filter": {"vid": cfg.device.usb_vid, "pid": cfg.device.usb_pid},
        }
        print(json.dumps(payload, indent=2, default=str))
        return 0

    nut_upsc = args.nut_upsc or cfg.source.nut_upsc_path
    nut_device = args.nut_device or cfg.source.nut_device
    adapter = FakeAdapter() if args.fake else NutAdapter(nut_upsc, nut_device)

    if args.tray or not (args.once or args.detail_window):
        from ecoflow_tray.ui.tray import TrayDependenciesMissing, run_tray

        try:
            run_tray(adapter.read, interval_seconds=cfg.source.poll_interval_seconds)
            return 0
        except TrayDependenciesMissing as exc:
            print(str(exc))
            return 3

    if args.detail_window:
        from ecoflow_tray.ui.detail import DetailWindowUnavailable, show_detail_window

        try:
            show_detail_window(adapter.read, refresh_seconds=cfg.source.poll_interval_seconds)
            return 0
        except DetailWindowUnavailable as exc:
            print(str(exc))
            return 4

    t = adapter.read()
    payload = asdict(t)
    payload["updated_at"] = t.updated_at.isoformat() if t.updated_at else None
    payload["runtime"] = format_minutes(t.runtime_remaining_minutes)
    payload["time_to_full"] = format_minutes(t.time_to_full_minutes)
    payload["summary"] = build_status_text(t)
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0 if t.connected else 2


if __name__ == "__main__":
    raise SystemExit(main())
