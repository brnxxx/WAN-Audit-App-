import re
import ipaddress
import platform
import subprocess

import httpx
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from sqlalchemy.orm import Session

from app.config import DEVICE_SSH_PASSWORD, DEVICE_SSH_USERNAME, GNS3_URL
from app.models import Device, Interface, TopologyLink, Site, Backbone, GNS3Project


class GNS3ServiceError(Exception):
    """Levée quand la communication avec GNS3 échoue."""
    pass


def _normalize_name(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _get(endpoint: str) -> list[dict] | dict:
    url = f"{GNS3_URL}{endpoint}"
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        return data
    except httpx.RequestError as exc:
        raise GNS3ServiceError(f"Impossible de contacter GNS3 : {exc}")
    except httpx.HTTPStatusError as exc:
        allow = exc.response.headers.get("allow")
        suffix = f" (méthodes acceptées : {allow})" if allow else ""
        raise GNS3ServiceError(
            f"GNS3 a renvoyé une erreur : {exc.response.status_code}{suffix}"
        )


def get_projects() -> list[dict]:
    data = _get("/v2/projects")
    if isinstance(data, list):
        return data
    return []


def get_project_nodes(project_id: str) -> list[dict]:
    data = _get(f"/v2/projects/{project_id}/nodes")
    if isinstance(data, list):
        return data
    return []


def get_project_node(project_id: str, node_id: str) -> dict:
    data = _get(f"/v2/projects/{project_id}/nodes/{node_id}")
    return data if isinstance(data, dict) else {}


def get_project_links(project_id: str) -> list[dict]:
    data = _get(f"/v2/projects/{project_id}/links")
    if isinstance(data, list):
        return data
    return []


def _action(endpoint: str, method: str = "post") -> dict:
    url = f"{GNS3_URL}{endpoint}"
    try:
        response = getattr(httpx, method)(url, timeout=10.0)
        response.raise_for_status()
        if not response.content:
            return {"status": "ok"}
        data = response.json()
        return data if isinstance(data, dict) else {"data": data}
    except httpx.RequestError as exc:
        raise GNS3ServiceError(f"Impossible de contacter GNS3 : {exc}")
    except httpx.HTTPStatusError as exc:
        allow = exc.response.headers.get("allow")
        suffix = f" (méthodes acceptées : {allow})" if allow else ""
        raise GNS3ServiceError(
            f"GNS3 a renvoyé une erreur : {exc.response.status_code}{suffix}"
        )


def get_project(project_id: str) -> dict:
    data = _get(f"/v2/projects/{project_id}")
    return data if isinstance(data, dict) else {}


def start_project(project_id: str) -> dict:
    # GNS3 exposes project lifecycle actions as POST endpoints.
    return _action(f"/v2/projects/{project_id}/open")


def stop_project(project_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/close")


def start_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/start")


def stop_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/stop")


def reload_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/reload")


def _validate_target(target: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        return ipaddress.ip_address(target)
    except ValueError as exc:
        raise GNS3ServiceError("La cible doit être une adresse IP valide") from exc


def _run_from_node(project_id: str, source_node_id: str, command: str) -> tuple[str, str]:
    node = get_project_node(project_id, source_node_id)
    host = node.get("console_host")
    port = node.get("console")
    if not host or not port:
        raise GNS3ServiceError(
            f"Le nœud {node.get('name', source_node_id)} n'a pas de console GNS3 disponible"
        )
    try:
        conn = ConnectHandler(
            device_type="cisco_ios_telnet",
            host=host,
            port=int(port),
            username=DEVICE_SSH_USERNAME or "",
            password=DEVICE_SSH_PASSWORD or "",
            timeout=10,
            auth_timeout=10,
            banner_timeout=10,
            fast_cli=False,
        )
        output = conn.send_command_timing(command, read_timeout=15)
        conn.disconnect()
    except (NetmikoTimeoutException, NetmikoAuthenticationException, OSError) as exc:
        raise GNS3ServiceError(
            f"Connexion impossible au nœud {node.get('name', source_node_id)} : {exc}"
        ) from exc
    return output, node.get("name", source_node_id)


def execute_router_command(project_id: str, source_node_id: str, command: str) -> dict:
    cleaned_command = " ".join(command.strip().split())
    allowed_commands = {
        item["command"]
        for item in COMMAND_GUIDE
        if item["platform"] == "Cisco IOS" and item["risk"] == "read-only"
    }
    if cleaned_command not in allowed_commands:
        raise GNS3ServiceError(
            "Commande refusée. Utilisez une commande Cisco IOS de lecture proposée par le guide."
        )
    node = get_project_node(project_id, source_node_id)
    node_type = str(node.get("node_type") or "").lower()
    if node_type not in {"dynamips", "iou", "qemu"}:
        raise GNS3ServiceError("La console de commandes est réservée aux routeurs Cisco du projet")
    output, source = _run_from_node(project_id, source_node_id, cleaned_command)
    return {
        "project_id": project_id,
        "source_node_id": source_node_id,
        "source": source,
        "command": cleaned_command,
        "output": output[-12000:],
    }


def _parse_ping_output(output: str, count: int, return_code: int, target: str) -> dict:
    received_match = re.search(r"(\d+)\s*(?:packets? received|received)", output, re.IGNORECASE)
    sent_match = re.search(r"(\d+)\s*(?:packets? transmitted|sent)", output, re.IGNORECASE)
    loss_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*(?:packet )?loss", output, re.IGNORECASE)
    rtt_match = re.search(r"=\s*([\d.,]+)\s*/\s*([\d.,]+)\s*/\s*([\d.,]+)", output)
    if not rtt_match:
        rtt_match = re.search(
            r"minimum\s*=\s*([\d.,]+).*?maximum\s*=\s*([\d.,]+).*?average\s*=\s*([\d.,]+)",
            output,
            re.IGNORECASE,
        )
    cisco_match = re.search(r"\((\d+)\s*/\s*(\d+)\)", output)
    if cisco_match:
        packets_received = int(cisco_match.group(1))
        packets_sent = int(cisco_match.group(2))
    else:
        packets_sent = int(sent_match.group(1)) if sent_match else count
        packets_received = int(received_match.group(1)) if received_match else (
            packets_sent if return_code == 0 and output else 0
        )
    if not rtt_match:
        rtt_match = re.search(
            r"round-trip.*?=\s*([\d.,]+)\s*/\s*([\d.,]+)\s*/\s*([\d.,]+)",
            output,
            re.IGNORECASE,
        )
    packet_loss = (
        float(loss_match.group(1).replace(",", "."))
        if loss_match
        else round((1 - packets_received / packets_sent) * 100, 1)
        if packets_sent
        else 100.0
    )
    return {
        "target": target,
        "reachable": packets_received > 0 and packet_loss < 100,
        "return_code": return_code,
        "packets_sent": packets_sent,
        "packets_received": packets_received,
        "packet_loss_percent": packet_loss,
        "latency_min_ms": float(rtt_match.group(1).replace(",", ".")) if rtt_match else None,
        "latency_avg_ms": float(rtt_match.group(2).replace(",", ".")) if rtt_match else None,
        "latency_max_ms": float(rtt_match.group(3).replace(",", ".")) if rtt_match else None,
        "output": output[-4000:],
    }


def ping_host(
    target: str,
    count: int = 4,
    project_id: str | None = None,
    source_node_id: str | None = None,
) -> dict:
    address = _validate_target(target)
    count = max(1, min(count, 5))
    if bool(project_id) != bool(source_node_id):
        raise GNS3ServiceError("Le projet et le nœud source doivent être fournis ensemble")
    if project_id and source_node_id:
        output, source = _run_from_node(project_id, source_node_id, f"ping {target} repeat {count}")
        result = _parse_ping_output(output, count, 0, target)
        result.update({"source": source, "execution": "gns3-node"})
        return result
    family_flag = "-6" if address.version == 6 else "-4"
    command = ["ping", family_flag]
    command += ["-n", str(count)] if platform.system() == "Windows" else ["-c", str(count)]
    command.append(target)
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    except subprocess.TimeoutExpired as exc:
        raise GNS3ServiceError("Le ping a dépassé le délai maximal") from exc
    output = process.stdout or process.stderr
    result = _parse_ping_output(output, count, process.returncode, target)
    result.update({"source": "Serveur backend", "execution": "server"})
    return result


def traceroute_host(
    target: str,
    project_id: str | None = None,
    source_node_id: str | None = None,
) -> dict:
    address = _validate_target(target)
    if bool(project_id) != bool(source_node_id):
        raise GNS3ServiceError("Le projet et le nœud source doivent être fournis ensemble")
    if project_id and source_node_id:
        output, source = _run_from_node(project_id, source_node_id, f"traceroute {target}")
        return_code = 0
        execution = "gns3-node"
    else:
        family_flag = "-6" if address.version == 6 else "-4"
        command = (
            ["tracert", family_flag, "-d", "-h", "12", "-w", "1000", target]
            if platform.system() == "Windows"
            else ["traceroute", "-n", "-m", "12", "-w", "1", target]
        )
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
        except FileNotFoundError as exc:
            raise GNS3ServiceError("L'outil traceroute/tracert n'est pas disponible sur le serveur") from exc
        except subprocess.TimeoutExpired as exc:
            raise GNS3ServiceError("Le traceroute a dépassé le délai maximal") from exc
        output = process.stdout or process.stderr
        return_code = process.returncode
        source = "Serveur backend"
        execution = "server"
    hops = []
    for line in output.splitlines():
        match = re.match(r"\s*(\d+)\s+(.*)", line)
        if match:
            hops.append({"hop": int(match.group(1)), "detail": match.group(2).strip()})
    return {
        "target": target,
        "reachable": bool(hops) and return_code == 0,
        "return_code": return_code,
        "hop_count": len(hops),
        "hops": hops,
        "output": output[-5000:],
        "source": source,
        "execution": execution,
    }


COMMAND_GUIDE = [
    {"platform": "Cisco IOS", "category": "Interfaces", "command": "show ip interface brief", "purpose": "Vue rapide des interfaces, adresses IP et états.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Routing", "command": "show ip route", "purpose": "Afficher la table de routage IPv4.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Routing", "command": "show ip protocols", "purpose": "Inspecter les protocoles de routage actifs.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Neighbors", "command": "show cdp neighbors detail", "purpose": "Découvrir les voisins Cisco et leurs interfaces.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Neighbors", "command": "show lldp neighbors detail", "purpose": "Découvrir les voisins LLDP.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Performance", "command": "show processes cpu sorted", "purpose": "Identifier les processus consommant le CPU.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Performance", "command": "show memory statistics", "purpose": "Contrôler l'utilisation mémoire.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "Logs", "command": "show logging", "purpose": "Lire les événements et erreurs système.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "BGP", "command": "show ip bgp summary", "purpose": "Vérifier les voisins BGP et le nombre de préfixes.", "risk": "read-only"},
    {"platform": "Cisco IOS", "category": "OSPF", "command": "show ip ospf neighbor", "purpose": "Vérifier les adjacences OSPF.", "risk": "read-only"},
    {"platform": "Linux", "category": "Diagnostics", "command": "ip addr", "purpose": "Afficher les interfaces et adresses Linux.", "risk": "read-only"},
    {"platform": "Linux", "category": "Routing", "command": "ip route", "purpose": "Afficher la table de routage Linux.", "risk": "read-only"},
    {"platform": "Linux", "category": "Diagnostics", "command": "ping -c 4 <ip>", "purpose": "Mesurer la joignabilité et la latence.", "risk": "read-only"},
    {"platform": "Linux", "category": "Performance", "command": "ss -tulpn", "purpose": "Lister les ports et sockets à l'écoute.", "risk": "read-only"},
    {"platform": "GNS3 API", "category": "Projects", "command": "GET /v2/projects", "purpose": "Lister les projets disponibles.", "risk": "read-only"},
    {"platform": "GNS3 API", "category": "Projects", "command": "GET /v2/projects/{project_id}/nodes", "purpose": "Lister les nœuds d'un projet.", "risk": "read-only"},
    {"platform": "GNS3 API", "category": "Projects", "command": "POST /v2/projects/{project_id}/open", "purpose": "Démarrer un projet GNS3.", "risk": "state-changing"},
    {"platform": "GNS3 API", "category": "Projects", "command": "POST /v2/projects/{project_id}/close", "purpose": "Arrêter un projet GNS3.", "risk": "state-changing"},
]


# ---------- Mapping GNS3 → schéma interne ----------

def _infer_device_type(node_type: str, name: str) -> str:
    name_lower = name.lower()
    if "fw" in name_lower or "firewall" in name_lower or "pfsense" in name_lower:
        return "firewall"
    if node_type in ("dynamips", "iou"):
        return "router"
    if node_type == "ethernet_switch":
        return "switch"
    if node_type in ("cloud", "nat"):
        return "cloud"
    if node_type in ("docker", "qemu"):
        return "server"
    return "other"


def _infer_status(gns3_status: str) -> str:
    return {"started": "online", "stopped": "offline"}.get(gns3_status, "unknown")


def _match_site_or_backbone(name: str, sites: list[Site], backbones: list[Backbone]):
    """Retourne (site_id, backbone_id) selon un match trouvé dans le nom du nœud GNS3."""
    normalized = _normalize_name(name)

    for backbone in backbones:
        key = _normalize_name(backbone.name)
        if key and key in normalized:
            return None, backbone.id

    for site in sites:
        key = _normalize_name(site.name)
        if key and key in normalized:
            return site.id, None

    return None, None  # aucun match — sera signalé comme avertissement


def _coerce_port_name(port: dict) -> str:
    return str(port.get("name") or port.get("short_name") or "unknown")


# ---------- Import principal ----------

def import_project_topology(db: Session, project_id: str) -> dict:
    try:
        projects = get_projects()
        project_info = next((p for p in projects if p.get("project_id") == project_id), None)
        if not project_info:
            raise GNS3ServiceError(f"Projet {project_id} introuvable sur GNS3")

        gns3_project = db.query(GNS3Project).filter(GNS3Project.project_id == project_id).first()
        if not gns3_project:
            gns3_project = GNS3Project(project_id=project_id, name=project_info.get("name", project_id))
            db.add(gns3_project)
        gns3_project.name = project_info.get("name", gns3_project.name)
        gns3_project.status = project_info.get("status")
        gns3_project.path = project_info.get("path")

        sites = db.query(Site).all()
        backbones = db.query(Backbone).all()

        nodes = get_project_nodes(project_id)
        links = get_project_links(project_id)

        devices_created, devices_updated, unmatched_site = 0, 0, []
        node_id_to_device: dict[str, Device] = {}

        for node in nodes:
            gns3_node_id = node.get("node_id")
            if not gns3_node_id:
                continue

            name = node.get("name") or "unnamed"
            node_type = node.get("node_type", "other")
            console_host = node.get("console_host")
            console_port = node.get("console")

            device = db.query(Device).filter(Device.gns3_node_id == gns3_node_id).first()
            is_new = device is None
            if is_new:
                device = Device(gns3_node_id=gns3_node_id)
                db.add(device)

            site_id, backbone_id = _match_site_or_backbone(name, sites, backbones)
            if site_id is None and backbone_id is None:
                unmatched_site.append(name)

            device.name = name
            device.device_type = _infer_device_type(node_type, name)
            device.status = _infer_status(node.get("status", "unknown"))
            device.gns3_project_id = project_id
            device.site_id = site_id
            device.backbone_id = backbone_id
            device.console_host = console_host
            device.console_port = console_port

            db.flush()

            ports = node.get("ports") or []
            if not isinstance(ports, list):
                ports = []

            for port in ports:
                if not isinstance(port, dict):
                    continue
                iface_name = _coerce_port_name(port)
                interface = (
                    db.query(Interface)
                    .filter(Interface.device_id == device.id, Interface.name == iface_name)
                    .first()
                )
                if not interface:
                    interface = Interface(device_id=device.id, name=iface_name)
                    db.add(interface)

            node_id_to_device[gns3_node_id] = device

            if is_new:
                devices_created += 1
            else:
                devices_updated += 1

        db.flush()

        links_created, links_updated = 0, 0
        seen_link_ids: set[str] = set()
        for link in links:
            gns3_link_id = link.get("link_id")
            if not gns3_link_id:
                continue
            if gns3_link_id in seen_link_ids:
                continue
            seen_link_ids.add(gns3_link_id)

            endpoints = link.get("nodes") or []
            if len(endpoints) != 2:
                continue

            n1, n2 = endpoints
            if not isinstance(n1, dict) or not isinstance(n2, dict):
                continue

            device1 = node_id_to_device.get(n1.get("node_id"))
            device2 = node_id_to_device.get(n2.get("node_id"))
            if not device1 or not device2:
                continue

            iface1 = ((n1.get("label") or {}).get("text") or "unknown")
            iface2 = ((n2.get("label") or {}).get("text") or "unknown")

            topo_link = db.query(TopologyLink).filter(TopologyLink.gns3_link_id == gns3_link_id).first()
            is_new = topo_link is None
            if is_new:
                topo_link = TopologyLink(gns3_link_id=gns3_link_id)
                db.add(topo_link)

            topo_link.source_device_id = device1.id
            topo_link.destination_device_id = device2.id
            topo_link.source_interface = iface1
            topo_link.destination_interface = iface2
            topo_link.status = "unknown"

            if is_new:
                links_created += 1
            else:
                links_updated += 1

        db.commit()

        unique_unmatched = []
        seen_names: set[str] = set()
        for name in unmatched_site:
            key = _normalize_name(name)
            if key and key not in seen_names:
                seen_names.add(key)
                unique_unmatched.append(name)

        return {
            "project": project_info.get("name", project_id),
            "devices_created": devices_created,
            "devices_updated": devices_updated,
            "links_created": links_created,
            "links_updated": links_updated,
            "unmatched_site_warning": unique_unmatched,
        }
    except Exception:
        db.rollback()
        raise
