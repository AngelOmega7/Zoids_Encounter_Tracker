"""SQLite storage for named snapshots of the Enemy page."""

import json
import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path


def database_path():
    # Flet supplies a persistent writable location on packaged mobile apps.
    if os.environ.get("FLET_APP_STORAGE_DATA"):
        root = Path(os.environ["FLET_APP_STORAGE_DATA"])
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "ZoidsEncounterTracker"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / "ZoidsEncounterTracker"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "zoids-encounter-tracker"
    return root / "enemy_sets.sqlite3"


class EnemySetStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS enemy_sets (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    snapshot TEXT NOT NULL
                )
            """)

    def list_sets(self):
        with closing(sqlite3.connect(self.path)) as connection:
            return connection.execute("SELECT id, name FROM enemy_sets ORDER BY name COLLATE NOCASE").fetchall()

    def save(self, name, cards, set_id=None):
        name = name.strip()
        if not name:
            raise ValueError("Enter a name for the enemy set.")
        snapshot = json.dumps({"version": 1, "cards": cards})
        with closing(sqlite3.connect(self.path)) as connection, connection:
            if set_id is None:
                cursor = connection.execute("INSERT INTO enemy_sets (name, snapshot) VALUES (?, ?)", (name, snapshot))
                return cursor.lastrowid
            cursor = connection.execute("UPDATE enemy_sets SET name = ?, snapshot = ? WHERE id = ?", (name, snapshot, set_id))
            if not cursor.rowcount:
                raise ValueError("That enemy set no longer exists.")
            return set_id

    def load(self, set_id):
        with closing(sqlite3.connect(self.path)) as connection:
            row = connection.execute("SELECT name, snapshot FROM enemy_sets WHERE id = ?", (set_id,)).fetchone()
        if row is None:
            raise ValueError("That enemy set no longer exists.")
        payload = json.loads(row[1])
        if payload.get("version") != 1 or not isinstance(payload.get("cards"), list):
            raise ValueError("Unsupported enemy set format.")
        return row[0], payload["cards"]

    def delete(self, set_id):
        with closing(sqlite3.connect(self.path)) as connection, connection:
            connection.execute("DELETE FROM enemy_sets WHERE id = ?", (set_id,))
