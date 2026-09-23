import httpx
from sqlalchemy.orm import Session

from app.config import GNS3_URL
from app.models import Device, Interface, TopologyLink, Site, Backbone, GNS3Project


class GNS3ServiceError(Exception):
    """Levée quand la communication avec GNS3 échoue."""
    pass


def _get(endpoint: str) -> list[dict] | dict:
    url = f"{GNS3_URL}{endpoint}"
    try:
        response = httpx.get(url, timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError as exc:
        raise GNS3ServiceError(f"Impossible de contacter GNS3 : {exc}")
    except httpx.HTTPStatusError as exc:
        raise GNS3ServiceError(f"GNS3 a renvoyé une erreur : {exc.response.status_code}")


def get_projects() -> list[dict]:
    return _get("/v2/projects")


def get_project_nodes(project_id: str) -> list[dict]:
    return _get(f"/v2/projects/{project_id}/nodes")


def get_project_links(project_id: str) -> list[dict]:
    return _get(f"/v2/projects/{project_id}/links")


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
    normalized = name.upper().replace(" ", "").replace("-", "").replace("_", "")

    for backbone in backbones:
        key = backbone.name.upper().replace(" ", "")
        if key in normalized:
            return None, backbone.id

    for site in sites:
        key = site.name.upper().replace(" ", "")
        if key in normalized:
            return site.id, None

    return None, None  # aucun match — sera signalé comme avertissement


# ---------- Import principal ----------

def import_project_topology(db: Session, project_id: str) -> dict:
    projects = get_projects()
    project_info = next((p for p in projects if p["project_id"] == project_id), None)
    if not project_info:
        raise GNS3ServiceError(f"Projet {project_id} introuvable sur GNS3")

    # upsert du projet
    gns3_project = db.query(GNS3Project).filter(GNS3Project.project_id == project_id).first()
    if not gns3_project:
        gns3_project = GNS3Project(project_id=project_id, name=project_info["name"])
        db.add(gns3_project)
    gns3_project.status = project_info.get("status")
    gns3_project.path = project_info.get("path")

    sites = db.query(Site).all()
    backbones = db.query(Backbone).all()

    nodes = get_project_nodes(project_id)
    links = get_project_links(project_id)

    devices_created, devices_updated, unmatched_site = 0, 0, []
    node_id_to_device: dict[str, Device] = {}

    for node in nodes:
        gns3_node_id = node["node_id"]
        name = node["name"]
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

        db.flush()  # pour obtenir device.id même si nouveau

        # Interfaces (ports)
        for port in node.get("ports", []):
            iface_name = port.get("name") or port.get("short_name") or "unknown"
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

    # Liens
    links_created, links_updated = 0, 0
    for link in links:
        gns3_link_id = link["link_id"]
        endpoints = link.get("nodes", [])
        if len(endpoints) != 2:
            continue  # lien incomplet ou multi-point, ignoré pour l'instant

        n1, n2 = endpoints
        device1 = node_id_to_device.get(n1["node_id"])
        device2 = node_id_to_device.get(n2["node_id"])
        if not device1 or not device2:
            continue

        iface1 = (n1.get("label") or {}).get("text", "unknown")
        iface2 = (n2.get("label") or {}).get("text", "unknown")

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

    return {
        "project": project_info["name"],
        "devices_created": devices_created,
        "devices_updated": devices_updated,
        "links_created": links_created,
        "links_updated": links_updated,
        "unmatched_site_warning": unmatched_site,
    }