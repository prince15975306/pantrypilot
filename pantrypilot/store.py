"""Tiny JSON-file store. State survives restarts, so Alexa+ remembers across sessions."""
import json
import os
from pathlib import Path


def _file() -> Path:
    return Path(os.environ.get("PANTRY_DB") or Path.cwd() / "data" / "state.json")


def _empty() -> dict:
    return {"pantry": [], "preferences": {}, "history": []}


def load() -> dict:
    try:
        return {**_empty(), **json.loads(_file().read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return _empty()


def save(state: dict) -> None:
    f = _file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2), encoding="utf-8")
