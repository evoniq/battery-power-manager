from __future__ import annotations

import sys

from ecoflow_tray.ui import tray


def test_detail_window_command_uses_module_in_source_checkout(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Python312\python.exe")

    assert tray._detail_window_command() == [
        r"C:\Python312\python.exe",
        "-m",
        "ecoflow_tray.cli",
        "--detail-window",
    ]


def test_detail_window_command_uses_bundled_exe_when_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\Battery Power Manager\BatteryPowerManager.exe")

    assert tray._detail_window_command() == [
        r"C:\Program Files\Battery Power Manager\BatteryPowerManager.exe",
        "--detail-window",
    ]
