from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database_backup import create_sqlite_snapshot


def test_sqlite_wal_consistent_snapshot(tmp_path: Path):
    source = tmp_path / 'live.db'
    backup = tmp_path / 'Backups' / 'snapshot.db'
    with sqlite3.connect(source) as connection:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('CREATE TABLE data (x TEXT)')
        connection.execute('INSERT INTO data VALUES (?)', ('persisted',))
    # Deve funcionar mesmo com WAL e conexão aberta
    connection = sqlite3.connect(source)
    try:
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('INSERT INTO data VALUES (?)', ('committed',))
        connection.commit()
        create_sqlite_snapshot(source, backup)
        with sqlite3.connect(backup) as snapshot:
            assert snapshot.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            assert snapshot.execute('SELECT x FROM data ORDER BY rowid').fetchall() == [('persisted',), ('committed',)]
    finally:
        connection.close()


def test_backup_not_created_for_missing_database(tmp_path: Path):
    destination = tmp_path / 'Backups' / 'snapshot.db'
    with pytest.raises(FileNotFoundError):
        create_sqlite_snapshot(tmp_path / 'unknown.db', destination)
    assert not destination.exists()
