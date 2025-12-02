#!/usr/bin/env python3
import os
import sqlite3
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path("/home/pi/picar-x")

# Load env with PG_DSN
load_dotenv(BASE_DIR / ".env")
PG_DSN = os.getenv("PG_DSN")
if not PG_DSN:
    raise RuntimeError("PG_DSN missing in .env")

LOCAL_DB = BASE_DIR / "logs" / "picarx_data.db"


def get_sqlite_conn():
    return sqlite3.connect(LOCAL_DB)


def get_neon_conn():
    # Use Neon connection string as-is (contains sslmode/etc)
    return psycopg2.connect(PG_DSN)


def fetch_unsynced(limit=200):
    conn = get_sqlite_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, ts_utc, sensor_name, value
        FROM sensor_readings
        WHERE synced = 0
        ORDER BY id ASC
        LIMIT ?;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def mark_synced(ids):
    if not ids:
        return
    conn = get_sqlite_conn()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE sensor_readings SET synced = 1 WHERE id IN ({','.join('?'*len(ids))})",
        ids,
    )
    conn.commit()
    conn.close()


def push_to_neon(rows):
    if not rows:
        print("No unsynced rows to send.")
        return

    with get_neon_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO sensor_readings (id, ts_utc, sensor_name, value)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (r["id"], r["ts_utc"], r["sensor_name"], r["value"]),
                )
        conn.commit()


def main():
    try:
        rows = fetch_unsynced(limit=500)
    except Exception as e:
        print("Error reading from local SQLite:", e)
        return

    if not rows:
        print("Nothing to sync.")
        return

    print(f"Found {len(rows)} rows to sync...")

    try:
        push_to_neon(rows)
    except Exception as e:
        print("Error pushing to Neon (probably no internet):", e)
        return

    ids = [str(r["id"]) for r in rows]
    mark_synced(ids)
    print(f"Synced {len(ids)} rows and marked them as synced in SQLite.")


if __name__ == "__main__":
    main()
