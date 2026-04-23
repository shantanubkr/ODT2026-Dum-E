# DUM-E pick calibration (approach A — measure in hardware)

Use these scripts with the **motor ESP32** on USB (same port as `DUM_E_SERIAL_PORT` in the desktop app). **Quit `mpremote` / Thonny** before running.

## Team inputs (example)

| Quantity | Example | Notes |
|----------|---------|--------|
| Camera ↔ base (horizontal) | **28.5 in** | Use for layout / extrinsics; hand–eye still needs a calibration run. |
| Cup height | **2.39 in** | Document for CAD/IK; **grasp Z** is set by jogging, not by this number alone. |
| Cup width (grasp) | **2.25 in** | Target opening at contact — **tune close angle empirically** and record. |

**Z for pick:** Jog until fingers are at the right height, then **record** `pose_deg` for **hover** (optional) and **grasp**. Suggested **hover** is **0.5–1.0 in** above contact in joint space (achieve by small joint nudges): **hover → descend → close**.

**Gripper:** Open = max; **close** = one value per setup (or per color if you tune four). Record the 5th joint after a good grasp.

## Environment

```bash
cd /path/to/dum-e
source .venv/bin/activate
pip install -r calibration/requirements.txt

export DUM_E_SERIAL_PORT=/dev/cu.usbserial-XXXX
# export DUM_E_SERIAL_BAUD=115200
```

## Scripts (suggested order)

| Script | Purpose |
|--------|---------|
| `named_pose_preview.py` | Print `pose_deg` lines for `home` / `ready` / `down` from `src/robot_kinematics.py`. |
| `send_pose_deg.py` | Send one `pose_deg w u f h ee` line. |
| `jog_pose.py` | Interactive nudge per joint; updates `calibration/.last_pose.json`. |
| `record_pose.py` | Append a labeled pose to `recorded_poses.jsonl`. |

Copy `pick_constants_template.yaml` → `pick_constants.yaml` and fill angles after runs.

## Safety

- E-stop / power within reach.
- Small jog steps first (default 2°).
- Start from `ready` or `home` before moving over the table.
