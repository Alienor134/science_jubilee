---
title: Labware plugin — requirements
---

(labware-plugin-guide)=
# Labware plugin — requirements

A **labware plugin** ships a folder of Opentrons-format JSON labware
definitions that `MachineSession` picks up automatically.

## File tree

```
jubilee_labware/
├── pyproject.toml
└── src/
    └── jubilee_labware/
        ├── __init__.py                     # exports LABWARE_DEFINITION_DIR
        └── labware_definitions/
            ├── corning_96_wellplate_360ul_flat.json
            └── ...
```

## Required entry points

```toml
[project.entry-points."jubilee.paths"]
labware_dir = "jubilee_labware:LABWARE_DEFINITION_DIR"

[project.entry-points."science_jubilee.labware_dirs"]
jubilee_labware = "jubilee_labware:LABWARE_DEFINITION_DIR"
```

`LABWARE_DEFINITION_DIR` is a `pathlib.Path` set in `__init__.py`.

## Naming convention

`<brand>_<well_count>_<type>_<volume>_<extras>.json`

## Reference

[`jubilee_labware`](https://github.com/Jubilee-CSL/labware).
