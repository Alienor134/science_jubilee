---
title: Every environment variable, explained
---

(environment-reference)=
# Every environment variable, explained

Every variable `science-jubilee` reads at runtime. Setting them via
`.env` file (see [env files](../getting_started/env_files.md)) is
preferred over exporting into your shell.

## Transport

| Variable | Values | Default | Meaning |
|---|---|---|---|
| `JUBILEE_TRANSPORT` | `mock`, `hardware` | `mock` | Which transport `from_env()` builds. |
| `JUBILEE_ADDRESS` | IP or hostname | *unset* | Duet address. **Required** when transport=`hardware`. |

## Experiment layout

| Variable | Default | Meaning |
|---|---|---|
| `JUBILEE_EXPERIMENT_DIR` | latest under `experiments/` | Folder containing `deck.json`, labware JSONs, source gcode. |
| `JUBILEE_DECK_DEF` | auto-detect single `.json` in experiment dir | Deck definition filename. |
| `JUBILEE_PIPELINE_DATA` | `<package>/pipeline_data` | Root of runtime outputs (gcode logs, snapshot, traces). |
| `JUBILEE_GCODE_LOG_COPY` | *unset* | Extra path to copy every gcode log to (e.g. an SD card). |
| `JUBILEE_RUN_NAME` | `Path(sys.argv[0]).stem` | Overrides the trace HTML filename. |

## Attached peripherals

| Variable | Meaning |
|---|---|
| `JUBILEE_CAMERA_ADDRESS` | OctoPi camera server IP; omit to skip camera. |
| `JUBILEE_NEOPIXEL_ADDRESS` | LED server IP; omit to skip Neopixel wiring. |
| `JUBILEE_CAMERA_CALIB` | Path to `camera_params.yaml` from `calibrate_camera.py`. |

## Twin & downstream tools

| Variable | Meaning |
|---|---|
| `JUBILEE_TWIN_TOOL_ASSETS` | Extra directories the digital twin scans for tool `.blend` files (colon-separated). |

## Resolution order

For every path variable, the search is:

1. Explicit `.env` value (or shell export)
2. Installed entry point (`jubilee.paths`)
3. Package default (relative to the `science_jubilee` install)

The `MachineSession.from_env()` docstring is the ground truth if this
table drifts — look at [`machine_session.py`](https://github.com/Jubilee-CSL/science-jubilee/blob/core-app/src/science_jubilee/machine_session.py).
