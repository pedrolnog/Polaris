import datetime
import uuid6
from pydantic import BaseModel, Field
from src.scanner.scan_models import ObservedDevice


class Device(BaseModel):
    id : int
    mac_address: str
    ip_address: str
    hostname: str | None = None
    category: str | None = None
    mac_vendor: str | None = None
    name: str  | None = None

class Network(BaseModel):
    name : str
    description : str | None = None
    device_list : list[Device] | None = None

class Scan(BaseModel):
    id : str = Field(default_factory=lambda: str(uuid6.uuid7()))
    scan_datetime : datetime.datetime
    observed_network : Network
    raw_scan_data : list[ObservedDevice]