import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.rag.retriever import PermissionAwareRetriever
from backend.app.rag.rag_chain import RAGChain
from seed_data import seed_database

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_data():
    seed_database()

def test_permission_aware_retrieval_allowed():
    # Loan Officer querying Home Loan Policy
    chunks = PermissionAwareRetriever.retrieve(
        query="What is the maximum LTV ratio for home loan?",
        user_roles=["LOAN_OFFICER"],
        top_k=3,
        threshold=0.30
    )
    assert len(chunks) > 0
    doc_names = [c.document_name for c in chunks]
    assert any("Home Loan" in name for name in doc_names)

def test_universal_document_retrieval():
    # Customer Support can now retrieve information across all approved banking documents
    chunks = PermissionAwareRetriever.retrieve(
        query="What is the password rotation policy and lockout duration for CBS?",
        user_roles=["CUSTOMER_SUPPORT"],
        top_k=3,
        threshold=0.15
    )
    assert len(chunks) > 0
    doc_names = [c.document_name for c in chunks]
    assert any("Cybersecurity" in name or "Security" in name for name in doc_names)

def test_rag_chain_execution_with_citations():
    result = RAGChain.execute(
        query="What are the home loan eligibility and CIBIL score requirements?",
        user_roles=["LOAN_OFFICER"]
    )
    assert result["is_grounded"] is True
    assert len(result["sources"]) > 0
    assert result["sources"][0].document_name != ""

def test_rag_irrelevant_query_fallback():
    # Irrelevant query about something outside banking docs (e.g. quantum physics cooking)
    result = RAGChain.execute(
        query="How do you bake a chocolate cake using quantum entanglement?",
        user_roles=["CUSTOMER_SUPPORT"]
    )
    # Threshold will catch this or result in no info fallback
    assert "could not find sufficient information" in result["answer"].lower() or len(result["sources"]) == 0
