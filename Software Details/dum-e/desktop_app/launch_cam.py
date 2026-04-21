"""launch_cam.py — one-command camera bringup.

Usage:
    python desktop_app/launch_cam.py

What it does:
    1. Prompts for WiFi SSID + password (or reads WIFI_SSID / WIFI_PASS env vars)
    2. Opens the ESP32-CAM serial port directly via pyserial (no mpremote)
    3. Pastes the stream-server script into the MicroPython REPL line by line
    4. Waits until the board prints its IP address
    5. Launches test_vision.py pointed at that IP

Press Ctrl+C at any time to shut everything down.
"""

import os
import re
import subprocess
import sys
import threading
import time

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run:  pip install pyserial")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PORT      = "/dev/tty.usbserial-10"
BAUD      = 115200
STREAM_PORT = 81
FRAME_SIZE  = "camera.FRAME_QVGA"   # 320×240 — good balance of speed vs quality
WIFI_TIMEOUT_S = 20                  # seconds the board waits to join WiFi
IP_TIMEOUT_S   = WIFI_TIMEOUT_S + 10 # total host-side wait for CAM_IP line

# ---------------------------------------------------------------------------
# MicroPython stream-server — pasted into the live REPL
# ---------------------------------------------------------------------------

def build_script(ssid: str, password: str) -> str:
    """Return the complete MicroPython script as a single string."""
    return f"""\
import network, socket, camera, time

wifi = network.WLAN(network.STA_IF)
wifi.active(True)
wifi.connect({ssid!r}, {password!r})

dl = time.ticks_add(time.ticks_ms(), {WIFI_TIMEOUT_S * 1000})
while not wifi.isconnected():
    if time.ticks_diff(dl, time.ticks_ms()) <= 0:
        print('WIFI_FAIL')
        raise SystemExit
    time.sleep(0.2)

ip = wifi.ifconfig()[0]
print('CAM_IP:' + ip)

camera.init(0, format=camera.JPEG, framesize={FRAME_SIZE})

srv = socket.socket()
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('', {STREAM_PORT}))
srv.listen(1)
print('STREAM_READY')

while True:
    conn, _ = srv.accept()
    conn.send(b'HTTP/1.1 200 OK\\r\\nContent-Type: multipart/x-mixed-replace; boundary=frame\\r\\n\\r\\n')
    try:
        while True:
            img = camera.capture()
            conn.send(b'--frame\\r\\nContent-Type: image/jpeg\\r\\n\\r\\n' + img + b'\\r\\n')
    except:
        conn.close()
"""

# ---------------------------------------------------------------------------
# Serial REPL helpers
# ---------------------------------------------------------------------------

def wait_for_prompt(ser: serial.Serial, timeout: float = 5.0) -> bool:
    """Drain input until we see '>>> ', return True on success."""
    deadline = time.time() + timeout
    buf = b""
    while time.time() < deadline:
        chunk = ser.read(ser.in_waiting or 1)
        buf += chunk
        if b">>> " in buf or b"... " in buf:
            return True
    return False


def send_line(ser: serial.Serial, line: str):
    ser.write((line + "\r\n").encode())
    time.sleep(0.05)   # small gap so the board can echo + process


def read_output(ser: serial.Serial,
                collected: list[str],
                stop: threading.Event):
    """Background thread: read serial bytes, split into lines, print + collect."""
    buf = ""
    while not stop.is_set():
        try:
            raw = ser.read(ser.in_waiting or 1)
        except Exception:
            break
        if not raw:
            continue
        buf += raw.decode(errors="replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip("\r")
            if line:
                print(f"[ESP32-CAM] {line}")
                collected.append(line)

# ---------------------------------------------------------------------------
# Credential helper
# ---------------------------------------------------------------------------

def get_wifi_credentials() -> tuple[str, str]:
    ssid = os.environ.get("WIFI_SSID") or input("WiFi SSID: ").strip()
    pwd  = os.environ.get("WIFI_PASS") or input("WiFi Password: ").strip()
    return ssid, pwd

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ssid, password = get_wifi_credentials()
    script = build_script(ssid, password)

    print(f"\nOpening {PORT} at {BAUD} baud...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
    except serial.SerialException as exc:
        print(f"ERROR: Could not open serial port: {exc}")
        sys.exit(1)

    time.sleep(0.5)                 # let the port settle

    # Interrupt any running script, get back to >>>
    ser.write(b"\r\n\x03\x03\r\n") # Ctrl+C twice
    time.sleep(0.3)
    ser.reset_input_buffer()

    if not wait_for_prompt(ser, timeout=5):
        print("WARNING: Could not confirm >>> prompt — continuing anyway...")

    # Start background reader
    collected: list[str] = []
    stop_event = threading.Event()
    reader = threading.Thread(
        target=read_output, args=(ser, collected, stop_event), daemon=True
    )
    reader.start()

    # Use MicroPython paste mode (Ctrl+E … Ctrl+D) so the entire script is
    # sent as one block — avoids the REPL mis-indenting lines inside loops.
    print("Sending stream-server script to ESP32-CAM (paste mode)...")
    ser.write(b"\x05")              # Ctrl+E — enter paste mode
    time.sleep(0.2)
    ser.write(script.encode())      # send the full script
    time.sleep(0.1)
    ser.write(b"\x04")              # Ctrl+D — execute

    # Wait for the board to connect to WiFi and print its IP
    print(f"Waiting up to {IP_TIMEOUT_S}s for WiFi + IP...")
    deadline = time.time() + IP_TIMEOUT_S
    ip = None
    while time.time() < deadline:
        for entry in collected:
            m = re.search(r"CAM_IP:(\d+\.\d+\.\d+\.\d+)", entry)
            if m:
                ip = m.group(1)
                break
            if entry.strip() == "WIFI_FAIL":
                print("\nERROR: ESP32-CAM could not join WiFi. Check SSID / password.")
                stop_event.set()
                ser.close()
                sys.exit(1)
        if ip:
            break
        time.sleep(0.3)

    if not ip:
        print("\nERROR: No IP received within timeout.")
        print("Tips: correct SSID? 2.4 GHz network? Board in range?")
        stop_event.set()
        ser.close()
        sys.exit(1)

    stream_url = f"http://{ip}:{STREAM_PORT}/stream"
    print(f"\nStream live at {stream_url}")
    print("Launching vision test... (press q in the OpenCV window to quit)\n")

    vision_script = os.path.join(os.path.dirname(__file__), "test_vision.py")
    try:
        subprocess.run([sys.executable, vision_script, stream_url], check=False)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nShutting down...")
        stop_event.set()
        ser.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
