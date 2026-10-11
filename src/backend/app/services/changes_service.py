import datetime
from src.backend.app.database.connection import update_device
from src.scanner.scan_models import ObservedDevice
from src.backend.app.schemas.models import Change, Device


def check_changes(previous_devices : list[Device], current_devices : list[Device], raw_data : list[ObservedDevice], scan_id : str) -> list[Change]:
    previous_macs = {d.mac_address: d for d in previous_devices}
    currently_online_macs = {d.mac_address for d in raw_data}
    changes = []

    for current_device in current_devices:

        # CASO 1: Dispositivo novo (nunca visto nesta rede antes)
        if current_device.mac_address not in previous_macs:
            change = Change(
                changed_device=current_device.id,
                scan_id=scan_id,
                detected_at=datetime.datetime.now(),
                change_type_id="003",
                old_value=None,
                new_value="ONLINE",
                description=f"Device ({current_device.mac_address}) has connected for the first time."
            )
            changes.append(change)
        else:
            previous_mac = previous_macs[current_device.mac_address]

            # CASO 2: Dispositivo já conhecido que estava OFFLINE e voltou a ficar ONLINE
            if previous_mac.status == "OFFLINE":
                changes.append(Change(
                    changed_device=current_device.id,
                    scan_id=scan_id,
                    detected_at=datetime.datetime.now(),
                    change_type_id="004",
                    old_value="OFFLINE",
                    new_value="ONLINE",
                    description=f"Device ({current_device.mac_address}) is now online."
                ))

            # CASO 3: Dispositivo trocou de IP
            if str(previous_mac.ip_address) != str(current_device.ip_address):
                changes.append(Change(
                    changed_device=current_device.id,
                    scan_id=scan_id,
                    detected_at=datetime.datetime.now(),
                    change_type_id="002",
                    old_value=str(previous_mac.ip_address),
                    new_value=str(current_device.ip_address),
                    description=f"IP Changed from {previous_mac.ip_address} to {current_device.ip_address}."
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