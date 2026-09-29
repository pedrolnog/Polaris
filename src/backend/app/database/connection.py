from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from src.backend.app.database.db_models import ScanHistory
from src.backend.app.schemas.models import Scan, Network

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

def get_or_create_network(network_name : str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, cidr, description FROM networks WHERE name = %s", (network_name, ))
        network = cursor.fetchone()
        if network:
            cursor.close()
            conn.commit()
            return Network(id=str(network[0]), name=network_name, description=network[2])
        else:
            network = Network(name=network_name)
            cursor.execute("INSERT INTO networks (id, name) VALUES (%s, %s)", (network.id, network_name))
            cursor.close()
            conn.commit()
            return network
