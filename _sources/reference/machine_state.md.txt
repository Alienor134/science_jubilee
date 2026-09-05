---
title: Machine state and snapshots
---

(machine-state)=
# Machine state and snapshots

`science_jubilee.machine_state.resolve()` is the single place that
answers: *"what does the machine look like right now?"* It's used by
both the mock transport (to replay the last real session's state) and
by the digital twin (to place tool models correctly).

## Signature

```python
def resolve(
    address: Optional[str] = None,
    saved_path: Optional[Path] = None,
    allow_live: bool = True,
) -> tuple[dict, str]:
    ...
```

Returns `(state, source_label)`, where `source_label` is one of
`"live"`, `"snapshot"`, or `"empty"`.

## Fallback chain

The resolver walks four steps in order, returning the first that
succeeds:

1. **Live query** — `HTTPTransport.get_machine_summary(address)`, only if `allow_live` and the port is reachable (0.3 s TCP pre-check).
2. **Snapshot at explicit path** — if `saved_path` was passed and exists.
3. **Snapshot for known address** — `machine.json` in `pipeline_data_dir()`, if its recorded address matches.
4. **Empty state** — a placeholder with 4 unnamed tools and offsets `[0, 0, -400]` used only when neither hardware nor snapshot exists.

Every step is traced in the HTML recap via
`trace.session().section("Machine state", reset=True)`.

## The snapshot: `machine.json`

Schema:

```json
{
  "source": "live",
  "head_position": [x, y, z],
  "active_tool": 0,
  "tools": [
    {
      "id": 0,
      "name": "pipette",
      "park": [x, y, z],
      "offsets": [dx, dy, dz],
      "blend": "pipette.blend",
      "park_post": "tpost0.g"
    },
    ...
  ]
}
```

Written to `pipeline_data/machine.json`. Used as the fallback for mock
mode when the hardware is offline.

## Pipeline data layout

```
pipeline_data/
├── machine.json              ← snapshot (from `resolve`)
├── gcode_logs/
│   └── 2026-09-05_12-34-56-my_script.gcode
└── traces/
    └── my_script.html        ← trace recap
```

Override the root with `JUBILEE_PIPELINE_DATA` — see
[env files](../getting_started/env_files.md).

## Reading it yourself

```python
from science_jubilee.machine_state import resolve

state, source = resolve(address="10.0.3.48", allow_live=True)
print(f"Loaded state from: {source}")
for tool in state["tools"]:
    print(tool["id"], tool["name"], tool["park"])
```
