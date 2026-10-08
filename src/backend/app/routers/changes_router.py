from fastapi import APIRouter
from src.backend.app.database.connection import get_changes
from src.backend.app.schemas.models import Change

changes_router = APIRouter()

@changes_router.get("/changes", status_code=200, response_model=list[Change])
async def changes(limit: int = 50, offset: int = 0):
    return get_changes()