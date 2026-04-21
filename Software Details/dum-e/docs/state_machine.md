# State machine

States are defined in **`src/modules/state_machine.py`** as **`States.*`** string constants. Use **`change_state()`** for transitions (logged); do not assign raw strings.

## States

| State | Meaning in code |
|-------|------------------|
| `BOOT` | Initial value after `StateMachine()`; cleared on first **`boot()`** in `main.py` (or desktop init in **`dum_e_runtime.py`**) by transitioning to **`ACTIVE`**. |
| `ACTIVE` | Default “awake” running state after boot; user activity keeps the activity timer fresh. While behavior is **`"idle"`**, **`BehaviorEngine`** runs **curious wander** (motion every 2–5 s) when **`SafetyManager.can_move()`** allows. |
| `SAD` | **Mood** state after negative sentiment: **`express_sad`** animation, then **`sad_hold`** (slouch). No wander. Exits to **`ACTIVE`** on almost any routed command (except **`status`** / **`history`**) or on **GREET** / **HAPPY** / **BYE** sentiment. |
| `WORKING` | Set by **`CommandRouter`** for **`MOVE_TO`** when there is **no** named pose in metadata — placeholder path (“trajectory TBD” in logs). |
| `ERROR` | Legacy / reserved; **`STOP`** no longer lands here — use **`STOP_COOLDOWN`**. |
| `STOP_COOLDOWN` | After **`STOP`**: move to **`home`**, then when home is reached **`trigger_emergency_stop()`** and hold **10 s** (`STOP_COOLDOWN_MS`) with **no** other motion or commands (duplicate **`STOP`** ignored). Then estop clears automatically → **`ACTIVE`** + **`idle`** (wander enabled again). |
| `DATA_ERROR` | Bad serial / timeout / coords: call **`CommandRouter.route_data_fault(reason)`** — log, **`error_nod`** (waist shake), stub error sound log; **5 s** later (`DATA_ERROR_RECOVERY_MS`) auto **home** → **`ACTIVE`** + **`idle`**. Other commands ignored until recovery or **`RESET`**. |
| `SLEEP` | Entered when **`SLEEP_TIMEOUT_MS`** passes since last activity (unless already sleeping). **`STOP_COOLDOWN`**, **`DATA_ERROR`**, and **`ERROR`** return early so sleep logic does not run. There is **no separate `IDLE` state** — inactivity goes straight to **sleep**. |

## Behaviors tied to states (related, not 1:1)

- **`SLEEP`**: `BehaviorEngine` is set to **`"none"`** (no wander).
- **`ACTIVE`** with behavior **`"idle"`**: curious wander + optional **`idle_look_at`** inspect (vision / `IDLE_LOOK_AT` command).
- **`RESET`**: clears estop and fault timers, transitions to **`ACTIVE`**, behavior **`"idle"`**, arm to **`home`** pose.

## Commands that change state (via `CommandRouter`)

| Action | Typical transition |
|--------|---------------------|
| `STOP` | → **`STOP_COOLDOWN`**, move **`home`**, then 10 s hold at home (estop); then auto **`ACTIVE`** + **`idle`**. Second **`STOP`** during hold is ignored. |
| `RESET` | → **`ACTIVE`**, estop off, fault timers cleared, `home` |
| `GREET` | → **`ACTIVE`**, **`greeting`** behavior (move to **home** pose, **hand nod**, then **`idle`**) |
| `dance` | → **`ACTIVE`**, **`dancing`** behavior (rhythmic sway ~**`DANCE_DURATION_MS`**, then **`idle`**) |
| `MOVE_TO` (no pose) | → **`WORKING`**, thinking behavior (trajectory still TBD in router) |
| `idle_look_at` | Stays **`ACTIVE`**; **`begin_idle_inspect(waist, hand)`** if behavior is **`"idle"`** |

## Activity timer

**`mark_activity()`** resets the inactivity clock on commands (firmware **`main.py`**, desktop **`dum_e_runtime.mark_activity()`**). Waking from **`SLEEP`** on new input sets **`ACTIVE`** and **`idle`** behavior.

Desktop **`DesktopAppRuntime.send_text_command()`** calls **`mark_activity()`** so voice/text is heard even when the phrase does not parse to a routed action.

See **`src/config.py`** for **`SLEEP_TIMEOUT_MS`**, **`STOP_COOLDOWN_MS`**, **`DATA_ERROR_RECOVERY_MS`**, and wander tuning (**`IDLE_WANDER_*`**, **`IDLE_INSPECT_*`**).
