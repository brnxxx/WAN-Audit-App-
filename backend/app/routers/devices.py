from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Device, Admin, Site, Backbone
from app.schemas import DeviceOut, DeviceCreate, DeviceUpdate
from app.routers.auth import get_current_admin
from app.services import netmiko_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut])
def list_devices(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    return (
        db.query(Device)
        .options(joinedload(Device.site), joinedload(Device.backbone))
        .order_by(Device.name)
        .all()
    )


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    device = (
        db.query(Device)
        .options(joinedload(Device.site), joinedload(Device.backbone))
        .filter(Device.id == device_id)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device introuvable")
    return device


@router.post("", response_model=DeviceOut, status_code=201)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    if payload.site_id is not None and not db.get(Site, payload.site_id):
        raise HTTPException(status_code=404, detail="Site introuvable")
    if payload.backbone_id is not None and not db.get(Backbone, payload.backbone_id):
        raise HTTPException(status_code=404, detail="Backbone introuvable")
    device = Device(**payload.model_dump())
    db.add(device)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Impossible de créer cet équipement") from exc
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, payload: DeviceUpdate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device introuvable")
    if payload.site_id is not None and payload.backbone_id is None and not db.get(Site, payload.site_id):
        raise HTTPException(status_code=404, detail="Site introuvable")
    if payload.backbone_id is not None and payload.site_id is None and not db.get(Backbone, payload.backbone_id):
        raise HTTPException(status_code=404, detail="Backbone introuvable")
    for key, value in payload.model_dump().items():
        setattr(device, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Impossible de modifier cet équipement") from exc
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device introuvable")
    db.delete(device)
    db.commit()


@router.post("/{device_id}/sync-ip")
def sync_device_ip(device_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    try:
        return netmiko_service.sync_device_ips(db, device_id)
    except netmiko_service.CiscoServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))