from fastapi import APIRouter, HTTPException, BackgroundTasks

from src.backend.app.services.scan_service import exec_scan_pipeline
from src.backend.app.database.connection import get_scan_history
from src.backend.app.database.db_models import ScanHistory
from src.backend.app.schemas.models import Scan

scan_router = APIRouter()

# Gatilho de diagnóstico. Força a varredura no momento que é disparada.
@scan_router.post("/scan", status_code=200, response_model=Scan | None)
async def scan(interface: str):
    try:
        return await exec_scan_pipeline(interface)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@scan_router.get("/scan/history", status_code=200, response_model=list[ScanHistory])
async def get_previous_scans(id : str | None = None):
    if id:
        return get_scan_history(identification=id)
    else:
        return get_scan_history()