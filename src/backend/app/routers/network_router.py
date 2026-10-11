from fastapi import APIRouter, HTTPException

from src.backend.app.database.connection import get_network
from src.backend.app.database.connection import get_all_networks, get_network_devices
from src.backend.app.schemas.models import Network, Device
from src.scanner.scanner import list_interfaces

network_router = APIRouter()

@network_router.get("/networks", status_code=200, response_model=list[Network])
async def get_networks() -> list[Network]:
    return get_all_networks()

@network_router.get("/networks/{network_id}", status_code=200, response_model=Network)
async def get_single_network(network_id: str) -> Network:
    if network_id:
        try:
            return get_network(network_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Network not found")
    else:
        raise HTTPException(status_code=400, detail="No parameters provided")

@network_router.get("/networks/{network_id}/devices", status_code=200, response_model=list[Device])
async def network_devices(network_id: str) -> list[Device]:
    return get_network_devices(network_id)

@network_router.get("/networks/interfaces", status_code=200, response_model=list[str])
async def get_network_interfaces():
    return list_interfaces()