from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.backend.app.services.device_service import enrich_devices_task
from src.backend.app.services.changes_service import check_changes
from src.backend.app.database.connection import get_scan_history, save_scan, save_observed_device, save_changes, \
    get_changes, get_all_devices
from src.backend.app.database.db_models import ScanHistory
from src.scanner.scanner import scanner, find_subnet
from src.backend.app.services.scan_service import create_scan
from src.backend.app.schemas.models import Scan, Change

device_router = APIRouter()

@device_router.get("/scan", status_code=200, response_model=Scan | None)
async def scan(interface: str, background_tasks: BackgroundTasks):
    try:
        raw_data, net_interface = scanner(find_subnet(interface))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    device_data = create_scan(raw_data, net_interface)

    previous_devices = get_all_devices()

    save_scan(device_data)
    save_observed_device(device_data)

    current_devices = get_all_devices()

    changes_list = check_changes(previous_devices, current_devices, raw_data, device_data.id)
    save_changes(changes_list)

    new_device_ids = [c.changed_device for c in changes_list if c.change_type_id == "003"]
    print(new_device_ids)
    if new_device_ids:
        background_tasks.add_task(enrich_devices_task, new_device_ids)

    return device_data

@device_router.get("/changes", status_code=200, response_model=list[Change])
async def changes():
    return get_changes()

@device_router.get("/scan/history", status_code=200, response_model=list[ScanHistory])
async def get_previous_scans(id : str | None = None, mac_address: str | None = None):
    if id is not None:
        return get_scan_history(identification=id)
    elif mac_address is not None:
        return get_scan_history(mac_address=mac_address)
    else:
        return get_scan_history()