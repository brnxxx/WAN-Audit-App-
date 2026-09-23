from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interface, Admin, Device
from app.schemas import InterfaceCreate, InterfaceOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/interfaces", tags=["interfaces"])


@router.get("", response_model=list[InterfaceOut])
def list_interfaces(
    device_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    query = db.query(Interface)
    if device_id is not None:
        query = query.filter(Interface.device_id == device_id)
    return query.order_by(Interface.name).all()


@router.get("/{interface_id}", response_model=InterfaceOut)
def get_interface(interface_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    interface = db.get(Interface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface introuvable")
    return interface


@router.post("", response_model=InterfaceOut, status_code=201)
def create_interface(payload: InterfaceCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    if not db.get(Device, payload.device_id):
        raise HTTPException(status_code=404, detail="Device introuvable")
    if db.query(Interface).filter(Interface.device_id == payload.device_id, Interface.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Cette interface existe déjà pour cet équipement")
    interface = Interface(**payload.model_dump())
    db.add(interface)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Impossible de créer cette interface") from exc
    db.refresh(interface)
    return interface


@router.put("/{interface_id}", response_model=InterfaceOut)
def update_interface(interface_id: int, payload: InterfaceCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    interface = db.get(Interface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface introuvable")
    duplicate = db.query(Interface).filter(
        Interface.device_id == payload.device_id,
        Interface.name == payload.name,
        Interface.id != interface_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Cette interface existe déjà pour cet équipement")
    for key, value in payload.model_dump().items():
        setattr(interface, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Impossible de modifier cette interface") from exc
    db.refresh(interface)
    return interface


@router.delete("/{interface_id}", status_code=204)
def delete_interface(interface_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    interface = db.get(Interface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface introuvable")
    db.delete(interface)
    db.commit()