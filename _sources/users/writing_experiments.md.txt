---
title: Writing an experiment script
---

(writing-experiments)=
# Writing an experiment script

`science-jubilee` gives you two ways to move the machine around, aimed
at different levels of geometry knowledge:

| Class | Knows about deck? | Use when |
|---|---|---|
| `FreeNavigator` | No | Jogging, calibration, arbitrary G-code, one-off scripts |
| `DeckNavigator` | Yes (loaded from deck.json) | Real experiments with labware, safe Z travel, well-based navigation |

Both wrap the same underlying `MotionDriver` and `ToolChanger`. Always
call motion on a navigator — never on `session.motion` directly.

## `FreeNavigator` — jogging and setup

```python
from science_jubilee.machine_session import MachineSession

with MachineSession.from_env(".env.hardware") as session:
    nav = session.free_navigator
    nav.home_all()
    nav.move_to(x=150, y=150, z=20)
    nav.pickup_tool(0)
    nav.jog(z=-5)                 # relative move down
    nav.park_tool()
```

This is the right level for:
- Manual jog + capture during calibration
- Debugging tool offsets
- Running a script that doesn't know the deck yet

## `DeckNavigator` — labware-aware experiments

```python
from science_jubilee.machine_session import MachineSession

with MachineSession.from_env(".env.hardware") as session:
    deck_nav = session.navigator           # DeckNavigator, auto-created from JUBILEE_DECK_DEF
    nav = session.free_navigator           # for tool ops (they live on FreeNavigator)
    plate = deck_nav.deck.slot(1)          # 96-well plate loaded from labware plugin

    nav.pickup_tool(0)                     # e.g. pipette

    for well in ("A1", "A2", "A3"):
        deck_nav.move_to_well(plate[well])
        # aspirate / dispense / image
```

`DeckNavigator` enforces safe Z travel (`travel_margin` above
`deck.safe_z`) between moves, so you don't drag a tool through
neighbouring labware.

## Recording labelled steps in the run report

Every session automatically writes an HTML report to
`pipeline_data/traces/<script_name>.html`. By default the report only
contains messages the framework emits (machine state, tool loading,
etc.). If you want your own steps in the report — one line per action,
with success/failure marks — wrap them in a `trace` section:

```python
from science_jubilee import trace

with trace.session().section("Serial dilution", reset=True) as sec:
    sec.step("Pickup pipette", ok=True)
    sec.step("Aspirate 50 μL", ok=True)
```

Each `section("...")` becomes a collapsible block in the HTML; each
`sec.step(...)` becomes a row inside it. Full details of what the
report looks like: [Session trace (HTML recap)](../reference/trace.md).

## Where deck definitions come from

The deck JSON your `DeckNavigator` uses is discovered via the
`science_jubilee.deck` entry point (typically shipped by the
[`decks`](https://github.com/Jubilee-CSL/decks) plugin) or overridden
by `JUBILEE_DECK_DEF` in your `.env`. See
[env files](../getting_started/env_files.md).
