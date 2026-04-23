# Firmware setup & tuning (ESP32 / MicroPython)

Matches the **servo-only** build in **`src/modules/motion_controller.py`** and **`src/drivers/servo.py`** (`Servo` class). Default: **no panel buttons** — control via **desktop dashboard**, **USB serial**, or **REPL** (`USE_PHYSICAL_BUTTONS = False` in **`src/config.py`**).

## What to configure

| Location | Purpose |
|----------|---------|
| `src/pins.py` | GPIO per servo (`SERVO_*`); optional `BTN_*` if using physical buttons. |
| `src/config.py` | **`UPRIGHT_POSE_DEG`** / **`JOINT_HOME_ANGLES`**, **`MOTION_SMOOTHING`**, **`MOTION_DEADZONE_DEG`**, `LOOP_DELAY_MS`, `USE_PHYSICAL_BUTTONS`, **`USE_BLE_NUS`**, per-joint **`JOINT_ANGLE_*`**, **`SERVO_PWM_MIN_US` / `SERVO_PWM_MAX_US`**, idle look ranges, sleep timeouts, behavior durations. |

## After mechanical assembly

1. **GPIOs / PCA** — Confirm **`pins.py`** matches wiring (legacy GPIO defaults: waist 4, upper_arm 22, forearm 23, hand 21; or I2C + PCA9685 per the same file).
2. **PWM calibration** — For each joint, sweep toward **0°** and **180°** and tune **`SERVO_PWM_MIN_US[i]`** / **`SERVO_PWM_MAX_US[i]`** so horns match mechanical limits without binding (often 500–2500 µs; some servos need a narrower range).
3. **Software limits** — Set **`JOINT_ANGLE_MIN_DEG`** / **`JOINT_ANGLE_MAX_DEG`** so commands never exceed **physical stops**.
4. **Motion feel** — Increase **`MOTION_SMOOTHING`** (0.05–0.2) for snappier tracking to targets; lower **`LOOP_DELAY_MS`** raises the loop rate (smoother but more CPU). **`MOTION_DEADZONE_DEG`** reduces end-stop jitter.

## Physical buttons (optional)

Set **`USE_PHYSICAL_BUTTONS = True`** in **`config.py`**. **`main.py`** then uses **`drivers.panel_button.Button`** on **`BTN_J1`…`BTN_J4`** (joint select) and **`BTN_UP` / `BTN_DOWN`** (nudge).

## Commands (stdin / dashboard)

Parsed by **`modules/command_parser.py`** (exact keywords) and **`modules/intent_parser.py`** (adds **sentiment**). Known one-word commands include: **`pick`**, **`drop`**, **`move`**, **`stop`**, **`hello`**, **`home`**, **`ready`**, **`down`**, **`status`**, **`history`**, **`reset`**. Lines like **`move left`** are parsed as **`move`** with args.

**`build_command_from_parse_result()`** in **`backend/command_router.py`** maps parser output to **`Command`** + **`Actions`**. **`STOP`** / **`RESET`** interact with **`SafetyManager`** and **`StateMachine`** as documented in **`docs/state_machine.md`**.

Sentiment keywords can trigger **`express_*`** behaviors in **`main.py`** before routing (see **`_SENTIMENT_BEHAVIOR`** map).

## Laptop / ROS / RViz

- **Inverse kinematics**, measured link lengths, and **URDF** live on the host; see **`ros2_ws/src/dum_e_description/`** and **`docs/hardware.md`**.
- **Without ROS (e.g. Mac only):** set **`DUM_E_SERIAL_PORT`** to the motor ESP’s USB device (for example `DUM_E_SERIAL_PORT=/dev/cu.usbserial-0001`). **`desktop_app/services/robot_bridge.py`** then sends the same one-line text commands over **USB serial** only — it will **not** also run `ros2 topic pub`. Optional **`DUM_E_SERIAL_BAUD`** (default `115200`). Close **`mpremote`** / Thonny while the app owns the port.
- **BLE (Nordic UART):** on the ESP32 set **`USE_BLE_NUS = True`** in **`config.py`** (needs a **MicroPython build with Bluetooth**). On the laptop: **`DUM_E_BLE=1`**, **`pip install bleak`**, optional **`DUM_E_BLE_NAME`** / **`DUM_E_BLE_ADDRESS`** (same NUS UUIDs as common ESP32 examples). Unset **`DUM_E_SERIAL_PORT`** when using BLE so the bridge does not open USB. USB serial + BLE can both feed **`main.py`** if you still plug in USB for logs, but the desktop should use only one transport.
- **With ROS:** leave **`DUM_E_SERIAL_PORT` unset** and do **not** set **`DUM_E_SKIP_ROS2=1`**. The bridge publishes to **`/dum_e_command`**. Do not enable **`DUM_E_LOCAL_TARGET_TRACK`** in **`desktop_app`** at the same time as the ROS **`track_target_node`**.
- **Dry run (logs only):** set **`DUM_E_SKIP_ROS2=1`** and **no** serial port — no bytes to the robot.

## Serial / dashboard

The main loop reads **lines from stdin** (USB serial). The desktop app is intended to send the same text commands as the REPL. Ensure **`main.py`** is the entry script on the board after deploy.
