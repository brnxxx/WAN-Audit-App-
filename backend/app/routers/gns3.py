from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import gns3_service
from app.routers.auth import get_current_admin
from app.models import Admin

router = APIRouter(prefix="/gns3", tags=["gns3"])


@router.get("/projects")
def list_projects(current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_projects()
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}/nodes")
def list_nodes(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project_nodes(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}/links")
def list_links(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project_links(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}")
def get_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/start")
def start_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.start_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/stop")
def stop_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.stop_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/nodes/{node_id}/{action}")
def control_node(project_id: str, node_id: str, action: str, current_admin: Admin = Depends(get_current_admin)):
    actions = {
        "start": gns3_service.start_node,
        "stop": gns3_service.stop_node,
        "reload": gns3_service.reload_node,
    }
    if action not in actions:
        raise HTTPException(status_code=400, detail="Action nœud invalide")
    try:
        return actions[action](project_id, node_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/commands")
def command_guide(current_admin: Admin = Depends(get_current_admin)):
    return gns3_service.COMMAND_GUIDE


@router.post("/diagnostics/ping")
def diagnostic_ping(payload: dict, current_admin: Admin = Depends(get_current_admin)):
    target = payload.get("target")
    count = payload.get("count", 4)
    if not isinstance(target, str) or not isinstance(count, int):
        raise HTTPException(status_code=422, detail="target et count sont invalides")
    try:
        return gns3_service.ping_host(target, count)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/projects/{project_id}/import")
def import_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    try:
        return gns3_service.import_project_topology(db, project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))