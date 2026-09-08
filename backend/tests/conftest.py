import os

os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FRONTEND_URL"] = "http://localhost:8000"
os.environ["RESEND_API_KEY"] = ""
os.environ["WOMPI_PUBLIC_KEY"] = "pub_test_1234"
os.environ["WOMPI_INTEGRITY_SECRET"] = "test_integrity_secret"
os.environ["WOMPI_EVENTS_SECRET"] = "test_events_secret"
os.environ["MERCADOPAGO_ACCESS_TOKEN"] = "TEST-token"
os.environ["MERCADOPAGO_WEBHOOK_SECRET"] = "test_mp_secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from middleware.auth import hash_password
from models.user import User

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.create_all(bind=engine)
    app.state.limiter.reset()
    yield
    Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@jgparfums.com",
        password_hash=hash_password("supersecret123"),
        full_name="Admin JG",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post("/auth/login", json={"email": admin_user.email, "password": "supersecret123"})
    return response.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
