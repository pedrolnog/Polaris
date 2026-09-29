from uuid import UUID
from pydantic import BaseModel
import datetime as dt

class ScanHistory(BaseModel):
    id : UUID
    network_id : UUID
    scan_datetime : dt.datetime
    devices_found : int