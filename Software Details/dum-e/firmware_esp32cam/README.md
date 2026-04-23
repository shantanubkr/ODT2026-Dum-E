# ESP32-CAM: MJPEG tuning (Arduino + reference for MicroPython)

## Arduino (`esp32-camera` / `esp_camera` init)

In your `setup()` (before `esp_camera_init(&config);`), set:

```c
config.frame_size = FRAMESIZE_QVGA;   // 320×240 — stable, low bandwidth
config.jpeg_quality = 20;             // 0–63; **higher** = more compression / smaller files (less lag)
```

Use the value `20` for a smaller per-frame payload than very low values (e.g. 5–10) which can produce **larger** JPEGs in busy scenes, depending on the sensor driver.

`jpeg_quality` semantics follow **Espressif `esp32-camera`**: see your board package’s `sensor_t` and examples under **Examples → ESP32 → Camera → CameraWebServer**.

## MicroPython (this repo)

`desktop_app/launch_cam.py` pastes a stream server that uses `camera.FRAME_QVGA` and, if supported, `quality=20` in `camera.init(...)`. If the board firmware rejects `quality=`, the script falls back to the two-argument `init` only.

## Laptop / OpenCV

Use `desktop_app/services/camera_stream.py` — **FFmpeg** backend, **buffer size 1**, corrupt frames return `None` so vision does not block on a bad chunk.

See `firmware_esp32cam/arduino_mjpeg_config_snippet.ino` for a drop-in `config` block.
