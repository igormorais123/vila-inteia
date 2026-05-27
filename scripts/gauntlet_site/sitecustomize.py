"""Compatibility hooks used only by scripts/system_gauntlet.py subprocesses."""
from __future__ import annotations

import builtins
import io
import os
from pathlib import Path


REPO_ROOT = Path(os.environ.get("VILA_REPO_ROOT", "")).resolve()
LEGACY_ROOTS = (
    "/home/pedroafonso/vila-inteia",
    "/home/pedro/vila-inteia",
    "\\home\\pedroafonso\\vila-inteia",
    "\\home\\pedro\\vila-inteia",
)


def _remap_path(path):
    if not REPO_ROOT:
        return path
    text = os.fspath(path) if isinstance(path, (str, bytes, os.PathLike)) else None
    if text is None or isinstance(text, bytes):
        return path
    normalized = text.replace("\\", "/")
    for legacy in LEGACY_ROOTS:
        legacy_norm = legacy.replace("\\", "/")
        if normalized == legacy_norm:
            return str(REPO_ROOT)
        if normalized.startswith(legacy_norm + "/"):
            rel = normalized[len(legacy_norm) + 1 :]
            return str(REPO_ROOT / Path(*rel.split("/")))
    return path


_original_open = builtins.open
_original_io_open = io.open
_original_exists = os.path.exists
_original_isfile = os.path.isfile
_original_isdir = os.path.isdir
_original_path_open = Path.open
_original_path_exists = Path.exists
_original_path_is_file = Path.is_file
_original_path_is_dir = Path.is_dir


def open(file, *args, **kwargs):  # noqa: A001 - mirrors builtins.open
    return _original_open(_remap_path(file), *args, **kwargs)


def io_open(file, *args, **kwargs):
    return _original_io_open(_remap_path(file), *args, **kwargs)


def exists(path):
    return _original_exists(_remap_path(path))


def isfile(path):
    return _original_isfile(_remap_path(path))


def isdir(path):
    return _original_isdir(_remap_path(path))


def path_open(self, *args, **kwargs):
    return _original_path_open(Path(_remap_path(self)), *args, **kwargs)


def path_exists(self):
    return _original_path_exists(Path(_remap_path(self)))


def path_is_file(self):
    return _original_path_is_file(Path(_remap_path(self)))


def path_is_dir(self):
    return _original_path_is_dir(Path(_remap_path(self)))


builtins.open = open
io.open = io_open
os.path.exists = exists
os.path.isfile = isfile
os.path.isdir = isdir
Path.open = path_open
Path.exists = path_exists
Path.is_file = path_is_file
Path.is_dir = path_is_dir
