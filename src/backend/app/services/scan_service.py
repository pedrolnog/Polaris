import datetime as dt

from src.backend.app.services.device_service import get_or_create_network
from src.scanner.scan_models import ObservedDevice
from src.backend.app.schemas.models import Scan, Network

def create_scan(raw_data : list[ObservedDevice], net_interface : str) -> Scan:
    network = get_or_create_network(net_interface)

    return Scan(
        scan_datetime=dt.datetime.now(),
        observed_network=network,
        scan_data=raw_data
    )