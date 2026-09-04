from pydantic import BaseModel
import datetime as dt

from src.backend.app.schemas.models import Scan


class ScanHistory(BaseModel):
    id : str
    device_data : Scan
    search_time : dt.datetime