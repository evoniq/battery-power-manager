from __future__ import annotations

"""Tray UI boundary.

`pystray` and `pillow` are optional dependencies (extra `tray`). All imports
are kept lazy inside `run_tray` so that:
- the package, CLI, and tests stay usable without them installed,
- a missing dep produces one clear error instead of an import-time crash.
"""

from typing import Callable
import os
import subprocess
import sys

from ..single_instance import AlreadyRunning, acquire_instance_lock
from ..telemetry import Telemetry
from .status import build_status_text, build_tooltip


class TrayDependenciesMissing(RuntimeError):
    pass


def _detail_window_command() -> list[str]:
    """Return the command used by the tray menu to open the detail window.

    In a normal Python checkout we can relaunch the module. In a PyInstaller
    build, however, ``sys.executable`` is already the bundled application EXE;
    passing ``-m ecoflow_tray.cli`` to that EXE makes the child process exit
    immediately. That looked like a GUI window trying to open and instantly
    closing from the tray menu. Use the bundled EXE directly when frozen.
    """
    if getattr(sys, "frozen", False):
        return [sys.executable, "--detail-window"]
    return [sys.executable, "-m", "ecoflow_tray.cli", "--detail-window"]


def run_tray(
    poll: Callable[[], Telemetry],
    *,
    interval_seconds: float = 10.0,
    title: str = "EcoFlow Tray",
) -> None:
    """Launch the tray icon. Blocks on the pystray event loop.

    `poll` is called every `interval_seconds` on a background thread to refresh
    the icon tooltip. Kept thin: rendering is delegated to `build_status_text`.
    """
    try:
        tray_lock = acquire_instance_lock(47631, "EcoFlow tray")
    except AlreadyRunning:
        return

    try:
        import threading
        import time

        import pystray  # type: ignore[import-not-found]
        from PIL import Image, ImageDraw  # type: ignore[import-not-found]
    except ImportError as exc:
        tray_lock.close()
        raise TrayDependenciesMissing(
            "Install the `tray` extra: `uv pip install -e .[tray]` "
            "(needs pystray and pillow)."
        ) from exc

    icon_image = _battery_icon(Image, ImageDraw, 0.0)
    icon = pystray.Icon(name="ecoflow-tray", icon=icon_image, title=title)
    stop = threading.Event()

    def refresh_loop() -> None:
        while not stop.is_set():
            try:
                t = poll()
                icon.title = build_tooltip(t)
                icon.icon = _battery_icon(Image, ImageDraw, (t.soc_percent or 0) / 100.0)
            except Exception as exc:  # keep loop alive on adapter errors
                icon.title = f"{title}: poll error: {exc}"
            stop.wait(interval_seconds)

    def on_show_details(icon_: object, _item: object) -> None:
        env = os.environ.copy()
        subprocess.Popen(
            _detail_window_command(),
            cwd=os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd(),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    def on_quit(icon_: object, _item: object) -> None:
        stop.set()
        tray_lock.close()
        icon.stop()  # type: ignore[attr-defined]

    icon.menu = pystray.Menu(
        pystray.MenuItem("Show details", on_show_details, default=True),
        pystray.MenuItem("Quit", on_quit),
    )
    threading.Thread(target=refresh_loop, name="ecoflow-poll", daemon=True).start()
    icon.run()


def _battery_icon(Image, ImageDraw, fill: float):
    """Horizontal tray battery icon.

    Windows tray icons are tiny; the previous vertical battery wasted width. This
    draws a 90-degree rotated battery so the fill bar is wider and easier to
    read next to the clock.
    """
    fill = max(0.0, min(1.0, fill))
    # Give Windows a high-resolution source image. The taskbar still decides the
    # final physical size, but a larger/bolder source survives scaling much
    # better than a tiny 64px drawing.
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = (10, 54, 222, 190)
    cap = (222, 92, 248, 152)
    d.rounded_rectangle(body, radius=28, fill=(18, 24, 38, 255), outline=(0, 0, 0, 255), width=18)
    d.rounded_rectangle(cap, radius=8, fill=(0, 0, 0, 255))
    inner_left, inner_top, inner_right, inner_bottom = 32, 78, 200, 166
    fill_right = inner_left + int((inner_right - inner_left) * fill)
    if fill > 0.60:
        color = (80, 210, 100, 255)
    elif fill > 0.30:
        color = (235, 190, 65, 255)
    else:
        color = (225, 80, 75, 255)
    if fill_right > inner_left:
        d.rounded_rectangle((inner_left, inner_top, fill_right, inner_bottom), radius=14, fill=color)
    return img
