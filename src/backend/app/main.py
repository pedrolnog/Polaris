from fastapi import FastAPI
from src.backend.app.routers.devices import router
app = FastAPI(
    title="Polaris - Infrastructure Observability Platform",
    description="Polaris API",
    version="0.1",
)

app.include_router(router)