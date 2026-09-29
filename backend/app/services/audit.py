def record(db, event_type: str, entity: str, entity_id, user=None, details: dict | None = None) -> None:
    from app.models.audit import AuditLog
    safe = None
    if details:
        safe = {key: value for key, value in details.items() if key.lower() not in {"password", "token", "access_token", "secret", "api_key"}}
    db.add(AuditLog(
        event_type=event_type,
        entity=entity,
        entity_id=str(entity_id),
        user_id=getattr(user, "id", None),
        details=safe,
    ))
