from fastapi import APIRouter

from src.scanner.scanner import list_interfaces

network_router = APIRouter()

@network_router.get("/networks/interfaces", status_code=200, response_model=list[str])
async def get_network_interfaces():
    return list_interfaces()