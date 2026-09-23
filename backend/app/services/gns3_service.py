import re
import ipaddress
import platform
import subprocess

import httpx
from sqlalchemy.orm import Session

from app.config import GNS3_URL
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
        raise GNS3ServiceError(f"GNS3 a renvoyé une erreur : {exc.response.status_code}")


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
        raise GNS3ServiceError(f"GNS3 a renvoyé une erreur : {exc.response.status_code}")


def get_project(project_id: str) -> dict:
    data = _get(f"/v2/projects/{project_id}")
    return data if isinstance(data, dict) else {}


def start_project(project_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/open")


def stop_project(project_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/close")


def start_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/start")


def stop_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/stop")


def reload_node(project_id: str, node_id: str) -> dict:
    return _action(f"/v2/projects/{project_id}/nodes/{node_id}/reload")


def ping_host(target: str, count: int = 4) -> dict:
    try:
        ipaddress.ip_address(target)
    except ValueError as exc:
        raise GNS3ServiceError("La cible doit être une adresse IP valide") from exc
    count = max(1, min(count, 5))
    command = ["ping", "-n" if platform.system() == "Windows" else "-c", str(count), target]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
    except subprocess.TimeoutExpired as exc:
        raise GNS3ServiceError("Le ping a dépassé le délai maximal") from exc
    return {
        "target": target,
        "reachable": result.returncode == 0,
        "return_code": result.returncode,
        "output": result.stdout[-4000:] or result.stderr[-4000:],
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
