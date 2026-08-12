from fastapi import APIRouter
from scanner.scanner import scanner
from scanner.scan_models import Device

router = APIRouter()

@router.get("/devices", response_model=list[Device])
async def get_devices():
    return scanner()