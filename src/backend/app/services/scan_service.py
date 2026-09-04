import datetime as dt
from src.scanner.scan_models import ObservedDevice
from src.backend.app.schemas.models import Scan, Network

def create_scan(raw_data : list[ObservedDevice], net_interface : str) -> Scan:
    network = Network(
        name=net_interface,
    )

    return Scan(
        scan_datetime=dt.datetime.now(),
        observed_network=network,
        raw_scan_data=raw_data
    )