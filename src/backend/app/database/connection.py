import os
from contextlib import contextmanager
import datetime as dt
from pathlib import Path
import psycopg
from dotenv import load_dotenv, find_dotenv
from psycopg.rows import dict_row
from src.backend.app.schemas.models import Change
from src.backend.app.database.db_models import ScanHistory
from src.backend.app.schemas.models import Scan, Network, Device

SCHEMA_FILE = Path(__file__).parent / "schema.sql"
ALLOWED_FIELDS = {"status", "ip_address", "hostname", "custom_name"}
load_dotenv(find_dotenv())

@contextmanager
def get_connection():
    conn = psycopg.connect(f"dbname=polaris_db user={os.getenv("DB_USER")} password={os.getenv("DB_PASS")}")
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

# SCANS

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

# DEVICES

def get_device(id : str | None = None, mac_address : str | None = None, name : str | None = None) -> Device:
    with get_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)
        if id:
            cursor.execute(
                "SELECT * FROM devices WHERE id = %s",
                (id,)
            )
            device = cursor.fetchone()
            if device:
                return Device(**device)
            else:
                raise ValueError("Device not found")
        elif mac_address:
            cursor.execute(
                "SELECT * FROM devices WHERE mac_address = %s",
                (mac_address,)
            )
            device = cursor.fetchone()
            if device:
                return Device(**device)
            else:
                raise ValueError("Device not found")
        elif name:
            cursor.execute(
                "SELECT * FROM devices WHERE custom_name = %s",
                (name, )
            )
            device = cursor.fetchone()
            if device:
                return Device(**device)
            else:
                raise ValueError("Device not found")
        else:
            raise ValueError("Either mac_address, id or name must be provided.")

def get_all_devices() -> list[Device]:
    with get_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)
        cursor.execute("SELECT * FROM devices")
        devices = cursor.fetchall()
        cursor.close()

        device_list = []

        for row in devices:
            for key in row.keys():
                if type(row[key]) is not str:
                    row[key] = str(row[key])

            device_list.append(Device(**row))


        return device_list

def save_observed_device(scan : Scan):
    with get_connection() as conn:
        cursor = conn.cursor()
        for device in scan.scan_data:
            d = Device(mac_address=device.mac_address, ip_address=device.ip_address)

            cursor.execute(
                "INSERT INTO devices (id, mac_address, ip_address, network_id, last_seen, status) VALUES (%s, %s, %s, %s, NOW(), 'ONLINE') ON CONFLICT (network_id, mac_address) DO UPDATE SET ip_address = EXCLUDED.ip_address, last_seen = NOW(), status = 'ONLINE';",
                (d.id, d.mac_address, d.ip_address, scan.observed_network.id)
            )
        cursor.close()
        conn.commit()

def update_device(device : Device, parameter : str, new_value : str) -> None:
    if parameter not in ALLOWED_FIELDS:
        raise ValueError(f"Invalid parameter: {parameter}")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE devices SET {parameter} = %s WHERE id = %s", (new_value, device.id)
        )
        cursor.close()
        conn.commit()

# NETWORK

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

# CHANGES

def save_changes(changes : list[Change]) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()

        for change in changes:
            cursor.execute("INSERT INTO changes (id, changed_device, scan_id, change_type_id, description, old_value, new_value, detected_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (change.id, change.changed_device, change.scan_id, change.change_type_id, change.description, change.old_value, change.new_value, change.detected_at))
        cursor.close()
        conn.commit()

def get_changes() -> list[Change]:
    with get_connection() as conn:
        cursor = conn.cursor(row_factory=dict_row)
        cursor.execute("SELECT * FROM changes")
        changes = cursor.fetchall()
        cursor.close()

        change_list = []

        for row in changes:
            for key in row.keys():
                if type(row[key]) is not str:
                    row[key] = str(row[key])

            print("\n\n" + str(row) + "\n\n")
            change_list.append(Change(**row))

        return change_list
