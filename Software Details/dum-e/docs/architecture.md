# Architecture

Firmware keeps **hardware** in one layer and **policy / behavior** in another. The ESP32 entrypoint stays **thin**: construct objects, `boot()`, then a `loop()` that polls serial, updates motion, behaviors, and activity timeouts.

## Repository layout (firmware)

| Path | Role |
|------|------|
| `src/main.py` | Entry: `StateMachine`, `IntentParser`, `BehaviorEngine`, `SafetyManager`, `MotionController`, `CommandRouter`; non-blocking stdin; optional physical buttons when `USE_PHYSICAL_BUTTONS` is True. |
| `src/config.py` | Timing, joint limits, PWM calibration, feature flags (e.g. `USE_PHYSICAL_BUTTONS`). |
| `src/pins.py` | GPIO for servos and optional `BTN_*` pins. |
| `src/backend/` | **`command_schema.py`** — `Actions`, `Command`. **`command_router.py`** — `CommandRouter` (routes `Command` to motion, safety, behaviors, status/history) and **`build_command_from_parse_result()`** (maps parser output to `Command`). |
| `src/modules/` | **`state_machine.py`** — `States` and transitions. **`command_parser.py`** — text → `{type, command, args}`. **`intent_parser.py`** — extends parser with **sentiment** (`GREET` / `BYE` / `HAPPY` / `SAD` / `NEUTRAL`) for expression behaviors. **`motion_controller.py`** — five PWM servos, named poses (`home`, `ready`, `down`). **`behavior_engine.py`** — idle / greeting / thinking + `express_*` behaviors. **`safety_manager.py`** — emergency stop (+ optional fault latch); `can_move()` gates motion in the router. |
| `src/drivers/` | **`stepper.py`** — `Servo` (MicroPython `PWM` hobby servo; filename is legacy). **`panel_button.py`** — `Button` (debounced) if **`USE_PHYSICAL_BUTTONS`** is enabled. Vision runs on the **laptop** (`desktop_app/`), not on the ESP32. |
| `src/utils/` | Logging, timers — no hardware imports. |
| `deploy/` | Host scripts (`mpremote`) — not flashed to the device. |
| `test/` | Host-side or future scaffolds. |

## Host / desktop (not on the ESP32)

| Path | Role |
|------|------|
| `desktop_app/` | Dashboard and **`dum_e_runtime.py`**: imports the same `backend` + `modules` under CPython (with a small time shim), optional **`LaptopMotionController`** sim, or **`RobotBridge`** to publish string commands to ROS 2 (`/dum_e_command`) when not skipping ROS. |
| `src/interfaces/robot_bridge.py` | **`RobotBridge`** — maps high-level `Command` actions to ROS-side strings; used from **`desktop_app`**, **not** from `src/main.py` on the board. |

## Data flow (firmware)

1. **stdin line** → `IntentParser.parse()` → sentiment may run **`BehaviorEngine.run_behavior()`** for `express_*` → **`build_command_from_parse_result()`** → **`CommandRouter.route()`**.
2. **`MotionController.update()`** each loop tick interpolates toward target angles (smooth motion).
3. **`BehaviorEngine.update()`** runs the current behavior tick (expressions, timed greeting/thinking).
4. **`update_activity_state()`** (firmware) or **`_update_desktop_inactivity()`** (desktop) moves **ACTIVE → SLEEP** after **`SLEEP_TIMEOUT_MS`**; activity resets the timer. There is no intermediate **IDLE** machine state.

## Principles

1. **Drivers** talk to GPIO/PWM only; they do not encode “why” the arm moves.
2. **Modules + backend** encode commands, safety, and behaviors.
3. **`main.py`** wires objects and runs the loop — minimal logic.

New on-robot hardware belongs in `src/drivers/`; new command or policy behavior in `src/modules/` or `src/backend/` as appropriate.
