from contextlib import contextmanager
import datetime as dt
from functools import cache
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.backend.app.database.db_models import ScanHistory
from src.backend.app.schemas.models import Scan


@contextmanager
def get_connection():
    conn = psycopg.connect("dbname=test user=postgres password=WsZuOk.4")

    try:
        yield conn
    finally:
        conn.close()

def create_table() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS scan_history (ID UUID PRIMARY KEY, device_data JSONB, search_time TIMESTAMPTZ NOT NULL)")
        cursor.close()
        conn.commit()

def save_scan(scan : Scan) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scan_history (id, device_data, search_time) VALUES (%s, %s, %s)",
            (scan.id, Jsonb(scan.model_dump(mode='json')), dt.datetime.now())
        )
        cursor.close()
        conn.commit()

def get_scan_history(identification : str | None = None, mac_address : str | None = None) -> list[ScanHistory]:
    with get_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)

        if identification is not None:
            cursor.execute("SELECT * FROM scan_history WHERE id = %s", (identification,))

        elif mac_address is not None:
            cursor.execute("SELECT * FROM scan_history WHERE mac_address = %s", (mac_address, ))

        else:
            cursor.execute("SELECT * FROM scan_history")

        history = cursor.fetchall()
        cursor.close()

        return [ScanHistory(**row) for row in history]