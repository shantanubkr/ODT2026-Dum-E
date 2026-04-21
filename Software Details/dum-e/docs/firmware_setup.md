# Firmware setup & tuning (ESP32 / MicroPython)

This doc matches the **servo-only, no panel buttons** build. Control is via the **desktop dashboard**, **USB serial**, or **REPL**.

## What you configure in software

| Location | Purpose |
|----------|---------|
| `src/pins.py` | GPIO for each servo — **must match your wiring**. |
| `src/config.py` | `USE_PHYSICAL_BUTTONS`, `LOOP_DELAY_MS`, `MOTION_STEP_DEG_PER_TICK`, per-joint **angle limits**, **PWM calibration** (`SERVO_PWM_MIN_US` / `SERVO_PWM_MAX_US`). |

## Steps after assembly

1. **Set GPIOs** in `pins.py` for `SERVO_HAND` and `SERVO_END_EFFECTOR` if they differ from the defaults (currently 21 and 19).
2. **PWM calibration:** For each joint, move to roughly **0°** and **180°** (via REPL or temporary test script) and adjust `SERVO_PWM_MIN_US[i]` / `SERVO_PWM_MAX_US[i]` until the horn matches your mechanical range without buzzing or binding. Typical range is 500–2500 µs; some servos need 600–2400 µs.
3. **Angle limits:** Set `JOINT_ANGLE_MIN_DEG` and `JOINT_ANGLE_MAX_DEG` so software never commands past **physical stops** (especially the gripper — often a narrow range).
4. **Motion feel:** Increase `MOTION_STEP_DEG_PER_TICK` (e.g. 2–3) for snappier motion; keep `1` for smoother motion. Lower `LOOP_DELAY_MS` increases update rate (more CPU).

## Physical buttons (optional)

Set `USE_PHYSICAL_BUTTONS = True` in `config.py` and wire buttons to the pins listed in `pins.py` (`BTN_J1` … `BTN_DOWN`).

## What we still need from you (for IK / RViz / laptop bridge)

These are **not** editable in firmware alone:

- **Measured link lengths** (or URDF) for each segment — for inverse kinematics on the laptop.
- **Confirmed GPIO map** after final wiring (update `pins.py` once and commit).
- **Local-space STL exports** from CAD — for correct RViz visuals (see hardware brief).

## Serial / dashboard

The main loop reads **lines from stdin** (USB serial). The desktop app routes commands through the same command schema as the REPL. No change required for basic operation once the board runs `main.py`.
