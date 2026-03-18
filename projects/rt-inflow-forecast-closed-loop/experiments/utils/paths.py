from __future__ import annotations

from pathlib import Path


def resolve_project_path(*, base_dir: Path, relative_path: str) -> str:
    return str((base_dir / relative_path).resolve())


