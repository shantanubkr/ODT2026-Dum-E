# Architecture

This project is organized so that hardware details stay in one layer and system behavior stays in another. The goal is a **thin** entrypoint and **modular** growth as DUM-E gets more capable.

## Layout

- **`src/utils/`** — Small shared helpers: logging, timing, and other cross-cutting utilities. No hardware imports here.
- **`src/drivers/`** — **Hardware only.** Each driver talks to one kind of device (stepper, ToF, ultrasonic, PIR, buzzer). Drivers expose a small API; they do not decide *why* a motor moves or when to stop for safety.
- **`src/modules/`** — **System logic.** Motion planning hooks, safety policy, command parsing, state machine, behaviors, and perception orchestration live here. Modules call drivers and other modules; they encode rules and coordination.
- **`src/interfaces/`** — Optional ways to talk to the robot (serial/REPL-style, Bluetooth, web). These should translate external input into commands or events the modules understand, without duplicating driver code.
- **`deploy/`** — Scripts to copy firmware from your machine to the ESP32 (e.g. `mpremote`) and to reset the board. Not loaded on the device.
- **`test/`** — Starting point for automated checks or host-side scaffolds. Full hardware tests will still need the real board.

## Principles

1. **Drivers** only talk to hardware (GPIO, I2C, timing for steps, etc.).
2. **Modules** implement policy: when to move, when to refuse movement, how to parse a line of text into an action.
3. **`main.py`** should stay **thin**: wire up config, construct objects, call `boot()` / `loop()` or similar, and delegate everything else.

As the codebase grows, keep new hardware in `drivers/` and new “what should DUM-E do?” logic in `modules/`.
