# Battery Power Manager

A small Windows tray application for monitoring EcoFlow-style UPS/battery devices through a local NUT (`upsc`) backend.

It was built for an EcoFlow RIVER 3 Plus setup where the operator only needed the useful stuff near the clock: charge percentage, charging/discharging/idle state, and estimated runtime.

## Features

- Windows notification-area tray icon.
- Tkinter detail window.
- NUT adapter using `upsc <device>` output.
- Clean operator-facing tooltip, e.g. `Battery: 76% discharging, 4h 56m left`.
- Single-instance protection for tray and detail window.
- Hidden subprocess handling on Windows so recurring `upsc.exe` polling does not flash a console window.
- PyInstaller-friendly launch handling for tray -> detail window.
- NSIS installer script for a machine-wide Windows install.
- Unit-tested telemetry mapping and UI status text.

## Current scope

This repo intentionally keeps the UI simple. It does **not** try to show every diagnostic field the backend may expose. If live watts, temperature, or load are unavailable from NUT, the app does not invent them. Numbers that lie are worse than no numbers. Shocking, I know.

## Requirements

For development:

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) recommended
- Optional tray dependencies: `pystray`, `pillow`
- Optional Windows build: PyInstaller + NSIS

For live telemetry:

- A local NUT server or compatible `upsc.exe` reachable by the app.
- Default device string is `nutdev1@127.0.0.1`.

## Development

```bash
uv sync --extra test --extra tray --extra build
uv run pytest -q
```

Run a fake one-shot telemetry sample:

```bash
uv run ecoflow-tray --source fake --once
```

Run a NUT one-shot read:

```bash
uv run ecoflow-tray --source nut --device nutdev1@127.0.0.1 --once
```

Run tray UI:

```bash
uv run ecoflow-tray --tray
```

Run detail window:

```bash
uv run ecoflow-tray --detail-window
```

## Configuration

The app can load TOML config from the platform config path or an explicit path:

```bash
uv run ecoflow-tray --config path/to/config.toml --once
```

Example:

```toml
[device]
source = "nut"
nut_device = "nutdev1@127.0.0.1"
nut_upsc_path = "upsc"

[alerts]
low_soc_percent = 20
low_runtime_minutes = 30
```

## Windows packaging notes

The operator build uses two PyInstaller outputs:

- `BatteryPowerManager.exe` — windowed tray/detail app.
- `BatteryPowerManagerConsole.exe` — console diagnostic binary for `--once` checks.

The NSIS script installs the bundle under `Program Files` and registers startup via:

```text
HKLM\Software\Microsoft\Windows\CurrentVersion\Run
```

Important Windows lessons baked into the code/tests:

- A frozen PyInstaller app should open its detail window with `App.exe --detail-window`, not `App.exe -m package.cli --detail-window`.
- Recurring helper executables such as `upsc.exe` need `CREATE_NO_WINDOW` + hidden `STARTUPINFO` to avoid console flashes from a windowed app.
- Keep tooltip text operator-facing: charge, state, runtime/ETA. Hide model names, timestamps, and debug fields unless explicitly requested.

## License

MIT. See [LICENSE](LICENSE).
