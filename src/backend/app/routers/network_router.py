from fastapi import APIRouter

network_router = APIRouter()

@network_router.get("/networks/interfaces", status_code=200)
async def get_network_interfaces():
