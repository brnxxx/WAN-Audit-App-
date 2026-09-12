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