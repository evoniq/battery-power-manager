from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class SerialPortInfo:
    """Subset of pyserial's ListPortInfo we actually depend on.

    Kept hand-rolled so detection logic is testable without pyserial installed.
    """

    device: str  # e.g. "COM7" or "/dev/ttyUSB0"
    description: str = ""
    vid: int | None = None
    pid: int | None = None
    serial_number: str | None = None
    manufacturer: str | None = None


def list_serial_ports() -> list[SerialPortInfo]:
    """Enumerate serial ports via pyserial if available; otherwise return [].

    The import is lazy so the rest of the package stays usable on systems
    that have not opted into the `serial` extra.
    """
    try:
        from serial.tools import list_ports  # type: ignore[import-not-found]
    except ImportError:
        return []
    out: list[SerialPortInfo] = []
    for p in list_ports.comports():
        out.append(
            SerialPortInfo(
                device=getattr(p, "device", ""),
                description=getattr(p, "description", "") or "",
                vid=getattr(p, "vid", None),
                pid=getattr(p, "pid", None),
                serial_number=getattr(p, "serial_number", None),
                manufacturer=getattr(p, "manufacturer", None),
            )
        )
    return out


def find_ecoflow_ports(
    ports: Iterable[SerialPortInfo],
    vid: int,
    pid: int,
) -> list[SerialPortInfo]:
    return [p for p in ports if p.vid == vid and p.pid == pid]


def pick_port(
    ports: Sequence[SerialPortInfo],
    vid: int,
    pid: int,
    hint: str | None = None,
) -> SerialPortInfo | None:
    """Resolve a single serial port to use.

    Priority:
      1. `hint` (e.g. "COM7") if it matches a known device.
      2. First VID/PID match.
      3. None.
    """
    if hint:
        for p in ports:
            if p.device.lower() == hint.lower():
                return p
    matches = find_ecoflow_ports(ports, vid, pid)
    return matches[0] if matches else None
