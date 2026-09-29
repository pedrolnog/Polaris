from fastapi import APIRouter, HTTPException

from src.backend.app.database.connection import get_scan_history, save_scan, save_observed_device
from src.backend.app.database.db_models import ScanHistory
from src.scanner.scanner import scanner, find_subnet
from src.backend.app.services.scan_service import create_scan
from src.backend.app.schemas.models import Scan
device_router = APIRouter()

@device_router.get("/scan", status_code=200, response_model=Scan | None)
async def scan(interface: str):
    try:
        raw_data, net_interface = scanner(find_subnet(interface))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    device_data = create_scan(raw_data, net_interface)
    save_scan(device_data)
    save_observed_device(device_data)

    return device_data

@device_router.get("/scan/history", status_code=200, response_model=list[ScanHistory])
async def get_previous_scans(id : str | None = None, mac_address: str | None = None):
    if id is not None:
        return get_scan_history(identification=id)
    elif mac_address is not None:
        return get_scan_history(mac_address=mac_address)
    else:
        return get_scan_history()