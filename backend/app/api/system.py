from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import current_user, require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(tags=["system"])


@router.get("/auth/me", summary="Signed-in staff profile")
def me(user=Depends(current_user)):
    return {"id": user.id, "username": user.username, "role": user.role}


@router.get("/system/status", summary="Non-secret runtime status")
def status(user=Depends(current_user)):
    return {
        "app": "Anand Jewellers",
        "role": user.role,
        "whatsapp_mode": "live" if settings.WHATSAPP_ENABLED else "development",
        "storage_configured": bool(settings.S3_BUCKET and settings.S3_ENDPOINT_URL),
    }


@router.get("/audit", summary="Audit trail")
def audit(limit: int = 50, db: Session = Depends(get_db), _=Depends(current_user)):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 200)).all()
    users = {user.id: user.username for user in db.query(User).all()}
    return [{
        "id": row.id,
        "event_type": row.event_type,
        "entity": row.entity,
        "entity_id": row.entity_id,
        "user": users.get(row.user_id),
        "details": row.details,
        "created_at": row.created_at,
    } for row in rows]


@router.get("/access", summary="Security access records")
def access(limit: int = 50, db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    cap = min(limit, 200)
    users = {user.id: user.username for user in db.query(User).all()}
    sign_ins = db.query(AuditLog).filter(AuditLog.event_type == "access").order_by(AuditLog.id.desc()).limit(cap).all()
    edits = db.query(AuditLog).filter(AuditLog.event_type == "phone_corrected").order_by(AuditLog.id.desc()).limit(cap).all()
    return {
        "sign_ins": [{
            "id": row.id,
            "username": (row.details or {}).get("username") or users.get(row.user_id),
            "role": (row.details or {}).get("role"),
            "browser": (row.details or {}).get("browser"),
            "ip": (row.details or {}).get("ip"),
            "created_at": row.created_at,
        } for row in sign_ins],
        "edits": [{
            "id": row.id,
            "username": (row.details or {}).get("username") or users.get(row.user_id),
            "role": (row.details or {}).get("role"),
            "customer": (row.details or {}).get("customer"),
            "previous_phone": (row.details or {}).get("previous_phone"),
            "phone": (row.details or {}).get("phone"),
            "created_at": row.created_at,
        } for row in edits],
    }


@router.get("/users", summary="Staff accounts")
def users(_: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)):
    return [{"id": user.id, "username": user.username, "role": user.role, "is_active": user.is_active} for user in db.query(User).order_by(User.id).all()]
