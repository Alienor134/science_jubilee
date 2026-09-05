---
title: Session trace (HTML recap)
---

(trace)=
# Session trace (HTML recap)

The `science_jubilee.trace` module produces a per-run HTML file that
captures every fallback step, log record, and tool-loading decision.
This page describes what's in that file and how to add to it.

## Where it lives

```
pipeline_data/traces/<script_name>.html
```

Where `<script_name>` is `Path(sys.argv[0]).stem`, or the value of
`JUBILEE_RUN_NAME` if set.

## What's in a trace

Each trace is a series of **sections**, one per subsystem. Every section
has an ordered list of **steps**. A step records:

- A label
- Whether it succeeded
- Optional detail lines (paths, values, error messages)

The rendered HTML is standalone (all styles inlined) — you can email
or attach it to a bug report.

## Standard sections written by `science-jubilee`

| Section | Written by | Records |
|---|---|---|
| `Machine state` | `machine_state.resolve()` | live query attempt, snapshot fallback, empty fallback |
| `Tool models` | `jubilee_twin.pipeline.tool_id` | park origin per slot (live/snapshot/plugin/defaults) |
| `Deck` | `DeckNavigator.__init__` | deck.json load path, slot count |
| `Labware` | `Labware.load_from` | labware JSON scan, definitions found |
| `Session lifecycle` | `machine_session` | transport type, address, atexit flush |

## Adding to a trace from user code

```python
from science_jubilee import trace

with trace.session().section("Serial dilution", reset=True) as sec:
    sec.step("Pickup pipette", ok=True)
    sec.step("Aspirate 50 μL from A1", ok=True, detail=["z=8mm", "flow=20uL/s"])
    try:
        do_something_risky()
        sec.step("Dispense to B1", ok=True)
    except Exception as e:
        sec.step("Dispense to B1", ok=False, detail=[str(e)])
        raise
```

- `reset=True` starts a fresh section; without it, `section("...")`
  appends steps to an existing one with the same name.
- Sections and steps flush automatically at process exit via
  `atexit.register(trace.flush)`. Call `trace.flush()` explicitly if
  your process might be killed.

## Log capture

```python
trace.capture_logger("science_jubilee")
```

Attaches a buffered handler to a named logger. Anything logged at
`INFO` or above ends up embedded in the trace HTML under a "Log" section
at the end.

## Threading

`trace._session` and `trace._session_dir` are module globals — single
threaded. If you need a session per thread, wrap your entry point in
`with trace.session(pipeline_data_dir(), title=my_thread_name): ...`
and don't share the state.
