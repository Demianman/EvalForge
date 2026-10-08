import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
import pytest
from fastapi.testclient import TestClient
from app.database import Base, SessionLocal, engine
from app.main import app, pwd
from app.models import User


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    with SessionLocal() as db:
        db.add(User(email="test@example.com", name="Test", password_hash=pwd.hash("password"))); db.commit()
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"email": "test@example.com", "password": "password"})
        yield c
    Base.metadata.drop_all(engine)
