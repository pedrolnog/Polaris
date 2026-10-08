from fastapi import APIRouter, HTTPException

from src.backend.app.database.connection import update_device
from src.backend.app.database.connection import get_all_devices, get_device
from src.backend.app.schemas.models import Device, DeviceRenameRequest

devices_router = APIRouter()

@devices_router.get("/devices", status_code=200, response_model=list[Device])
async def devices():
    try:
        return get_all_devices()
    except ValueError:
        raise HTTPException(status_code=500, detail="Unable to retrieve devices")

@devices_router.get("/devices/{device_id}", status_code=200, response_model=Device)
async def get_device_by_id(device_id: str):
    try:
        return get_device(device_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Device not found")

@devices_router.patch("/devices/{device_id}", status_code=200, response_model=Device)
async def rename_device(device_id : str, payload : DeviceRenameRequest):
    update_device(device_id, "custom_name", payload.new_name)
    return get_device(device_id)