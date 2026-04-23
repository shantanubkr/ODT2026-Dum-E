# DUM-E

DUM-E is an ESP32-based robotic arm / assistant inspired by Marvel’s DUM-E. On-robot: **ESP32**, **five servos**, and **power**. **Camera and higher-level software** (dashboard, vision, optional ROS) run on a **laptop**. This repository holds the MicroPython firmware, deploy tooling, and desktop app.

The device runs **MicroPython** on an ESP32. You edit code locally in **Cursor** and deploy it to the board (for example with `mpremote` and the scripts under `deploy/`).

### Setup (host)

1. **One-shot host install** (creates `.venv`, installs `mpremote`):

   ```bash
   cd "/path/to/Software Details/dum-e"
   ./setup-host.sh
   ```

2. **Push code to the ESP32 and reset** — `deploy/common.sh` picks a serial port automatically (`DUM_E_MPREMOTE_PORT` if set and valid, else `/dev/cu.usbserial-0001`, else first `cu.usbserial*` / `wchusbserial*` / `SLAB`):

   ```bash
   cd deploy
   ./sync.sh          # same as ./upload.sh && ./run.sh
   ```

3. **Open the REPL** (quit anything else using the USB serial port first — Thonny, another `mpremote`, etc.):

   ```bash
   cd deploy
   ./repl.sh
   ```

4. **Manual split** (same as before): `./upload.sh` then `./run.sh`.

5. The scripts prefer `.venv`’s `python -m mpremote` (see `deploy/common.sh`).

6. **`mpremote: failed to access (it may be in use…)`** — another app has the port, **or** `DUM_E_MPREMOTE_PORT` was empty/wrong. Fix: close other serial tools, `unset DUM_E_MPREMOTE_PORT` for auto-detect, or `export DUM_E_MPREMOTE_PORT=/dev/cu.usbserial-0001`.

7. If you moved the repo and see `bad interpreter` from `mpremote`, remove `.venv` and run `./setup-host.sh` again.

8. **`termios.error: (22, 'Invalid argument')` when `mpremote` connects** — pyserial could not apply serial settings on that `/dev/cu.*` node (common on macOS with some USB‑UART chips or when the wrong device is selected). Quit the **desktop app**, **Thonny**, and any **serial monitor** using the same port; unplug/replug the ESP32; run `ls /dev/cu.*` and set **`export DUM_E_MPREMOTE_PORT=/dev/cu.…`** to the real motor board; try another **USB cable/port** (data cable, not charge‑only); update the vendor driver (Silicon Labs CP210x, WCH CH34x, etc.) for your OS version; then **`pip install -U pyserial mpremote`** in `.venv`. If **`screen /dev/cu.… 115200`** also fails, the issue is outside Python (cable, hub, or driver).

## Current focus

1. Foundation (project layout, config, docs)
2. Motion (servos, named poses, smooth stepping)
3. Safety (limits, emergency stop)
4. Vision & UX on the laptop (camera, dashboard, optional ROS)
5. Higher-level behavior (state machine, commands, personality-style behaviors)
6. **Table / pick calibration (USB `pose_deg` jog):** see **`calibration/README.md`**

## Project structure

| Path | Role |
|------|------|
| `src/` | MicroPython application: entrypoint, config, drivers, modules, interfaces |
| `docs/` | Hardware inventory, architecture, state machine notes |
| `deploy/` | Helper scripts to upload `src/` to the device and reset the board |
| `requirements.txt` | Host Python deps (`mpremote`); use with project `.venv` |

## Next steps

- Finalize wiring and tune `src/pins.py` + per-joint PWM limits in `src/config.py`.
- Calibrate motion and grow the state machine / command path as behaviors stabilize.
