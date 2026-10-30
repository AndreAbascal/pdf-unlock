"""Deterministic PDF discovery without following symbolic links."""

import os
from pathlib import Path


def discover(path: Path, recursive: bool = False) -> tuple[list[Path], list[str]]:
    """Return PDF paths and traversal errors. Symlinks are excluded for safe replacement."""
    if path.is_symlink():
        raise ValueError("Symbolic links are not supported")
    if not path.exists():
        raise ValueError("Path does not exist")
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise ValueError("File must have a .pdf extension")
        return [path], []
    if not path.is_dir():
        raise ValueError("Path is not a regular file or directory")
    errors: list[str] = []
    files: list[Path] = []

    def onerror(error: OSError) -> None:
        errors.append(str(error))

    for root, dirs, names in os.walk(path, topdown=True, onerror=onerror, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(root) / d).is_symlink()) if recursive else []
        for name in sorted(names):
            candidate = Path(root) / name
            if candidate.suffix.lower() == ".pdf" and not candidate.is_symlink():
                files.append(candidate)
    return sorted(files, key=lambda p: str(p)), errors
