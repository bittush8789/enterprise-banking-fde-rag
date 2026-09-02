import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app

client = TestClient(app)

def get_token_for(email: str, password: str) -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json()["access_token"]

def test_universal_access_to_user_management():
    loan_token = get_token_for("loan.officer@bankassist.ai", "Loan@123456")
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {loan_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 4

def test_universal_access_to_audit_logs():
    support_token = get_token_for("support@bankassist.ai", "Support@123456")
    res = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {support_token}"})
    assert res.status_code == 200

def test_universal_access_to_document_list():
    support_token = get_token_for("support@bankassist.ai", "Support@123456")
    res = client.get("/api/documents", headers={"Authorization": f"Bearer {support_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 4
