# Hardware inventory

This doc matches the **current build**: **ESP32**, **four PWM servos** (arm only), **dedicated servo power**, and a **camera** used with **laptop-side** vision (`desktop_app/`). CAD / ROS URDF and meshes: **`ros2_ws/src/dum_e_description/`** (canonical).

**CAD vs firmware:** The URDF has **four** revolute joints (`Revolute 7`–`10`); firmware joint order matches (**waist**, **upper_arm**, **forearm**, **hand**).

Update the **Status** column as you wire and test: `planned` → `wired` → `tested`.

---

## Controllers & compute

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| ESP32 DevKit (e.g. 30-pin) | 1 | MicroPython; PWM to servos; USB serial for deploy and dashboard | planned |
| Laptop | 1 | Dashboard, speech, vision, optional ROS — not on the robot PCB | planned |

---

## Motion — four PWM servos (arm)

Firmware uses **four** hobby servos (50 Hz) for the arm. The **base** link in CAD has **no motor**; rotation starts at **waist**.

| Servo # | Firmware / CAD name | Role |
|---------|---------------------|------|
| 1 | `waist` | Base rotation (base ↔ waist) |
| 2 | `upper_arm` | Waist ↔ upper arm |
| 3 | `forearm` | Upper arm ↔ forearm |
| 4 | `hand` | Forearm ↔ hand (wrist) |

Joint order in code and logs: `waist`, `upper_arm`, `forearm`, `hand`.

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Hobby / RC servo (PWM), arm | 4 | Per link torque | planned |

GPIO defaults are in `src/pins.py` (`SERVO_WAIST`–`SERVO_HAND`, or PCA9685 channels when `USE_PCA9685` is True). **Change there when wiring is final.**

Mechanical **upright / home** is defined in `src/config.py` as **`UPRIGHT_POSE_DEG`** (and `robot_kinematics.UPRIGHT_FIRMWARE_DEG`): by default all joints **90°** after PWM calibration so the arm stands stacked neutral.

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
| `dum-e.trans` | ROS 1–style transmissions; replace with **ros2_control** if you simulate in Gazebo later |

---

## Components table (electronics documentation)

| Component | Quantity | Purpose | Justification |
|-----------|----------|---------|---------------|
| ESP32 development board | 1 | Run MicroPython, PWM for servos, USB for programming and serial dashboard | Single board with enough GPIO; matches firmware and deploy flow (`mpremote`). |
| Hobby (RC) servo motors | 4 | Arm joints (waist … hand) | PWM servos per mechanical design. |
| 5 V power source for servos | 1 | Supply motor current without loading the ESP32 regulator | Peak current; dedicated rail avoids brownouts. |
| Common electrical ground | 1 (net) | ESP32 GND to servo supply GND | Required for valid PWM references. |
| USB cable | 1 | Power and flash ESP32 from PC | For `deploy/` scripts and REPL. |
| Camera (with laptop) | 1 | Vision / idle behaviors on host | Processing in `desktop_app/`, not on ESP32. |
| Jumper wires / breadboard | as needed | Bring-up | Standard prototyping. |

---

## Placeholders

Add rows for **panel buttons**, **E-stop**, **encoders**, or **LEDs** only if those become part of the wired build.
