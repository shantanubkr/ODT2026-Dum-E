# State machine (provisional)

These states are a **starting point** and will evolve as behaviors and error handling mature.

| State | Meaning (draft) |
|-------|------------------|
| `BOOT` | One-time startup: hardware init, config load, self-checks |
| `IDLE` | Powered, safe, waiting for commands or triggers |
| `ACTIVE` | Awake and responsive; may accept motion / interaction |
| `WORKING` | Performing a task (e.g. motion sequence, manipulation) |
| `ERROR` | Fault or safety trip; motion restricted until cleared |
| `SLEEP` | Low-activity mode to save power or reduce motion |

Transitions (e.g. `IDLE` → `WORKING`, `*` → `ERROR`) are not fixed yet; implement them in `src/modules/state_machine.py` as the design stabilizes.
