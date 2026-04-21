/*
 * DUM-E — ESP32-CAM: camera config snippet for Arduino (esp32-camera)
 *
 * Merge these assignments into the camera_config_t used before esp_camera_init()
 * in your WebServer or MJPEG example (e.g. File → Examples → ESP32 → Camera).
 *
 * Build target: your ESP32-CAM board. Requires board support package with esp_camera.
 */
#if __has_include("esp_camera.h")
#include "esp_camera.h"
#endif

// Call from setup() after you declare camera_config_t config = { };
static void dum_e_apply_camera_mjpeg_tuning(camera_config_t *config) {
  if (config == nullptr) {
    return;
  }
  // Stable, low-latency stream: 320×240
  config->frame_size = FRAMESIZE_QVGA;
  // Smaller per-frame size vs very low “quality” numbers in some scenes (per driver, 0–63)
  config->jpeg_quality = 20;
}

/*
Example placement (pseudo-code):

  camera_config_t config;
  // ... set pins, xclk, ledc, sensor, sccb, sccb_port, reset, pwdn, etc. ...

  dum_e_apply_camera_mjpeg_tuning(&config);

  if (esp_camera_init(&config) != ESP_OK) {
    // handle error
  }
*/
