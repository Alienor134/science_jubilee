---
title: Plugin discovery (entry points)
---

(entry-points)=
# Plugin discovery (entry points)

Every plugin type in the Jubilee ecosystem is discovered by
`importlib.metadata.entry_points`. This page is the definitive table.

## Table

| Group | Purpose | Value type | Consumed by |
|---|---|---|---|
| `jubilee.paths` | Shared filesystem locations (labware dir, camera calibration file, log folder, etc.) | Module attribute → `Path` or `str` | Any Jubilee package |
| `science_jubilee.tools` | Tool classes registered by tool_key | Class | `MachineSession` |
| `science_jubilee.tools.mocks` | Mock counterpart for a real tool | Class | `MockTransport` |
| `science_jubilee.tools.configs` | Config JSON per tool_key | Module attribute → `Path` to folder | `MachineSession` |
| `science_jubilee.tools.twin_assets` | Blender `.blend` for a tool | Module attribute → `Path` to folder | `jubilee-blender-twin` |
| `science_jubilee.deck` | Deck definition JSON | Module attribute → `Path` to folder | `MachineSession`, `DeckNavigator` |
| `science_jubilee.labware_dirs` | Labware definition JSON folders | Module attribute → `Path` to folder | `MachineSession`, `DeckNavigator` |
| `science_jubilee.digital_twin` | Twin viewers/analysers | Callable | External tools |

## Names within each group

- For groups keyed on a tool (`science_jubilee.tools`, `.mocks`, `.configs`, `.twin_assets`), the **entry-point name is the tool_key**. See [Design a new tool](../new_tool/index.md).
- For `jubilee.paths`, the name is free-form but conventionally short: `labware_dir`, `interface_dir`, `experiment_deck_dir`, `twin_dir`, `gcode_logs_dir`, `jubilee_dir`, `camera_params_yaml`.
- For other groups, the name is the plugin package name.

## Ecosystem publishers today

| Package | Publishes | Consumes |
|---|---|---|
| `science-jubilee` (this repo) | `jubilee.paths` (`jubilee_dir`, `pipeline_data_dir`, `gcode_logs_dir`, `camera_params_yaml`, `machine_state_json`) | `science_jubilee.*` (all groups) |
| `jubilee-blender-twin` | `jubilee.paths/twin_dir` | `jubilee.paths`, `science_jubilee.tools.twin_assets` |
| `science-jubilee-interface` | `jubilee.paths/interface_dir`, `experiment_deck_dir` | `jubilee.paths` |
| `jubilee_labware` | `jubilee.paths/labware_dir`, `science_jubilee.labware_dirs/jubilee_labware` | – |
| `decks` | `science_jubilee.deck` | – |
| `tool-pen-maag` | `science_jubilee.tools.maag_pen`, `.configs.maag_pen`, `.twin_assets.maag_pen` | – |
| `tool-fluo-csl` | same shape as `tool-pen-maag` | – |

## Adding your own

Every plugin ships:

1. A `setup.cfg` (or `pyproject.toml`) with `[options.entry_points]`
2. `pip install -e .` into the environment where `science-jubilee` lives

The [plugin guide](../development/plugins.md) picks the right group for
what you're building; the [Design a new tool](../new_tool/index.md) guide
covers the tool-plugin case in step-by-step detail.
