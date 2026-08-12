import asyncio
from fastapi import APIRouter
from src.backend.app.schemas.models import Device
from src.backend.app.services.device_service import get_device_netdata
router = APIRouter()

@router.get("/devices", response_model=list[Device])
async def get_devices():
    await asyncio.sleep(1)

    device_data = await get_device_netdata()

    return device_data