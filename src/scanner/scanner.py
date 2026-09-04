import socket
import psutil
from scapy.layers.l2 import Ether, ARP, srp
from src.scanner.scan_models import ObservedDevice

def list_interfaces():
    interfaces = psutil.net_if_addrs().keys()

    interface_list = [i for i in interfaces]

    return interface_list

def find_subnet(interface_name : str) -> tuple[str, str] | None:
    interface_address = psutil.net_if_addrs().get(interface_name)

    for i in interface_address:
        if i.family == socket.AF_INET:

            address = i.address.split(".")
            bin_address = [int(x) for x in address]

            netmask = i.netmask.split(".")
            bin_netmask = [int(x) for x in netmask]

            netmask_bit_count = 0

            for n in bin_netmask:
                netmask_bit_count += n.bit_count()

            net_address = [(bin_address[i] & bin_netmask[i]) for i in range(len(bin_address))]

            subnet_address = f"{".".join(str(i) for i in net_address)}/{netmask_bit_count}"

            return subnet_address, interface_name
    raise RuntimeError(f"Invalid interface ({interface_name}) or no active IPv4.")

def scanner(info : tuple[str, str]) -> tuple[list[ObservedDevice], str]:
    broadcast_frame = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = ARP(pdst=info[0])

    packet = broadcast_frame / arp_request

    answered, _ = srp(packet, timeout=2, verbose=False)

    obs_device_list = []
    if answered:
        for sent, received in answered:
            device = ObservedDevice(ip_address=received.psrc, mac_address=received.hwsrc)

            obs_device_list.append(device)
    else:
        print("No devices found.")
        return [], info[1]

    return obs_device_list, info[1]
