import asyncio

import psycopg_pool
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.backend.app.services.scan_service import exec_scan_pipeline
from src.scanner.scanner import find_all_subnets
from src.backend.app.routers.changes_router import changes_router
from src.backend.app.routers.devices_router import devices_router
from src.backend.app.routers.network_router import network_router
from src.backend.app.routers.scan_router import scan_router
from src.backend.app.database.connection import create_table, pool


async def periodic_scan_loop():
    while True:
        try:
            for subnet, iface in find_all_subnets():
                await exec_scan_pipeline(iface)
                print("[Observabilidade] Scan periódico executado com sucesso.")
        except asyncio.CancelledError:
            print("[Observabilidade] Encerrando loop de scan...")
            break
        except Exception as e:
            print(f"[Observabilidade] Erro no scan periódico: {e}")

        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_table()
    scanner_task = asyncio.create_task(periodic_scan_loop())

    yield

    scanner_task.cancel()
    try:
        await scanner_task
    except asyncio.CancelledError:
        pass

    pool.close()

app = FastAPI(
    title="Polaris - Infrastructure Observability Platform",
    description="Polaris API",
    version="0.1",
    lifespan=lifespan,
)

app.include_router(scan_router)
app.include_router(network_router)
app.include_router(changes_router)
app.include_router(devices_router)