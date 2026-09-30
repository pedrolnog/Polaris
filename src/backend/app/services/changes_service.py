import datetime
from src.backend.app.database.connection import update_device
from src.scanner.scan_models import ObservedDevice
from src.backend.app.schemas.models import Change, Device


def check_changes(previous_devices : list[Device], current_devices : list[Device], raw_data : list[ObservedDevice], scan_id : str) -> list[Change]:
    previous_macs = {d.mac_address: d for d in previous_devices}
    currently_online_macs = {d.mac_address for d in raw_data}
    changes = []

    for current_device in current_devices:
        if current_device.mac_address not in previous_macs:
            change = Change(
                changed_device=current_device.id,
                scan_id=scan_id,
                detected_at=datetime.datetime.now(),
                change_type_id="003",
                old_value=None,
                new_value="ONLINE",
                description=f"Device ({current_device.mac_address}) has gone online."
            )
            changes.append(change)
        else:
            previous_mac = previous_macs[current_device.mac_address]
            if previous_mac.ip_address != current_device.ip_address:
                changes.append(Change(
                    changed_device=current_device.id,
                    scan_id=scan_id,
                    detected_at=datetime.datetime.now(),
                    change_type_id="002",
                    old_value=previous_mac.ip_address,
                    new_value=current_device.ip_address,
                    description = f"IP Changed from {previous_mac.ip_address} to {current_device.ip_address}."
                ))

    for previous_device in previous_devices:
        if previous_device.status != "OFFLINE" and previous_device.mac_address not in currently_online_macs:
            update_device(previous_device, "status", "OFFLINE")
            changes.append(Change(
                changed_device=previous_device.id,
                scan_id=scan_id,
                detected_at=datetime.datetime.now(),
                change_type_id="001",
                old_value = previous_device.status,
                new_value = "OFFLINE",
                description = f"Device ({previous_device.mac_address}) has gone offline."
            ))

    return changes