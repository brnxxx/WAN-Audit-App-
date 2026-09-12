from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Backbone, Admin
from app.schemas import BackboneCreate, BackboneOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/backbone", tags=["backbone"])


@router.get("", response_model=list[BackboneOut])
def list_backbones(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    return db.query(Backbone).order_by(Backbone.name).all()


@router.get("/{backbone_id}", response_model=BackboneOut)
def get_backbone(backbone_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    backbone = db.get(Backbone, backbone_id)
    if not backbone:
        raise HTTPException(status_code=404, detail="Backbone introuvable")
    return backbone


@router.post("", response_model=BackboneOut, status_code=201)
def create_backbone(payload: BackboneCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    if db.query(Backbone).filter(Backbone.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Un backbone avec ce nom existe déjà")
    backbone = Backbone(**payload.model_dump())
    db.add(backbone)
    db.commit()
    db.refresh(backbone)
    return backbone


@router.put("/{backbone_id}", response_model=BackboneOut)
def update_backbone(backbone_id: int, payload: BackboneCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    backbone = db.get(Backbone, backbone_id)
    if not backbone:
        raise HTTPException(status_code=404, detail="Backbone introuvable")
    for key, value in payload.model_dump().items():
        setattr(backbone, key, value)
    db.commit()
    db.refresh(backbone)
    return backbone


@router.delete("/{backbone_id}", status_code=204)
def delete_backbone(backbone_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    backbone = db.get(Backbone, backbone_id)
    if not backbone:
        raise HTTPException(status_code=404, detail="Backbone introuvable")
    db.delete(backbone)
    db.commit()