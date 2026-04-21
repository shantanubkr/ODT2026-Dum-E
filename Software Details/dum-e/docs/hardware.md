# Hardware inventory

This doc matches the **current firmware** (`src/pins.py`, `src/config.py`, `src/modules/motion_controller.py`) and the **CAD / ROS** packages (`ros2_ws/src/dum_e_description/`, reference copy under `dum_hardware/urdf/`).

**CAD vs firmware:** The URDF has **four** revolute joints (`Revolute 7`–`10`); the **gripper** is driven in firmware as a fifth PWM axis (`end_effector`) and may not appear as a separate joint in RViz until bridged (see `ros2_ws/src/dum_e_description/README.md`).

Update the **Status** column as you wire and test: `planned` → `wired` → `tested`.

---

## Controllers & compute

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| ESP32 DevKit (e.g. 30-pin) | 1 | MicroPython; PWM to servos; USB serial for deploy and dashboard | planned |
| ESP32-CAM (optional) | 0–1 | Onboard vision — not required for arm bring-up | planned |

---

## Motion (current build — hobby servos)

Firmware uses **five** PWM servos (50 Hz). The **base** link in CAD has **no motor**; rotation starts at **waist**.

| Servo # | Firmware / CAD name | Role |
|---------|---------------------|------|
| 1 | `waist` | Base rotation (base ↔ waist) |
| 2 | `upper_arm` | Waist ↔ upper arm |
| 3 | `forearm` | Upper arm ↔ forearm |
| 4 | `hand` | Forearm ↔ hand (wrist) |
| 5 | `end_effector` | Gripper open/close |

Joint order in code and logs: `waist`, `upper_arm`, `forearm`, `hand`, `end_effector`.

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Hobby / RC servo (PWM) | 5 | One per row above; torque per link as per mechanical design | planned |

GPIO defaults are in `src/pins.py` (`SERVO_WAIST` 4, `SERVO_UPPER_ARM` 22, `SERVO_FOREARM` 23, `SERVO_HAND` 21, `SERVO_END_EFFECTOR` 19). **Change there when wiring is final.**

**Control:** No panel buttons in the default build (`USE_PHYSICAL_BUTTONS = False` in `config.py`). Use desktop dashboard, USB serial, or REPL. Optional panel buttons use the pins listed in `pins.py` (`BTN_*`).

---

## Power

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| USB cable / 5 V from host | 1 | Powers and programs the ESP32 | planned |
| 5 V rail for servos (bench supply, BEC, or buck from 12 V) | 1 | Servos can draw high peak current; **do not** rely on the ESP32 3.3 V regulator for motor power | planned |
| Common ground | 1 | ESP32 GND tied to servo supply GND for valid PWM and safety | planned |
| Buck / LDO (optional) | 0–1 | If you run logic from a higher-voltage main rail | planned |

---

## Sensing & feedback

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| VL53L0X (ToF) | 0–1 | I2C distance — **not wired in current build**; distance constants in `config.py` are reserved; **no sensor driver** under `src/drivers/` yet | planned |
| HC-SR04 (ultrasonic) | 0–1 | **Not wired in current build** — same as above | planned |

**Firmware:** `SafetyManager` supports a **sensor fault** latch (`set_sensor_error` / `clear_sensor_error`), but nothing in the current `src/` tree calls it until drivers exist.

---

## Passive, mechanical, prototyping

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Capacitors | as needed | Bulk/decoupling on servo supply if long leads or noisy supply | planned |
| Resistors | as needed | Pull-ups if adding I2C or buttons | planned |
| Jumper wires | — | Dupont / solid core | planned |
| Breadboard / perfboard | — | Bring-up | planned |

---

## ROS / simulation (not on the robot PCB)

| Item | Notes |
|------|--------|
| `ros2_ws/src/dum_e_description/` | Canonical URDF, meshes, launch for RViz |
| `dum_hardware/urdf/` | Reference xacro aligned with description package |
| `dum-e.trans` | ROS 1–style transmissions; replace with **ros2_control** if you simulate in Gazebo later |

---

## Components table (electronics documentation)

Use this for approval / BOM-style write-ups. Adjust quantities if you omit optional parts.

| Component | Quantity | Purpose | Justification |
|-----------|----------|---------|---------------|
| ESP32 development board | 1 | Run MicroPython, generate PWM for servos, USB for programming and serial dashboard | Single board with enough GPIO and USB; matches firmware and deploy flow (`mpremote`). |
| Hobby (RC) servo motor | 5 | Actuate waist, upper arm, forearm, hand, and gripper | PWM servos give settable angles for each joint; fits a desktop arm and matches CAD joint count (four arm DOF + gripper in firmware). |
| 5 V power source for servos | 1 | Supply motor current without loading the ESP32 regulator | Servos draw large peak current; a dedicated 5 V rail avoids brownouts and damage to the MCU. |
| Common electrical ground | 1 (net) | Connect ESP32 GND to servo supply GND | Required so PWM signals and returns are referenced correctly and safely. |
| USB cable | 1 | Power and flash the ESP32 from a PC | Needed for `deploy/` scripts and REPL during development. |
| Jumper wires / breadboard | as needed | Route signals and power during bring-up | Standard for prototyping before a fixed PCB or harness. |

---

## Placeholders

Add rows for any **panel buttons**, **E-stop**, **encoders**, **LEDs**, or **ESP32-CAM** when those become part of the wired build.
