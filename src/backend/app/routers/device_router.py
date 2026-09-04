from fastapi import APIRouter
from database.connection import get_scan_history, save_scan
from database.db_models import ScanHistory
from src.scanner.scanner import scanner
from src.backend.app.services.scan_service import create_scan
from src.backend.app.schemas.models import Scan

device_router = APIRouter()

@device_router.get("/devices", status_code=200, response_model=Scan)
async def get_devices():
    raw_data, net_interface = scanner()

    device_data = create_scan(raw_data, net_interface)

    return device_data

@device_router.get("/devices/history", status_code=200, response_model=list[ScanHistory])
async def get_devices_history(id : str | None = None, mac_address: str | None = None):
    if id is not None:
        return get_scan_history(identification=id)
    elif mac_address is not None:
        return get_scan_history(mac_address=mac_address)
    else:
        return get_scan_history()