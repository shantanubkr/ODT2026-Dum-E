# Hardware inventory

This doc matches the **current build**: **ESP32**, **five PWM servos**, **dedicated servo power**, and a **camera** used with **laptop-side** vision (`desktop_app/`). CAD / ROS packages: `ros2_ws/src/dum_e_description/`, reference copy under `dum_hardware/urdf/`.

**CAD vs firmware:** The URDF has **four** revolute joints (`Revolute 7`–`10`); the **gripper** is driven in firmware as a fifth PWM axis (`end_effector`) and may not appear as a separate joint in RViz until bridged (see `ros2_ws/src/dum_e_description/README.md`).

Update the **Status** column as you wire and test: `planned` → `wired` → `tested`.

---

## Controllers & compute

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| ESP32 DevKit (e.g. 30-pin) | 1 | MicroPython; PWM to servos; USB serial for deploy and dashboard | planned |
| Laptop | 1 | Dashboard, speech, vision, optional ROS — not on the robot PCB | planned |

---

## Motion — five PWM servos

Firmware uses **five** hobby servos (50 Hz): **four larger** units for the arm, **one smaller** for the gripper (`end_effector`). The **base** link in CAD has **no motor**; rotation starts at **waist**.

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
| Hobby / RC servo (PWM), arm | 4 | Larger units per link torque | planned |
| Hobby / RC servo (PWM), gripper | 1 | Smaller unit for end effector | planned |

GPIO defaults are in `src/pins.py` (`SERVO_WAIST` 4, `SERVO_UPPER_ARM` 22, `SERVO_FOREARM` 23, `SERVO_HAND` 21, `SERVO_END_EFFECTOR` 19). **Change there when wiring is final.**

**Control:** Default build has **no** physical panel buttons (`USE_PHYSICAL_BUTTONS = False` in `config.py`). Use **desktop dashboard**, **USB serial**, or **REPL**.

---

## Power

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| USB cable / 5 V from host | 1 | Powers and programs the ESP32 | planned |
| 5 V rail for servos (bench supply, BEC, or buck) | 1 | Servos draw high peak current; **do not** power servos from the ESP32 3.3 V regulator | planned |
| Common ground | 1 | ESP32 GND tied to servo supply GND for valid PWM | planned |
| Buck / LDO (optional) | 0–1 | If logic runs from a higher-voltage main rail | planned |

---

## Camera & vision

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Camera module (e.g. USB webcam or board-mounted module) | 1 | Feeds the **laptop**; processing lives in `desktop_app/` (OpenCV, optional idle look-at). **ESP32 firmware does not run vision.** | planned |

---

## Passive, mechanical, prototyping

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Capacitors | as needed | Bulk/decoupling on servo supply if long leads or noisy supply | planned |
| Resistors | as needed | e.g. pull-ups if you add I2C later | planned |
| Jumper wires | — | Dupont / solid core | planned |
| Breadboard / perfboard | — | Bring-up | planned |

---

## ROS / simulation (not on the robot PCB)

| Item | Notes |
|------|-------|
| `ros2_ws/src/dum_e_description/` | Canonical URDF, meshes, launch for RViz |
| `dum_hardware/urdf/` | Reference xacro aligned with the description package |
| `dum-e.trans` | ROS 1–style transmissions; replace with **ros2_control** if you simulate in Gazebo later |

---

## Components table (electronics documentation)

| Component | Quantity | Purpose | Justification |
|-----------|----------|---------|---------------|
| ESP32 development board | 1 | Run MicroPython, PWM for servos, USB for programming and serial dashboard | Single board with enough GPIO; matches firmware and deploy flow (`mpremote`). |
| Hobby (RC) servo motors | 5 | Four arm joints + gripper | PWM servos; four larger + one small end effector per mechanical design. |
| 5 V power source for servos | 1 | Supply motor current without loading the ESP32 regulator | Peak current; dedicated rail avoids brownouts. |
| Common electrical ground | 1 (net) | ESP32 GND to servo supply GND | Required for valid PWM references. |
| USB cable | 1 | Power and flash ESP32 from PC | For `deploy/` scripts and REPL. |
| Camera (with laptop) | 1 | Vision / idle behaviors on host | Processing in `desktop_app/`, not on ESP32. |
| Jumper wires / breadboard | as needed | Bring-up | Standard prototyping. |

---

## Placeholders

Add rows for **panel buttons**, **E-stop**, **encoders**, or **LEDs** only if those become part of the wired build.
