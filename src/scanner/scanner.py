import socket
import psutil
import ipaddress

from scapy.layers.l2 import Ether, ARP, srp
from src.scanner.scan_models import ObservedDevice

def list_interfaces():
    interfaces = psutil.net_if_addrs().keys()

    interface_list = [i for i in interfaces]

    return interface_list

# Checa se a rede é válida para escaneamento
def is_valid_network(subnet_str: str) -> bool:
    try:
        net = ipaddress.IPv4Network(subnet_str, strict=False)

        if net.is_loopback or net.is_link_local:
            return False

        if not net.is_private:
            return False

        # Caso a rede tenha uma submáscara grande, é ignorada.
        if net.prefixlen < 20:
            return False

        return True
    except ValueError:
        return False

# Faz o tratamento e retorna a sub-rede
def find_subnet(interface_name : str) -> tuple[str, str]:
    interface_address = psutil.net_if_addrs().get(interface_name)

    if interface_address:
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
    else:
        raise ValueError(f"Invalid interface name ({interface_name}).")

    raise RuntimeError(f"Invalid interface ({interface_name}) or no active IPv4.")

def find_all_subnets() -> list[tuple[str, str]]:
    interfaces = list_interfaces()
    subnet_list = []

    for i in interfaces:
        try:
            subnet, iface = find_subnet(i)

            if is_valid_network(subnet):
                subnet_list.append((subnet, iface))

        except (RuntimeError, ValueError):
            continue

    return subnet_list

def scanner(info : tuple[str, str]) -> tuple[list[ObservedDevice], str]:
    broadcast_frame = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request = ARP(pdst=info[0])

    packet = broadcast_frame / arp_request

    answered, _ = srp(packet, iface=info[1], timeout=2, verbose=False)

    obs_device_list = []
    if answered:
        for sent, received in answered:
            device = ObservedDevice(ip_address=received.psrc, mac_address=received.hwsrc)

            obs_device_list.append(device)
    else:
        return [], info[1]

    return obs_device_list, info[1]
