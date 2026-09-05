---
title: Choosing the right plugin type
---

(plugins-guide)=
# Choosing the right plugin type

Almost everything you might add to `science-jubilee` — a new tool, a labware
pack, a deck definition, a visualiser — ships as an **independent Python
package** discovered via entry points, not as a fork of the core.

This page picks the right entry-point group for what you want to build, then
points at a reference implementation. For hardware tools specifically, there
is a scaffolder that generates the whole layout for you — see
{ref}`tool-plugin-guide`.

## Decision tree

| You want to add… | Entry-point group | Reference implementation |
|---|---|---|
| A **hardware tool** (pen, syringe, camera, LED, …) | `science_jubilee.tools` (+ `.mocks`, `.configs`, `.twin_assets`) | See [Design a new tool](../new_tool/index.md) — hardware + plugin guide |
| A **labware pack** (well-plates, tip racks, custom holders) | `science_jubilee.labware_dirs` and `jubilee.paths/labware_dir` | [`jubilee_labware`](https://github.com/Jubilee-CSL/labware) |
| A **deck definition** (fixed slot layout for a lab) | `science_jubilee.deck` | [`jubilee_interface`](https://github.com/Jubilee-CSL/science-jubilee-interface) exports one |
| A **digital-twin viewer** or **visualiser** | `science_jubilee.digital_twin` and `jubilee.paths/twin_dir` | [`jubilee-blender-twin`](https://github.com/Jubilee-CSL/jubilee-blender-twin) |
| A **path provider** (folder your code owns) | `jubilee.paths` | See `science_jubilee._paths` |
| A **vision / analysis pipeline** | *(none — plain pip package)* | [`vision-duckweed-tracking`](https://github.com/Jubilee-CSL/vision-duckweed-tracking) |

If none of the above applies, you probably want a plain pip package — no
entry point, no naming rules.

## The common pattern

Every plugin type follows the same three steps:

1. **A Python package** with a normal `pyproject.toml` or `setup.cfg`.
2. **One or more entry points** in that config file, mapping a name to a
   callable or a module path. `science_jubilee` never imports plugins by
   name; discovery is entirely through `importlib.metadata.entry_points`.
3. **Install with `pip install -e .`** into the same environment as
   `science_jubilee`. The entry point becomes visible immediately.

Example, from a labware plugin's `setup.cfg`:

```ini
[options.entry_points]
jubilee.paths =
    labware_dir = jubilee_labware:LABWARE_DEFINITION_DIR

science_jubilee.labware_dirs =
    jubilee_labware = jubilee_labware:LABWARE_DEFINITION_DIR
```

`LABWARE_DEFINITION_DIR` here is a `Path` object at the package's root. When
`science_jubilee` looks for labware definitions it calls this entry point,
gets a directory, and scans it. Nothing needs to know the plugin exists at
import time.

## Which entry points does core actually consume?

Every group that starts with `science_jubilee.` is consumed by the core
package. `jubilee.paths` is a shared namespace: any Jubilee package can
publish and any other can consume. In practice:

- `science_jubilee` consumes `jubilee.paths` (`jubilee_dir`, `pipeline_data_dir`,
  `gcode_logs_dir`, `camera_params_yaml`, `machine_state_json`).
- `jubilee-blender-twin` consumes `jubilee.paths` (`jubilee_dir`, `gcode_logs_dir`,
  `interface_dir`, `experiment_deck_dir`, `camera_params_yaml`) and the
  `science_jubilee.tools.twin_assets` group.
- `science-jubilee-interface` consumes `jubilee.paths` (`labware_dir`,
  `gcode_logs_dir`, `jubilee_dir`) and publishes `interface_dir`,
  `experiment_deck_dir`.

## Naming rules

For groups keyed by tool (`science_jubilee.tools`, `.mocks`, `.configs`,
`.twin_assets`), the entry-point **name** is the plugin's `TOOL_KEY`.
See {ref}`tool-plugin-guide` for the tool-key rules.

For all other groups the name is free-form; keep it short and unique to
your package. `jubilee_labware`, `jubilee_interface`, `twin_dir` are typical.

## Version discipline

Every plugin declares `science-jubilee>=X.Y` in its dependencies. Bump the
lower bound whenever your plugin uses a new core feature. Do **not** upper-bound
without a real reason; users installing multiple plugins will get pinned into a
corner otherwise.

## What lives where

The fallback chain across the whole ecosystem is always the same three steps:
**explicit path / env var → installed plugin → built-in default**. Every
consumer follows it, and every producer only needs to provide the middle
step.
