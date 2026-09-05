---
title: Digital-twin plugin — requirements
---

(digital-twin-plugin-guide)=
# Digital-twin plugin — requirements

A **digital-twin plugin** visualises, analyses, or replays a
`science-jubilee` session by reading from `pipeline_data/`.

## Three levels

- **Level 1 — plain package.** No entry point required. Just import
  `science_jubilee._paths.pipeline_data_dir()` and read the folder.
- **Level 2 — publish tool 3D models.** Register a
  `science_jubilee.tools.twin_assets` entry point pointing at a folder
  of `.blend` files. See [Design a new tool](../new_tool/index.md).
- **Level 3 — publish a viewer callable.** Register a
  `science_jubilee.digital_twin` entry point so other tools can
  discover installed twins.

## File tree (level 3)

```
my_twin/
├── pyproject.toml
└── src/
    └── my_twin/
        ├── __init__.py
        └── cli.py             # exposes launch_viewer()
```

## Required entry point (level 3)

```toml
[project.entry-points."science_jubilee.digital_twin"]
my_twin = "my_twin.cli:launch_viewer"
```

## Reference

[`jubilee-blender-twin`](https://github.com/Jubilee-CSL/jubilee-blender-twin)
— publishes `jubilee.paths/twin_dir`; consumes
`science_jubilee.tools.twin_assets` for per-tool `.blend` files.
