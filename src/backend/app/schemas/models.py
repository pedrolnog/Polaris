from pydantic import BaseModel, Field

class Device(BaseModel):
    id : int
    mac_address: str
    ip_address: str
    hostname: str | None = None
    category: str | None = None
    mac_vendor: str | None = None
    name: str  | None = None
