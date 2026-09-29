from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from src.backend.app.database.db_models import ScanHistory
from src.backend.app.schemas.models import Scan

SCHEMA_FILE = Path(__file__).parent / "schema.sql"


@contextmanager
def get_connection():
    conn = psycopg.connect("dbname=polaris_db user=postgres password=WsZuOk.4") # Tira a password

    try:
        yield conn
    finally:
        conn.close()

def create_table() -> None:
    sql_script = SCHEMA_FILE.read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
            conn.commit()

def save_scan(scan : Scan) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id from networks WHERE name = %s", (scan.observed_network.name,))
        if cursor.fetchone():
            cursor.execute(
                "INSERT INTO scans (id, network_id, scan_datetime, devices_found) VALUES (%s, %s, %s, %s)",
                (scan.id, scan.observed_network.id, dt.datetime.now(), len(scan.scan_data))
            )
        else:
            cursor.execute("INSERT INTO networks (id, name) VALUES (%s, %s)",
                           (scan.observed_network.id, scan.observed_network.name))
            cursor.execute(
                "INSERT INTO scans (id, network_id, scan_datetime, devices_found) VALUES (%s, %s, %s, %s)",
                (scan.id, scan.observed_network.id, dt.datetime.now(), len(scan.scan_data))
            )
        cursor.close()
        conn.commit()

def get_scan_history(identification : str | None = None, mac_address : str | None = None) -> list[ScanHistory]:
    with get_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)

        if identification is not None:
            cursor.execute("SELECT * FROM scans WHERE id = %s", (identification,))
        else:
            cursor.execute("SELECT * FROM scans")

        history = cursor.fetchall()
        cursor.close()

        return [ScanHistory(**row) for row in history]