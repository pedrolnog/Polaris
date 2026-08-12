from dataclasses import dataclass

@dataclass
class ObservedDevice:
    mac_address: str
    ip_address: str