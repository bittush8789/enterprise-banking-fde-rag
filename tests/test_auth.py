import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from seed_data import seed_database

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    seed_database()

def test_login_success():
    response = client.post("/api/auth/login", json={
        "email": "admin@bankassist.ai",
        "password": "Admin@123456"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@bankassist.ai"

def test_login_invalid_password():
    response = client.post("/api/auth/login", json={
        "email": "admin@bankassist.ai",
        "password": "WrongPassword!999"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["message"]

def test_get_current_user():
    # Login first
    login_res = client.post("/api/auth/login", json={
        "email": "loan.officer@bankassist.ai",
        "password": "Loan@123456"
    })
    token = login_res.json()["access_token"]

    # Call /api/auth/me
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["email"] == "loan.officer@bankassist.ai"
    role_names = [r["name"] for r in user_data["roles"]]
    assert "LOAN_OFFICER" in role_names

def test_invalid_jwt_token():
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_garbage_token"})
    assert res.status_code == 401
