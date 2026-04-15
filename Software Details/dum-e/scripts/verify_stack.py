#!/usr/bin/env python3
"""
Run automated checks for DUM-E dashboard + runtime (no ROS 2 required here).

ROS2: on Ubuntu/WSL after `colcon build` + `source install/setup.bash`, run:
  ros2 run dum_e_controller dum_e_state_manager
  ros2 topic echo /joint_states
"""
from __future__ import annotations

import os
import subprocess
import sys


def run_py(cwd: str, env: dict, code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_flask_sim() -> bool:
    """Laptop motion sim: GET /status, POST commands."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bs = os.path.join(base, "backend_server")
    env = {**os.environ, "DUM_E_SIM_MOTION": "1"}
    code = r"""
import importlib
import app as a
c = a.app.test_client()
r = c.get("/status")
assert r.status_code == 200, r.data
j = r.get_json()
assert j.get("simulation") is True, j
assert j.get("ros_state") is None, j
assert "state" in j and "pose" in j
# home via action
r2 = c.post("/command", json={"action": "move_home"})
assert r2.status_code == 200, r2.get_json()
# hello via text
r3 = c.post("/command", json={"text": "hello"})
assert r3.status_code == 200, r3.get_json()
print("FLASK_SIM_OK")
"""
    p = run_py(bs, env, code)
    if p.returncode != 0 or "FLASK_SIM_OK" not in (p.stdout + p.stderr):
        print("--- sim stdout ---\n", p.stdout)
        print("--- sim stderr ---\n", p.stderr)
        return False
    print("[ok] Flask + DUM_E_SIM_MOTION=1")
    return True


def test_flask_bridge_skip_ros() -> bool:
    """RobotBridge path without calling ros2 CLI."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bs = os.path.join(base, "backend_server")
    env = {
        **os.environ,
        "DUM_E_SIM_MOTION": "",
        "DUM_E_SKIP_ROS2": "1",
    }
    # Unset SIM so unsetenv - clear DUM_E_SIM_MOTION
    env.pop("DUM_E_SIM_MOTION", None)
    env["DUM_E_SIM_MOTION"] = "0"  # not in ("1","true","yes")
    code = r"""
import app as a
c = a.app.test_client()
r = c.get("/status")
j = r.get_json()
assert j.get("simulation") is False, j
assert isinstance(j.get("pose"), dict), j.get("pose")
r2 = c.post("/command", json={"action": "greet"})
assert r2.status_code == 200
j2 = c.get("/status").get_json()
assert j2.get("ros_state") == "HELLO", j2
c.post("/command", json={"action": "move_home"})
j3 = c.get("/status").get_json()
assert j3.get("ros_state") == "IDLE", j3
r3 = c.post("/command", json={"text": "ready"})
assert r3.status_code == 200
assert c.get("/status").get_json().get("ros_state") == "READY"
c.post("/command", json={"action": "stop"})
j4 = c.get("/status").get_json()
assert j4.get("ros_state") == "ERROR", j4
print("FLASK_BRIDGE_OK")
"""
    p = run_py(bs, env, code)
    if p.returncode != 0 or "FLASK_BRIDGE_OK" not in (p.stdout + p.stderr):
        print("--- bridge stdout ---\n", p.stdout)
        print("--- bridge stderr ---\n", p.stderr)
        return False
    print("[ok] Flask + RobotBridge + DUM_E_SKIP_ROS2=1 (ros_state + (ROS) Publishing log only)")
    return True


def compile_ros_node() -> bool:
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    node = os.path.join(
        base,
        "ros2_ws",
        "src",
        "dum_e_controller",
        "dum_e_controller",
        "dum_e_state_manager.py",
    )
    if not os.path.isfile(node):
        print("[skip] ROS node file missing:", node)
        return True
    r = subprocess.run([sys.executable, "-m", "py_compile", node], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        return False
    print("[ok] py_compile dum_e_state_manager.py")
    return True


def main() -> int:
    ok = True
    ok = compile_ros_node() and ok
    ok = test_flask_sim() and ok
    ok = test_flask_bridge_skip_ros() and ok
    print()
    print("Note: Full ROS pipeline needs Ubuntu/WSL with ros2 + colcon; this machine has no ros2 in PATH.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
