# Pin map

**All assignments below are placeholders.** Update this table after the schematic and breadboard layout are finalized, then mirror changes in `src/pins.py`.

| Component / subsystem | Signal | GPIO pin | Voltage | Notes |
|----------------------|--------|----------|---------|-------|
| Stepper 0 (example) | STEP | TBD | 3.3V logic | DRV8825 |
| Stepper 0 (example) | DIR | TBD | 3.3V logic | |
| Stepper 0 (example) | ENABLE | TBD | 3.3V logic | Active level per driver |
| Ultrasonic HC-SR04 | TRIG | TBD | 3.3V | |
| Ultrasonic HC-SR04 | ECHO | TBD | 3.3V / divider if 5V sensor | |
| VL53L0X | SDA | TBD | 3.3V | I2C |
| VL53L0X | SCL | TBD | 3.3V | I2C |
| Buzzer | SIG | TBD | 3.3V or transistor drive | Active vs passive |
| Emergency stop | INPUT | TBD | 3.3V | Pull-up / debounce |
