---
title: Design a new tool
---

(new-tool)=
(tool-plugin-guide)=
# Design a new tool

A "new tool" for Jubilee has two halves: a physical assembly that mounts
on the toolchanger, and a Python plugin that exposes it to
`science-jubilee`. Both halves live in **the same repository** — the
hardware CAD, the firmware macros, and the Python code all ship together.

This page walks through both halves in order.

## Step 1 — Hardware

Before writing any Python, you need a working physical tool. The
existing hardware guides in the Build section cover the pieces:

- [Designing custom tools](../building/designing_custom_tools.md) — CAD conventions and the tool-template STL that guarantees the balls and wedge plate are placed correctly
- [Parking posts](../building/parking_posts.md) — where the tool lives when it's not on the carriage
- [Tool offsets](../building/tool_offsets.md) — how to measure the tool's active point in the machine coordinate system
- [Tool postrequisites](../building/tool_postreqs.md) — the calibration procedure once assembly is done

You do **not** need to ship any of the calibration output (parking-post
coordinates, tool offsets) with the plugin — those are machine-specific.
Your plugin ships zeroed templates; each user's calibration notebook
fills them in on their own machine.

## Step 2 — Scaffold the plugin

The fastest way to bootstrap the software half is the included
scaffolder, which produces a complete testable repo skeleton:

```bash
create-tool-plugin --key csl_fluo --name "Fluorescence Imager" --out ~/repos
```

It generates `pyproject.toml`, `tool.py`, `mock.py`, tests that pass
immediately, and zeroed `tpre0.g` / `tpost0.g` / `tfree0.g` firmware
templates. Unzip, `pip install -e .`, `pytest` — all green.

The rest of this page explains the conventions the scaffolder encodes,
in case you want to build the repo by hand or understand what was
generated.

## Step 3 — Naming: the `TOOL_KEY`

Every tool has a single canonical name called the `TOOL_KEY`:

| Rule | Reason |
|------|--------|
| Lowercase ASCII letters, digits, underscores | RepRapFirmware `M563 S"..."` limit |
| Starts with a letter | Python identifier derivation |
| At most 15 characters | RepRapFirmware `M563 S` string limit |
| Prefix with your org tag if outside the mother repo | Collision avoidance (e.g. `csl_pen`) |

Reserved bare names (core repo only): `inoculator`, `camera`, `light`,
`neopixel`, `toolhead_cam`.

The same `TOOL_KEY` appears in five places — the scaffolder handles all
of them consistently:

| Where | Format | Example |
|-------|--------|---------|
| `TOOL_KEY` class attribute | exact key | `"csl_fluo"` |
| Entry-point name in `pyproject.toml` | exact key | `csl_fluo` |
| Duet `M563 S"..."` | exact key | `M563 P2 S"csl_fluo"` |
| Python package (import) | key with `_` | `csl_fluo_tool` |
| Distribution (pip / PyPI) | key with `-` | `csl-fluo-tool` |

## Step 4 — Repo layout

```
csl-fluo-tool/                        # distribution name (dashes)
├── pyproject.toml
├── README.md
├── templates/
│   ├── tpre0.g                       # zeroed firmware macros
│   ├── tpost0.g                      # overwritten by user's calibration
│   └── tfree0.g
├── calibration/
│   ├── SetToolParkingPositions.ipynb
│   └── ToolAlignmentXY.ipynb
├── src/
│   └── csl_fluo_tool/                # package name (underscores + _tool)
│       ├── __init__.py
│       ├── tool.py                   # hardware Tool subclass
│       ├── mock.py                   # mock subclass
│       ├── configs/
│       │   └── csl_fluo.json
│       └── twin_assets/              # .stl / .blend / .step files
└── tests/
    └── test_tool.py
```

## Step 5 — Entry points

Four entry-point groups. The last two (`configs`, `twin_assets`) are
optional — declare only what you actually ship.

```toml
[project.entry-points."science_jubilee.tools"]
csl_fluo = "csl_fluo_tool.tool:FluoTool"

[project.entry-points."science_jubilee.tools.mocks"]
csl_fluo = "csl_fluo_tool.mock:FluoToolMock"

[project.entry-points."science_jubilee.tools.configs"]
csl_fluo = "csl_fluo_tool.configs:__path__"

[project.entry-points."science_jubilee.tools.twin_assets"]
csl_fluo = "csl_fluo_tool.twin_assets:__path__"
```

