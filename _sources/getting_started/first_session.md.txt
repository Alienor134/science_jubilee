---
title: Your first session
---

(first-session)=
# Your first session

This page walks through opening a `MachineSession`, picking up a tool, and
moving. It assumes `science-jubilee` is installed
([installation guide](installation.md)) and an `.env.mock` (or
`.env.hardware`) file lives in the package root — see the
[env files reference](env_files.md).

## Mock session

If you don't have a Jubilee wired up yet (or you're just prototyping),
`MachineSession.mock()` gives you a fully-functional software machine.
G-code is captured to a log file instead of being sent to Duet; all
state is tracked locally.

Every run — mock or hardware — writes three kinds of artefact into
`pipeline_data/`:

```text
your_script.py
     │
     ▼
MachineSession.from_env()
     │
     ├── every G/M code ──────►  pipeline_data/gcode_logs/*.gcode
     │
     ├── snapshot on connect ──►  pipeline_data/machine.json
     │
     └── fallback-walk recap ──►  pipeline_data/traces/*.html
         (via atexit)
```

- **`gcode_logs/<timestamp>-<script>.gcode`** — every G/M code that was
  sent (or would have been, in mock mode). Replayable.
- **`machine.json`** — snapshot of tool table, offsets, and last known
  positions. Used as the fallback for mock mode when hardware is offline.
- **`traces/<script>.html`** — human-readable recap of the fallback walk
  (see [Trace reference](../reference/trace.md)). Opens in any browser.

Override the base folder with the `JUBILEE_PIPELINE_DATA` env var — see
[env files](env_files.md).

```python
from science_jubilee.machine_session import MachineSession

session = MachineSession.from_env(env_file=".env.mock")
```

`from_env()` reads `JUBILEE_TRANSPORT` from the environment. When it's
`mock` (the default), a `MockTransport` is wired in. When it's
`hardware`, an `HTTPTransport` is opened to `JUBILEE_ADDRESS`.

## Homing and moving

Motion goes through a navigator, never through raw `session.motion`
(which is the low-level driver — dicts only, no safety checks). For
free-form jogging use `session.free_navigator`:

```python
nav = session.free_navigator

nav.home_all()                    # G28
nav.move_to(x=100, y=50, z=10)    # absolute
nav.jog(x=20)                     # relative
```

`move_to` uses absolute coordinates, `jog` uses relative deltas. This
split is deliberate — you can't accidentally swap one for the other.

## Picking up a tool

Tool ops are on the navigator too:

```python
nav.pickup_tool(0)   # T0
# ...do stuff...
nav.park_tool()      # T-1
```

The tool numbers, names, and park positions come from
`pipeline_data/machine.json`, which is populated automatically the first
time you open a real hardware session, or from installed tool plugins
when running in mock mode.

## Navigating to a labware well

For labware-aware experiments — where the machine knows the deck and can
enforce safe Z travel — use `session.navigator` (a `DeckNavigator`,
auto-created when a deck definition is present):

```python
deck_nav = session.navigator
plate = deck_nav.deck.slot(1)   # 96-well plate loaded from labware plugin

nav.pickup_tool(0)              # still via the free navigator for tool ops
deck_nav.move_to_well(plate["A1"])
```

See [Writing an experiment script](../users/writing_experiments.md) for
when to pick `FreeNavigator` vs `DeckNavigator`.

## Cleanup

`MachineSession` is a context manager; `__exit__` is a no-op today, but
using `with` still helps IDEs and tests treat the session as scoped:

```python
with MachineSession.from_env(".env.mock") as session:
    nav = session.free_navigator
    nav.home_all()
    nav.move_to(x=100, y=100, z=20)
```

The trace HTML recap is flushed automatically via `atexit`; look in
`pipeline_data/traces/<script_name>.html` after the process exits.

## Where to look next

- [`.env` files and variables](env_files.md) — full list of what
  `from_env()` reads.
- [Writing experiments](../users/writing_experiments.md) — patterns for
  real-world experiment code.
- [`troubleshooting`](../users/troubleshooting.md) — common errors and
  what they mean.
