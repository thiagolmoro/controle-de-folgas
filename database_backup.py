"""Backups SQLite consistentes, inclusive para bases em modo WAL."""
from __future__ import annotations

import os
from contextlib import closing
import sqlite3
from pathlib import Path


def create_sqlite_snapshot(source: Path, destination: Path) -> Path:
    source = Path(source)
    destination = Path(destination)
    if not source.is_file():
        raise FileNotFoundError(f"Banco de dados não encontrado: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp = destination.with_name(destination.name + ".tmp")
    try:
        with closing(sqlite3.connect(source, timeout=15)) as origin:
            with closing(sqlite3.connect(tmp)) as snapshot:
                origin.backup(snapshot)
        with closing(sqlite3.connect(tmp)) as check:
            result = check.execute("PRAGMA quick_check").fetchone()
            if result is None or result[0] != "ok":
                raise sqlite3.DatabaseError(f"Falha na verificação do backup: {result}")
        os.replace(tmp, destination)
        return destination
    finally:
        if tmp.exists():
            tmp.unlink()
