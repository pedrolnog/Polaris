from dataclasses import dataclass

@dataclass
class Device:
    mac_address: str # Identificador principal de Device.
    ip_address: str
    hostname: str | None = None
    category: str | None = None
    mac_vendor: str | None = None
    name: str  | None = None

@dataclass
class ObservedDevice:
    mac_address: str
    ip_address: str