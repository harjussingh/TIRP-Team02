from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    """Return the root of the saca-windows-app project."""
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> Path:
    return project_root() / "assets" / Path(*parts)


def data_path(*parts: str) -> Path:
    return project_root() / "data" / Path(*parts)
