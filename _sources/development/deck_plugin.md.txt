---
title: Deck plugin — requirements
---

(deck-plugin-guide)=
# Deck plugin — requirements

A **deck plugin** ships JSON definitions of physical deck layouts —
fixed slot geometry for a specific bed plate.

## File tree

```
decks/
├── pyproject.toml
└── src/
    └── decks/
        ├── __init__.py                # exports DECK_DEFINITION_DIR
        └── deck_definitions/
            └── lab_automation_deck.json
```

## Required entry point

```toml
[project.entry-points."science_jubilee.deck"]
decks = "decks:DECK_DEFINITION_DIR"
```

## Deck JSON schema (summary)

```json
{
  "name": "lab_automation_deck",
  "safe_z": 100.0,
  "slots": [{"index": 0, "offset": [x, y, z]}, ...],
  "off_deck": [{"name": "sharps_container", "offset": [x, y, z]}]
}
```

Slot offsets are calibrated per-machine using a camera tool.

## Reference

[`decks`](https://github.com/Jubilee-CSL/decks).
