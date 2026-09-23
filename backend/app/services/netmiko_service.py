import re
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
from sqlalchemy.orm import Session

from app.config import DEVICE_SSH_USERNAME, DEVICE_SSH_PASSWORD
from app.models import Device, Interface


class CiscoServiceError(Exception):
    pass


def fetch_ip_interfaces(device: Device) -> dict:
    """Se connecte en Telnet console GNS3 et récupère les IP des interfaces."""
    if not device.console_host or not device.console_port:
        raise CiscoServiceError("console_host/console_port manquant pour ce device")

    connection = {
        "device_type": "cisco_ios_telnet",
        "host": device.console_host,
        "port": device.console_port,
        "username": DEVICE_SSH_USERNAME,
        "password": DEVICE_SSH_PASSWORD,
        "timeout": 10,
    }

    try:
        conn = ConnectHandler(**connection)
        output = conn.send_command("show ip interface brief")
        conn.disconnect()
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as exc:
        raise CiscoServiceError(f"Connexion échouée sur {device.name} : {exc}")

    interfaces = {}
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        iface_name, ip = parts[0], parts[1]
        if ip.lower() != "unassigned":
            interfaces[iface_name] = ip
    return interfaces


def sync_device_ips(db: Session, device_id: int) -> dict:
    device = db.get(Device, device_id)
    if not device:
        raise CiscoServiceError("Device introuvable")
    if device.device_type != "router":
        raise CiscoServiceError("Uniquement supporté pour les routeurs pour l'instant")

    interfaces_data = fetch_ip_interfaces(device)

    # IP principale du device = première interface trouvée avec une IP
    if interfaces_data:
        device.ip_address = next(iter(interfaces_data.values()))

    for iface_name, ip in interfaces_data.items():
        interface = (
            db.query(Interface)
            .filter(Interface.device_id == device.id, Interface.name == iface_name)
            .first()
        )
        if not interface:
            interface = Interface(device_id=device.id, name=iface_name)
            db.add(interface)
        interface.ip_address = ip
        interface.status = "up"

    db.commit()
    return {"device": device.name, "interfaces_found": len(interfaces_data)}