The entry-point name must exactly match `TOOL_KEY`. Mismatch → the
registry raises `ToolConfigurationError` at startup.

## Step 6 — The `Tool` subclass

```python
# src/csl_fluo_tool/tool.py
from dataclasses import dataclass
from typing import ClassVar

from science_jubilee.tools.Tool import Tool, requires_active_tool


@dataclass(slots=True, repr=False)
class FluoTool(Tool):
    TOOL_KEY: ClassVar[str] = "csl_fluo"
    exposure_ms: float = 100.0

    @requires_active_tool
    def capture(self, nav) -> None:
        """Trigger fluorescence capture at the current position."""
        ...
```

- Use `@dataclass(slots=True, repr=False)`
- `TOOL_KEY` is a `ClassVar[str]` matching the entry-point name
- Gate hardware calls with `@requires_active_tool` (fails fast if the
  wrong tool is active)
- The mock subclass inherits from your tool class and only overrides
  the I/O methods

## Step 7 — Duet firmware setup (per-machine, not per-plugin)

`tpre<N>.g`, `tpost<N>.g`, `tfree<N>.g` on the Duet SD card are
**machine-calibrated** — they contain the exact parking-post
coordinates on *that* specific machine. They are generated by the
calibration notebooks in Step 8; your plugin ships zeroed templates in
`templates/`.

The only Duet-side steps for a new tool are:

1. One `M563 P<N> S"<TOOL_KEY>"` in `config.g` — declares the tool number
2. One line in `toffsets.g` — the tool's XYZ offset (produced by `ToolAlignmentXY.ipynb`, see Step 8)

Both happen once, on each user's machine.

## Step 8 — Calibrate on the machine

Two notebooks live in the plugin's `calibration/` folder. Both must be
run on the target machine after the tool is physically installed and
`M563` is declared in `config.g`.

- **`SetToolParkingPositions.ipynb`** — jog to each parking post and
  record the (X, Y) of the ball-lock positions. Fills in `tpre<N>.g` /
  `tpost<N>.g` / `tfree<N>.g` from the zeroed templates and copies them
  to the Duet's SD card.

- **`ToolAlignmentXY.ipynb`** — with the tool active, use a reference
  point (e.g. a masking-tape cross under the toolhead camera) to find
  the tool's active point relative to the machine origin. Writes one
  line into `toffsets.g`.

The plugin doesn't ship the *results* of either notebook — they're
per-machine. Users re-run them if the tool is re-mounted or the
parking post moves.

## Step 9 — Digital-twin `.blend` asset

The Blender twin needs a `.blend` file placed in
`src/<pkg>/twin_assets/<TOOL_KEY>.blend`. Prepare it carefully — the
twin uses this file's local origin and hierarchy to position the tool
in the virtual scene.

1. **Model the full tool.** Include the wedge plate, both tool wings,
   and everything the toolchanger sees. The twin snaps the wedge plate
   to the carriage; if you omit it, the tool floats.

2. **Align against the reference wedge plate.** Open the reference
   `wedge_plate.blend` (shipped with `jubilee-blender-twin`, or grab
   the file linked in your reference implementation). Import your
   tool into that scene and manually align its wedge plate to the
   reference wedge plate — same position, same orientation. This is
   the alignment the twin will replicate on every session.

3. **Clean the parenting.** Before shipping, unparent everything (Alt +
   P → *Clear and Keep Transformation*). Meshes must have no parent
   set from the modelling phase; otherwise the twin's re-parenting to
   the machine Empty will inherit a transform you don't want.

4. **Parent the whole tool to a single Empty.** Add an Empty at the
   origin (which — because of step 2 — coincides with the wedge-plate
   reference). Select every mesh in the tool, then shift-select the
   Empty last, then Ctrl + P → *Object (Keep Transform)*. The Empty
   becomes the only object the twin needs to move; every mesh follows.

5. **Save as `<TOOL_KEY>.blend`.** The filename must match your
   `TOOL_KEY` for auto-discovery to work.

If any of these steps is skipped, the tool will appear misplaced in
the twin, drift when the machine moves, or fail to load at all.

## Reference implementations

- [`tool-pen-maag`](https://github.com/Jubilee-CSL/tool-pen-maag) — pen tool
- [`tool-fluo-csl`](https://github.com/Jubilee-CSL/tool-fluo-csl) — fluorescence imager

## See also

- [Choosing the right plugin type](../development/plugins.md) — decision tree across all plugin types
- [Plugin discovery (entry points)](../reference/entry_points.md) — full table
