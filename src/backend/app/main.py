from fastapi import FastAPI
from routers.devices import router
app = FastAPI(
    title="Polaris - Infrastructure Observability Platform",
    description="Polaris API",
    version="1.0",
)

app.include_router(router)