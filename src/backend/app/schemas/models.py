import datetime
from ipaddress import IPv4Address

import uuid6
from uuid import UUID
from pydantic import BaseModel, Field
from src.scanner.scan_models import ObservedDevice


class Device(BaseModel):
    id : UUID | str = Field(default_factory=lambda: str(uuid6.uuid7()))
    mac_address: str
    network_id: UUID | str
    ip_address: IPv4Address | str
    first_seen: datetime.datetime | None = None
    last_seen: datetime.datetime | None = None
    description : str | None = None
    status : str | None = None
    hostname: str | None = None
    category: str | None = None
    mac_vendor: str | None = None
    custom_name: str  | None = None

class DeviceRenameRequest(BaseModel):
    new_name : str

class Network(BaseModel):
    id : UUID | str = Field(default_factory=lambda: str(uuid6.uuid7()))
    name : str
    cidr : str | None = None
    description : str | None = None
    device_list : list[Device] | None = None

class Scan(BaseModel):
    id : UUID | str = Field(default_factory=lambda: str(uuid6.uuid7()))
    scan_datetime : datetime.datetime
    observed_network : Network
    scan_data : list[ObservedDevice]

class Change(BaseModel):
    id : UUID | str = Field(default_factory=lambda: str(uuid6.uuid7()))
    scan_id : str
    changed_device : UUID | str
    change_type_id : str
    old_value : IPv4Address | str | None = None
    new_value : IPv4Address | str | str
    description : str
    detected_at : datetime.datetime