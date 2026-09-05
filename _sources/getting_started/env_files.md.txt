---
title: Configuring science-jubilee with .env files
---

(env-files)=
# Configuring science-jubilee with .env files

`MachineSession.from_env()` reads all its configuration from environment
variables. Two `.env` files at the repo root cover the two common cases:

## `.env.mock` — offline development

```bash
JUBILEE_TRANSPORT=mock
JUBILEE_CAMERA_CALIB=src/science_jubilee/calibration/camera_params.yaml
# JUBILEE_PIPELINE_DATA=  # override the folder holding gcode_logs/, machine_state.json, traces/
```

Copy to `.env.mock` in the repo root, then:

```python
from science_jubilee.machine_session import MachineSession
session = MachineSession.from_env(".env.mock")
```

The mock replays the last real session recorded in
`pipeline_data/machine_state.json`, so it reports *your* tools and offsets
rather than an invented set. When there is no recorded snapshot, the mock
starts empty (four `None` slots).

## `.env.hardware` — connected machine

```bash
JUBILEE_TRANSPORT=hardware
JUBILEE_ADDRESS=192.168.1.2         # Duet IP
JUBILEE_CAMERA_ADDRESS=192.168.1.55  # optional
JUBILEE_NEOPIXEL_ADDRESS=192.168.1.55 # optional
JUBILEE_CAMERA_CALIB=src/science_jubilee/calibration/camera_params.yaml
JUBILEE_EXPERIMENT_DIR=/path/to/experiment_deck/2026-08-07_experience
# JUBILEE_PIPELINE_DATA=  # override the folder holding gcode_logs/, machine_state.json, traces/
```

The first time you open a hardware session, `RecordingTransport` writes a
snapshot to `pipeline_data/machine_state.json`. Subsequent mock sessions
mirror that snapshot.

## Full variable reference

| Variable | Default | Purpose |
|---|---|---|
| `JUBILEE_TRANSPORT` | `mock` | `mock` or `hardware` |
| `JUBILEE_ADDRESS` | — | Duet IP; required when `TRANSPORT=hardware` |
| `JUBILEE_EXPERIMENT_DIR` | latest interface export | Folder with `deck.json`, labware JSONs, G-code files |
| `JUBILEE_DECK_DEF` | auto-detected | Stem of the deck JSON file |
| `JUBILEE_PIPELINE_DATA` | `<repo>/pipeline_data` | Directory holding `gcode_logs/`, `machine_state.json`, `traces/` |
| `JUBILEE_CAMERA_ADDRESS` | — | Camera server IP, hardware only |
| `JUBILEE_NEOPIXEL_ADDRESS` | — | LED server IP, hardware only |
| `JUBILEE_CAMERA_CALIB` | bundled `camera_params.yaml` | Path to camera calibration |
| `JUBILEE_GCODE_LOG_COPY` | — | Extra named copy of the G-code log for archiving |
| `JUBILEE_RUN_NAME` | pytest test name | Suffix used when naming per-run G-code copies |

Any variable set in the shell overrides the same key in the `.env` file.
