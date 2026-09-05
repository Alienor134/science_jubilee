from pathlib import Path


def jubilee_dir() -> Path:
    """Return the science_jubilee repo root.

    Works for editable installs (returns the checked-out repo root).
    For wheel installs, returns the directory containing the installed package.
    """
    # src/science_jubilee/_paths.py → parents: [0] science_jubilee/, [1] src/, [2] repo root
    return Path(__file__).parents[2]


def camera_params_yaml() -> Path:
    """Return the path to the camera calibration YAML shipped with the package."""
    return Path(__file__).parent / "calibration" / "camera_params.yaml"


def pipeline_data_dir() -> Path:
    """Session-scoped state: g-code recordings, machine snapshot, trace recaps.

    Override with the ``JUBILEE_PIPELINE_DATA`` environment variable (useful for
    tests and for wheel installs where the repo root is not writable).

    On first access, creates the directory and seeds ``machine_state.json`` from
    the bundled default so a fresh install has real tool state to work with.
    """
    import os
    import shutil

    override = os.environ.get("JUBILEE_PIPELINE_DATA")
    d = Path(override) if override else jubilee_dir() / "pipeline_data"

    d.mkdir(parents=True, exist_ok=True)
    snapshot = d / "machine_state.json"
    if not snapshot.exists():
        bundled = Path(__file__).parent / "defaults" / "machine_state.json"
        if bundled.exists():
            shutil.copy(bundled, snapshot)

    return d


def machine_state_json() -> Path:
    """Snapshot of the machine written on each recorded session."""
    return pipeline_data_dir() / "machine_state.json"


def gcode_logs_dir() -> Path:
    """Where RecordingTransport writes the g-code stream."""
    return pipeline_data_dir() / "gcode_logs"


def traces_dir() -> Path:
    """Where MachineSession writes trace recaps."""
    return pipeline_data_dir() / "traces"


def latest_experiment_dir() -> Path | None:
    """Newest experiment folder exported by science-jubilee-interface.

    Returns None when the interface is not installed or has exported nothing.
    """
    from importlib.metadata import entry_points

    roots: list[Path] = []
    for ep in entry_points(group="jubilee.paths"):
        if ep.name not in ("experiment_deck_dir", "interface_dir"):
            continue
        try:
            base = Path(ep.load()())
        except Exception:
            continue
        roots.append(
            base if ep.name == "experiment_deck_dir" else base / "experiment_deck"
        )

    for root in roots:
        if not root.is_dir():
            continue
        subdirs = sorted((d for d in root.iterdir() if d.is_dir()), reverse=True)
        if subdirs:
            return subdirs[0]
    return None
