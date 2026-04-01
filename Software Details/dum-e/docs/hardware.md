# Hardware inventory

Document major parts as you wire and test them. Update the **Status** column as you go: `planned` → `wired` → `tested`.

## Controllers & compute

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| ESP32 DevKit V1 | 1 | Main MicroPython target | planned |
| ESP32-CAM | 1 | Vision / future perception | planned |

## Motion

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| NEMA 17 stepper motor | 2–4 | Joint actuation | planned |
| DRV8825 stepper driver | 2–4 | Matched to motors | planned |

## Power

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| 12V DC power supply | 1 | Motor / driver rail (verify current) | planned |
| Buck converter | 1 | ESP32 / logic rail from 12V or separate 5V/3.3V | planned |

## Sensing & feedback

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| VL53L0X | 1 | Time-of-flight distance (I2C) | planned |
| HC-SR04 | 1 | Ultrasonic distance | planned |

## Passive & mechanical support

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Capacitors | — | Decoupling / bulk as per schematic | planned |
| Resistors | — | Pull-ups, dividers, LED limits | planned |
| Heat sinks | — | Drivers / regulators as needed | planned |

## Wiring & prototyping

| Component | Qty | Notes | Status |
|-----------|-----|-------|--------|
| Jumper wires | — | Dupont / solid core as appropriate | planned |
| Breadboard / perfboard | — | Bring-up before final layout | planned |

## Placeholders

Add rows here for switches, LEDs, encoders, endstops, or other parts as the design firms up.
