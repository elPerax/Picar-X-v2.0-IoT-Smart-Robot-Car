"""
Local SQLite database helper for PiCar-X IoT project.

DB file:
  /home/pi/picar-x/logs/picarx_data.db
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# /home/pi/picar-x/logs/picarx_data.db
DB_PATH = Path(__file__).resolve().parents[1] / "logs" / "picarx_data.db"


def get_conn():
    """Return a connection to the local SQLite DB."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)  # make sure /logs exists
    return sqlite3.connect(str(DB_PATH))


def init_db():
    """Create tables if they don't exist yet, with a 'synced' column."""
    with get_conn() as conn:
        c = conn.cursor()

        # Main table with all sensor data
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                sensor_name TEXT NOT NULL,
                value TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        # Track what we've already synced to the cloud (legacy support)
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_synced_id INTEGER NOT NULL
            )
            """
        )

        # Ensure exactly one row exists
        c.execute(
            """
            INSERT OR IGNORE INTO sync_state (id, last_synced_id)
            VALUES (1, 0)
            """
        )

        conn.commit()


def insert_sensor_batch(sensor_dict: dict):
    """
    Insert one 'batch' of readings.

    Example sensor_dict:
    {
        "timestamp": time.time(),
        "ultrasonic-distance": 34.5,
        "grayscale-left": 120,
        "grayscale-mid": 90,
        "grayscale-right": 20,
        "tts": "hello world"
    }
    """
    ts = sensor_dict.get("timestamp")
    if ts is None:
        raise ValueError("sensor_dict must contain a 'timestamp' field")

    ts_iso = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()

    with get_conn() as conn:
        c = conn.cursor()
        for name, value in sensor_dict.items():
            if name == "timestamp":
                continue
            c.execute(
                "INSERT INTO sensor_readings (ts_utc, sensor_name, value, synced) "
                "VALUES (?, ?, ?, 0)",
                (ts_iso, name, str(value)),
            )
        conn.commit()


def get_last_synced_id() -> int:
    """Return the id up to which we've synced to the cloud (legacy)."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT last_synced_id FROM sync_state WHERE id = 1")
        row = c.fetchone()
        return row[0] if row else 0


def get_unsynced_rows(last_id: int, limit: int = 500):
    """
    Legacy helper (not used by sync_to_neon anymore).
    Kept only so old code doesn't crash.
    """
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT id, ts_utc, sensor_name, value
            FROM sensor_readings
            WHERE id > ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (last_id, limit),
        )
        return c.fetchall()


def update_last_synced_id(new_id: int):
    """Legacy helper for old sync logic (no-op for Neon)."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "UPDATE sync_state SET last_synced_id = ? WHERE id = 1",
            (new_id,),
        )
        conn.commit()
