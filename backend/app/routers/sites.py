from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Site, Admin
from app.schemas import SiteCreate, SiteOut
from app.routers.auth import get_current_admin

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    return db.query(Site).order_by(Site.name).all()


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site introuvable")
    return site


@router.post("", response_model=SiteOut, status_code=201)
def create_site(payload: SiteCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    if db.query(Site).filter(Site.name == payload.name).first():
        raise HTTPException(status_code=409, detail="Un site avec ce nom existe déjà")
    site = Site(**payload.model_dump())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.put("/{site_id}", response_model=SiteOut)
def update_site(site_id: int, payload: SiteCreate, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site introuvable")
    for key, value in payload.model_dump().items():
        setattr(site, key, value)
    db.commit()
    db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
def delete_site(site_id: int, db: Session = Depends(get_db), current_admin: Admin = Depends(get_current_admin)):
    site = db.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site introuvable")
    db.delete(site)
    db.commit()