from __future__ import annotations

"""Detail window view-model and Tkinter boundary.

The row builders are pure and tested. Tkinter is imported lazily so headless
CI/tests and tray-less installs do not explode just because Windows UI exists.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ..single_instance import AlreadyRunning, acquire_instance_lock
from ..telemetry import Telemetry, format_minutes


APP_TITLE = "Battery Power Manager"


class DetailWindowUnavailable(RuntimeError):
    pass


def build_window_title(telemetry: Telemetry) -> str:
    if not telemetry.connected:
        suffix = "disconnected"
    elif telemetry.soc_percent is None:
        suffix = "unknown"
    else:
        suffix = f"{telemetry.soc_percent:.0f}%"
    return f"{APP_TITLE} — {suffix}"


def build_detail_rows(telemetry: Telemetry) -> list[tuple[str, str]]:
    return [
        ("Device", telemetry.device_name),
        ("Connection", "Connected" if telemetry.connected else "Disconnected"),
        ("Battery", _percent(telemetry.soc_percent)),
        ("Status", _status(telemetry.status)),
        ("Runtime remaining", format_minutes(telemetry.runtime_remaining_minutes)),
        ("Source", telemetry.source),
        ("Updated", _datetime(telemetry.updated_at)),
    ]


def build_dashboard_summary(telemetry: Telemetry) -> dict[str, str]:
    """Compact labels used by the rich Tk view."""
    soc = _percent(telemetry.soc_percent)
    runtime = format_minutes(telemetry.runtime_remaining_minutes)
    status = _status(telemetry.status)
    return {
        "soc": soc,
        "runtime": runtime,
        "status": status,
    }


def show_detail_window(
    poll: Callable[[], Telemetry],
    *,
    refresh_seconds: float = 5.0,
    title: str = APP_TITLE,
) -> None:
    """Open a polished Tkinter battery dashboard and refresh it periodically."""
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception as exc:  # pragma: no cover - depends on host Tk install
        raise DetailWindowUnavailable("Tkinter is not available in this Python installation.") from exc

    try:
        detail_lock = acquire_instance_lock(47632, "EcoFlow detail window")
    except AlreadyRunning:
        return

    root = tk.Tk()
    root.title(title)
    root.geometry("640x480")
    root.minsize(640, 480)
    root.configure(bg="#0f172a")
    root.protocol("WM_DELETE_WINDOW", lambda: (detail_lock.close(), root.destroy()))

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Root.TFrame", background="#0f172a")
    style.configure("Card.TFrame", background="#172033", relief="flat")
    style.configure("Title.TLabel", background="#0f172a", foreground="#e5edf7", font=("Segoe UI", 16, "bold"))
    style.configure("Subtle.TLabel", background="#0f172a", foreground="#91a4bd", font=("Segoe UI", 9))
    style.configure("CardLabel.TLabel", background="#172033", foreground="#91a4bd", font=("Segoe UI", 9, "bold"))
    style.configure("CardValue.TLabel", background="#172033", foreground="#f8fafc", font=("Segoe UI", 15, "bold"))
    style.configure("Tiny.TLabel", background="#172033", foreground="#91a4bd", font=("Segoe UI", 8))
    style.configure("DetailKey.TLabel", background="#0f172a", foreground="#91a4bd", font=("Segoe UI", 9))
    style.configure("DetailValue.TLabel", background="#0f172a", foreground="#dbeafe", font=("Segoe UI", 9))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    main = ttk.Frame(root, style="Root.TFrame", padding=22)
    main.grid(row=0, column=0, sticky="nsew")
    main.columnconfigure(0, weight=1)
    main.columnconfigure(1, weight=0)

    header = ttk.Frame(main, style="Root.TFrame")
    header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
    header.columnconfigure(0, weight=1)
    title_label = ttk.Label(header, text=APP_TITLE, style="Title.TLabel")
    title_label.grid(row=0, column=0, sticky="w", rowspan=2)
    logo_image = _load_logo_image(tk)
    if logo_image is not None:
        brand = tk.Label(header, image=logo_image, bg="#0f172a")
        brand.image = logo_image  # type: ignore[attr-defined]
    else:
        brand = tk.Label(header, text="DEVON\nSYSTEMS", bg="#0f172a", fg="#38bdf8", font=("Segoe UI", 10, "bold"), justify="right")
    brand.grid(row=0, column=1, sticky="e", padx=(8, 0), rowspan=2)

    battery_card = tk.Frame(main, bg="#111827", highlightthickness=1, highlightbackground="#243044")
    battery_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 14))
    battery_card.columnconfigure(0, weight=1)

    soc_label = tk.Label(battery_card, text="--%", bg="#111827", fg="#22c55e", font=("Segoe UI", 54, "bold"))
    soc_label.grid(row=0, column=0, pady=(22, 0))
    soc_caption = tk.Label(battery_card, text="BATTERY", bg="#111827", fg="#94a3b8", font=("Segoe UI", 10, "bold"))
    soc_caption.grid(row=1, column=0)
    battery_status_label = tk.Label(battery_card, text="unknown", bg="#111827", fg="#dbeafe", font=("Segoe UI", 14, "bold"))
    battery_status_label.grid(row=2, column=0, pady=(8, 0))
    canvas = tk.Canvas(battery_card, width=210, height=34, bg="#111827", highlightthickness=0)
    canvas.grid(row=3, column=0, pady=(18, 8))
    runtime_caption = tk.Label(battery_card, text="RUNTIME LEFT", bg="#111827", fg="#94a3b8", font=("Segoe UI", 9, "bold"))
    runtime_caption.grid(row=4, column=0)
    runtime_label = tk.Label(battery_card, text="unknown", bg="#111827", fg="#f8fafc", font=("Segoe UI", 18, "bold"))
    runtime_label.grid(row=5, column=0, pady=(2, 22))

    def draw_battery(percent: float | None, color: str) -> None:
        canvas.delete("all")
        x0, y0, x1, y1 = 8, 6, 188, 30
        canvas.create_rectangle(x0, y0, x1, y1, outline="#64748b", width=2)
        canvas.create_rectangle(x1, 13, 202, 23, outline="#64748b", fill="#64748b", width=0)
        fill_width = 0 if percent is None else max(0, min(1, percent / 100.0)) * (x1 - x0 - 6)
        if fill_width:
            canvas.create_rectangle(x0 + 3, y0 + 3, x0 + 3 + fill_width, y1 - 3, outline=color, fill=color, width=0)
        for tick in (25, 50, 75):
            tx = x0 + 3 + (x1 - x0 - 6) * tick / 100
            canvas.create_line(tx, y0 + 5, tx, y1 - 5, fill="#1f2937")

    def refresh(*, schedule: bool = True) -> None:
        try:
            telemetry = poll()
            summary = build_dashboard_summary(telemetry)
            color = _accent(telemetry)
            root.title(build_window_title(telemetry))
            title_label.configure(text=APP_TITLE)
            soc_label.configure(text=summary["soc"], fg=color)
            battery_status_label.configure(text=summary["status"], fg=color)
            draw_battery(telemetry.soc_percent, color)
            runtime_label.configure(text=summary["runtime"])
        except Exception as exc:
            root.title(f"{title} — error")
            battery_status_label.configure(text="error", fg="#ef4444")
            runtime_label.configure(text=f"Error: {exc}")
            draw_battery(None, "#64748b")
        if schedule:
            root.after(max(1, int(refresh_seconds * 1000)), refresh)

    refresh()
    root.mainloop()


def _percent(value: float | None) -> str:
    return "unknown" if value is None else f"{value:.0f}%"


def _load_logo_image(tk: object) -> object | None:
    logo_path = Path(__file__).resolve().parents[1] / "assets" / "devon_systems_logo.png"
    if not logo_path.exists():
        return None
    try:
        return tk.PhotoImage(file=str(logo_path))  # type: ignore[attr-defined]
    except Exception:
        return None


def _watts(value: float | None) -> str:
    return "unknown" if value is None else f"{value:.0f} W"


def _temperature(value: float | None) -> str:
    return "not exposed" if value is None else f"{value:.0f} °C"


def _runtime_source(telemetry: Telemetry) -> str:
    raw = telemetry.raw or {}
    if raw.get("battery.runtime") is not None:
        return "battery via NUT HID"
    if telemetry.runtime_remaining_minutes is not None:
        return "estimated"
    return "not exposed"


def _power_source(telemetry: Telemetry) -> str:
    raw = telemetry.raw or {}
    current_power_keys = ("input.realpower", "input.power", "output.realpower", "output.power", "ups.load")
    if any(key in raw for key in current_power_keys):
        return "battery via NUT HID"
    if raw.get("ups.realpower.nominal") is not None:
        return "not exposed; nominal max only"
    return "not exposed"


def _status(value: str | None) -> str:
    if not value or value == "unknown":
        return "unknown"
    return value.replace("_", " ").capitalize()


def _datetime(value: datetime | None) -> str:
    return "unknown" if value is None else value.isoformat(timespec="seconds")


def _accent(telemetry: Telemetry) -> str:
    if not telemetry.connected:
        return "#ef4444"
    if telemetry.soc_percent is None:
        return "#94a3b8"
    if telemetry.soc_percent < 15:
        return "#ef4444"
    if telemetry.soc_percent < 35:
        return "#f59e0b"
    if telemetry.status == "charging":
        return "#38bdf8"
    return "#22c55e"
