import asyncio
import datetime as dt

from src.scanner.scanner import scanner, find_subnet
from src.backend.app.services.changes_service import check_changes
from src.backend.app.services.device_service import enrich_devices_task
from src.backend.app.database.connection import get_or_create_network, get_network_devices, save_scan, \
    save_observed_device, save_changes
from src.scanner.scan_models import ObservedDevice
from src.backend.app.schemas.models import Scan

def create_scan(raw_data : list[ObservedDevice], net_interface : str) -> Scan:
    network = get_or_create_network(net_interface)

    return Scan(
        scan_datetime=dt.datetime.now(),
        observed_network=network,
        scan_data=raw_data
    )

async def exec_scan_pipeline(interface_name : str) -> Scan:
    raw_data, net_interface = await asyncio.to_thread(scanner, find_subnet(interface_name))
    device_data = create_scan(raw_data, net_interface)

    previous_devices = get_network_devices(device_data.observed_network.id)

    save_scan(device_data)
    save_observed_device(device_data)

    current_devices = get_network_devices(device_data.observed_network.id)

    changes_list = check_changes(previous_devices, current_devices, raw_data, device_data.id)
    save_changes(changes_list)

    new_device_ids = [c.changed_device for c in changes_list if c.change_type_id == "003"]
    if new_device_ids:
        asyncio.create_task(enrich_devices_task(new_device_ids))

    return device_data