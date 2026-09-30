import datetime
import uuid6
from pydantic import BaseModel, Field
from src.scanner.scan_models import ObservedDevice


class Device(BaseModel):
    id : str = Field(default_factory=lambda: str(uuid6.uuid7()))
    mac_address: str
    ip_address: str
    description : str | None = None
    status : str | None = None
    hostname: str | None = None
    category: str | None = None
    mac_vendor: str | None = None
    name: str  | None = None

class Network(BaseModel):
    id : str = Field(default_factory=lambda: str(uuid6.uuid7()))
    name : str
    description : str | None = None
    device_list : list[Device] | None = None

class Scan(BaseModel):
    id : str = Field(default_factory=lambda: str(uuid6.uuid7()))
    scan_datetime : datetime.datetime
    observed_network : Network
    scan_data : list[ObservedDevice]

class Change(BaseModel):
    id : str = Field(default_factory=lambda: str(uuid6.uuid7()))
    scan_id : str
    changed_device : str
    change_type_id : str
    old_value : str | None = None
    new_value : str
    description : str
    detected_at : datetime.datetime