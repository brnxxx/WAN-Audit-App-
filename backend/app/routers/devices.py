from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Device, Admin
from app.schemas import DeviceOut, DeviceCreate
from app.routers.auth import get_current_admin

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
    device = Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.put("/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, payload: DeviceCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device introuvable")
    for key, value in payload.model_dump().items():
        setattr(device, key, value)
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device introuvable")
    db.delete(device)
    db.commit()