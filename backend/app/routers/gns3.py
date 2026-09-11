from fastapi import APIRouter, Depends, HTTPException
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