---
title: Common errors and how to fix them
---

(troubleshooting)=
# Common errors and how to fix them

## `ValueError: JUBILEE_ADDRESS must be set ... when JUBILEE_TRANSPORT=hardware`

You asked for a hardware session but didn't provide the machine IP.

- Either set `JUBILEE_ADDRESS=10.0.x.x` in your `.env.hardware`, or
- Switch to `JUBILEE_TRANSPORT=mock` if you don't actually have hardware.

## The session hangs for ~15 s on startup

The `HTTPTransport` is retrying against an unreachable Duet. Check:

1. `ping 10.0.x.x` — is the machine on the network?
2. Is the address right? (see `pipeline_data/machine.json` for the last-known address)
3. Is Duet on port 80? (default; RepRapFirmware doesn't expose this)

A TCP pre-check aborts early when the port is closed, but a firewall
that silently drops packets can still stall.

## Mock mode uses a stale tool table

Mock mode falls back to `pipeline_data/machine.json` from the last real
hardware session. To refresh:

```bash
JUBILEE_TRANSPORT=hardware JUBILEE_ADDRESS=10.0.x.x python -c \
    "from science_jubilee.machine_session import MachineSession; MachineSession.from_env('.env.hardware')"
```

That reconnects, dumps a fresh `machine.json`, and disconnects.

## Import fails with `ModuleNotFoundError: No module named 'neopixel'` (or similar)

Some legacy modules (`tools/piserver/*`, `tools/unique_tools/old/*`)
have Raspberry Pi–specific imports at module scope. If Sphinx or your
IDE tries to import them on a non-Pi host they fail. They're not part
of the public API — ignore or delete.

## The trace HTML doesn't appear

- Check the process exited cleanly. `trace.flush()` runs via `atexit`
  — a `SIGKILL` or unhandled system exit will skip it. Wrap your
  entry point in `try/finally` and call `trace.flush()` explicitly.
- Check `JUBILEE_PIPELINE_DATA` — that's where `traces/` lives.
- The filename is `<script_name>.html`, where `script_name = Path(sys.argv[0]).stem`. When you run via `python -m mymodule`, `script_name` is `mymodule`.

## The digital twin can't find my tool

Ensure your tool plugin registered a `science_jubilee.tools.twin_assets`
entry point pointing at a folder with a `.blend` file. See
[Digital Twin Plugin guide](../development/digital_twin_plugin.md).

## The build fails with `Relative import with too many levels (1) for module 'http'`

Sphinx-AutoAPI conflict with `hal/transport/http.py` (filename clashes
with stdlib `http`). Rename to e.g. `http_transport.py` and update
imports, or add `autoapi_ignore = ["*/hal/transport/http.py"]` to
`docs/conf.py`. Tracked as an open issue.
