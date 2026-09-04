from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.backend.app.routers.network_router import network_router
from src.backend.app.routers.device_router import device_router
from src.backend.app.database.connection import create_table

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_table()
    yield

app = FastAPI(
    title="Polaris - Infrastructure Observability Platform",
    description="Polaris API",
    version="0.1",
    lifespan=lifespan,
)

app.include_router(device_router)
app.include_router(network_router)