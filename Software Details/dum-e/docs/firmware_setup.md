# Firmware setup & tuning (ESP32 / MicroPython)

Matches the **servo-only** build in **`src/modules/motion_controller.py`** and **`src/drivers/stepper.py`** (`Servo` class). Default: **no panel buttons** — control via **desktop dashboard**, **USB serial**, or **REPL** (`USE_PHYSICAL_BUTTONS = False` in **`src/config.py`**).

## What to configure

| Location | Purpose |
|----------|---------|
| `src/pins.py` | GPIO per servo (`SERVO_*`); optional `BTN_*` if using physical buttons. |
| `src/config.py` | `USE_PHYSICAL_BUTTONS`, `LOOP_DELAY_MS`, `MOTION_STEP_DEG_PER_TICK`, per-joint **`JOINT_ANGLE_*`**, **`SERVO_PWM_MIN_US` / `SERVO_PWM_MAX_US`**, idle/sleep timeouts, behavior durations. |

## After mechanical assembly

1. **GPIOs** — Confirm **`pins.py`** matches wiring (defaults include waist 4, upper_arm 22, forearm 23, hand 21, end_effector 19).
2. **PWM calibration** — For each joint, sweep toward **0°** and **180°** and tune **`SERVO_PWM_MIN_US[i]`** / **`SERVO_PWM_MAX_US[i]`** so horns match mechanical limits without binding (often 500–2500 µs; some servos need a narrower range).
3. **Software limits** — Set **`JOINT_ANGLE_MIN_DEG`** / **`JOINT_ANGLE_MAX_DEG`** so commands never exceed **physical stops** (gripper often narrow).
4. **Motion feel** — Raise **`MOTION_STEP_DEG_PER_TICK`** (e.g. 2–3) for faster motion; lower **`LOOP_DELAY_MS`** raises loop rate (more CPU).

## Physical buttons (optional)

Set **`USE_PHYSICAL_BUTTONS = True`** in **`config.py`**. **`main.py`** then uses **`drivers.pir.Button`** on **`BTN_J1`…`BTN_J5`** (joint select) and **`BTN_UP` / `BTN_DOWN`** (nudge).

## Commands (stdin / dashboard)

Parsed by **`modules/command_parser.py`** (exact keywords) and **`modules/intent_parser.py`** (adds **sentiment**). Known one-word commands include: **`pick`**, **`drop`**, **`move`**, **`stop`**, **`hello`**, **`home`**, **`ready`**, **`down`**, **`status`**, **`history`**, **`reset`**. Lines like **`move left`** are parsed as **`move`** with args.

**`build_command_from_parse_result()`** in **`backend/command_router.py`** maps parser output to **`Command`** + **`Actions`**. **`STOP`** / **`RESET`** interact with **`SafetyManager`** and **`StateMachine`** as documented in **`docs/state_machine.md`**.

Sentiment keywords can trigger **`express_*`** behaviors in **`main.py`** before routing (see **`_SENTIMENT_BEHAVIOR`** map).

## Laptop / ROS / RViz

- **Inverse kinematics**, measured link lengths, and **URDF** live on the host; see **`ros2_ws/src/dum_e_description/`** and **`docs/hardware.md`**.
- **`desktop_app`** can publish high-level strings to ROS via **`src/interfaces/robot_bridge.py`** when running with ROS 2 available (`DUM_E_SKIP_ROS2` to disable).

## Serial / dashboard

The main loop reads **lines from stdin** (USB serial). The desktop app is intended to send the same text commands as the REPL. Ensure **`main.py`** is the entry script on the board after deploy.
