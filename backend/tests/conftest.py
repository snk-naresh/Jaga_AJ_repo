import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-anand"
os.environ["S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["S3_ACCESS_KEY"] = "test"
os.environ["S3_SECRET_KEY"] = "test"
os.environ["S3_BUCKET"] = "anand-jewellers"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["WHATSAPP_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch):
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    import app.models  # noqa: F401
    from app.core.security import hash_password
    from app.models.user import User
    from app.tasks.celery_app import send_whatsapp_task

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(User(username="admin", password_hash=hash_password("ChangeMe_123!"), role="ADMIN"))
    db.add(User(username="staff", password_hash=hash_password("Iamstaff@1"), role="STAFF"))
    db.commit()
    db.close()
    monkeypatch.setattr("app.services.notify.send_whatsapp_task.delay", lambda nid: send_whatsapp_task(nid))
    monkeypatch.setattr("app.api.notifications.send_whatsapp_task.delay", lambda nid: send_whatsapp_task(nid))
    from app.main import app
    return TestClient(app)


@pytest.fixture()
def token(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "ChangeMe_123!"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def auth(token):
    return {"Authorization": f"Bearer {token}"}
