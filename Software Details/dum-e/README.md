# DUM-E

DUM-E is an ESP32-based robotic arm / assistant inspired by Marvel’s DUM-E. This repository holds the firmware and tooling for motion, safety, sensing, and higher-level behavior.

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

## Current focus

1. Foundation (project layout, config, docs)
2. Motion (steppers, homing, trajectories)
3. Safety (limits, emergency stop, obstacle rules)
4. Sensing (distance, motion, future vision)
5. Higher-level behavior (state machine, commands, personality-style behaviors)

## Project structure

| Path | Role |
|------|------|
| `src/` | MicroPython application: entrypoint, config, drivers, modules, interfaces |
| `docs/` | Hardware inventory, pin map, architecture, state machine notes |
| `deploy/` | Helper scripts to upload `src/` to the device and reset the board |
| `requirements.txt` | Host Python deps (`mpremote`); use with project `.venv` |
| `test/` | Host-side or future test scaffolds (not full hardware-in-the-loop yet) |

## Next steps

- Finalize wiring and fill in `docs/pin_map.md` and `src/pins.py`.
- Implement drivers against real hardware, then wire `motion_controller` and `safety_manager`.
- Grow the state machine and command path once basics are reliable.
