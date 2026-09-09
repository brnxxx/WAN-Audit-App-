from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Admin
from app.schemas import LoginRequest, AdminOut
from app.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_admin(request: Request, db: Session = Depends(get_db)) -> Admin:
    """Dependency à réutiliser sur toutes les routes protégées plus tard."""
    admin_id = request.session.get("admin_id")
    if not admin_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié",
        )
    admin = db.get(Admin, admin_id)
    if not admin or not admin.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide",
        )
    return admin


@router.post("/login", response_model=AdminOut)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == payload.username).first()

    # Même message d'erreur que l'utilisateur existe ou non (anti-enumeration)
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    admin.last_login = datetime.utcnow()
    db.commit()

    request.session["admin_id"] = admin.id
    return admin


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"detail": "Déconnecté"}


@router.get("/me", response_model=AdminOut)
def me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin