"""Saved sessions: the system, display and sweep settings of the application as JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from .. import __version__
from .plots import DisplayOptions
from .state import Settings, SweepSettings

FORMAT = "pourbase-session"
FORMAT_VERSION = 1
SUFFIX = ".pourbase.json"


class SessionError(ValueError):
    """The file is not a readable pourbase session."""


def session_dict(settings: Settings, display: DisplayOptions, sweep: SweepSettings,
                 user_species: str | None = None, selection_policy: str | None = None) -> dict[str, Any]:
    return {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "pourbase_version": __version__,
        "settings": settings.to_dict(),
        "display": asdict(display),
        "sweep": asdict(sweep),
        "user_species": user_species,
        "selection_policy": selection_policy,
    }


def write_session(path: str | Path, settings: Settings, display: DisplayOptions, sweep: SweepSettings,
                  user_species: str | None = None, selection_policy: str | None = None) -> Path:
    """Write a session with the paths of a user-species CSV file and a selection-policy file, if any."""
    path = Path(path)
    data = session_dict(settings, display, sweep, user_species, selection_policy)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _known(cls: type, values: Any) -> dict[str, Any]:
    if not isinstance(values, dict):
        return {}
    defaults = cls()
    known = {}
    for item in fields(cls):
        if item.name in values:
            value, default = values[item.name], getattr(defaults, item.name)
            if isinstance(default, bool) != isinstance(value, bool):
                continue
            if isinstance(default, (int, float)) and isinstance(value, (int, float)):
                known[item.name] = type(default)(value)
            elif isinstance(value, type(default)):
                known[item.name] = value
    return known


def read_session(path: str | Path) -> tuple[Settings, DisplayOptions, SweepSettings]:
    """Read a session; unknown keys are ignored and invalid values take their defaults."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SessionError(f"Cannot read {path}: {error}") from error
    if not isinstance(data, dict) or data.get("format") != FORMAT:
        raise SessionError(f"{path} is not a pourbase session file")
    if int(data.get("format_version", 0)) > FORMAT_VERSION:
        raise SessionError(f"{path} was written by a newer pourbase ({data.get('pourbase_version')})")
    settings = Settings.from_dict(data.get("settings") or {})
    display = DisplayOptions(**_known(DisplayOptions, data.get("display")))
    try:
        sweep = SweepSettings(**_known(SweepSettings, data.get("sweep")))
    except (TypeError, ValueError):
        sweep = SweepSettings()
    return settings, display, sweep


def sidecar_path(figure_path: str | Path) -> Path:
    """The session file written next to an exported figure."""
    path = Path(figure_path)
    return path.with_name(path.stem + SUFFIX)


def _session_value(path: str | Path, key: str) -> str | None:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8")).get(key)
    except (OSError, ValueError, AttributeError):
        return None
    return str(value) if value else None


def session_user_species(path: str | Path) -> str | None:
    """The user-species CSV recorded in a session, if any."""
    return _session_value(path, "user_species")


def session_selection_policy(path: str | Path) -> str | None:
    """The selection-policy file recorded in a session, if any."""
    return _session_value(path, "selection_policy")
