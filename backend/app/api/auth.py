import time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_token
from app.services.audit import record

router = APIRouter(prefix="/auth", tags=["auth"])
_failures: dict[str, list[float]] = {}


def browser_name(user_agent: str) -> str:
    if "Edg/" in user_agent:
        return "Edge"
    if "Firefox/" in user_agent:
        return "Firefox"
    if "Chrome/" in user_agent or "CriOS/" in user_agent:
        return "Chrome"
    if "Safari/" in user_agent:
        return "Safari"
    return "Other"


@router.post("/login", response_model=TokenResponse, summary="Sign in")
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    now = time.time()
    recent = [stamp for stamp in _failures.get(req.username, []) if now - stamp < 60]
    if len(recent) >= 8:
        raise HTTPException(status_code=429, detail="Too many login attempts. Wait a minute and try again.")
    user = db.query(User).filter(User.username == req.username, User.is_active.is_(True)).first()
    if not user or not verify_password(req.password, user.password_hash):
        recent.append(now)
        _failures[req.username] = recent
        raise HTTPException(status_code=401, detail="Invalid username or password")
    _failures.pop(req.username, None)
    agent = (request.headers.get("user-agent") or "")[:180]
    record(db, "access", "session", user.id, user, {
        "username": user.username,
        "role": user.role,
        "browser": browser_name(agent),
        "user_agent": agent,
        "ip": request.client.host if request.client else "",
    })
    db.commit()
    return TokenResponse(access_token=create_token(user))
