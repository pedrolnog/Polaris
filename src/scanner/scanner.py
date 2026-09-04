import socket
import psutil
from scapy.layers.l2 import Ether, ARP, srp
from src.scanner.scan_models import ObservedDevice


def find_subnet(interface_name : str | None = None) -> tuple[str, str] | None:
    interfaces = psutil.net_if_addrs().keys()

    if __name__ == "__main__" and interface_name is None:
        interface_name = ""
        while not interface_name in interfaces:
            n = 0
            print("Interfaces: ")
            for i in interfaces:
                n += 1
                print(f" - {i}")

            interface_name = input("Choose a network interface:\n")

            if not interface_name in interfaces:
                print("Interface not found. Try again.")
    elif interface_name is None:
        return None

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

    return None

def scanner(info : tuple[str, str] | None = None) -> tuple[list[ObservedDevice], str] | None:
    if info is None:
        info = find_subnet()

    if info is not None:
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
    else:
        return None