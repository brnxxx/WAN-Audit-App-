from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Interface, Admin
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
    interface = Interface(**payload.model_dump())
    db.add(interface)
    db.commit()
    db.refresh(interface)
    return interface


@router.put("/{interface_id}", response_model=InterfaceOut)
def update_interface(interface_id: int, payload: InterfaceCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    interface = db.get(Interface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface introuvable")
    for key, value in payload.model_dump().items():
        setattr(interface, key, value)
    db.commit()
    db.refresh(interface)
    return interface


@router.delete("/{interface_id}", status_code=204)
def delete_interface(interface_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    interface = db.get(Interface, interface_id)
    if not interface:
        raise HTTPException(status_code=404, detail="Interface introuvable")
    db.delete(interface)
    db.commit()