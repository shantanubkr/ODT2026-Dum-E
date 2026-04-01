# DUM-E

DUM-E is an ESP32-based robotic arm / assistant inspired by Marvel’s DUM-E. This repository holds the firmware and tooling for motion, safety, sensing, and higher-level behavior.

The device runs **MicroPython** on an ESP32. You edit code locally in **Cursor** and deploy it to the board (for example with `mpremote` and the scripts under `deploy/`).

### Setup (host)

1. Create a virtual environment and install deploy tooling (includes `mpremote`):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

2. From `deploy/`, run `./upload.sh` to copy `src/` to the device, then `./run.sh` to reset the board. The scripts use `.venv`’s `python -m mpremote` first (works after moving the project folder), then `.venv/bin/mpremote`, then `mpremote` on your `PATH`, then system `python3 -m mpremote`.

3. If your serial device is not `/dev/cu.usbserial-0001`, set `DUM_E_MPREMOTE_PORT` or edit `deploy/common.sh`.

4. If you moved or copied the repo and see `bad interpreter` from `mpremote`, remove `.venv` and repeat step 1 so paths and wrapper scripts match this location.

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
