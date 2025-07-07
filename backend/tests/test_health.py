from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "RAG Chat Application API", "version": "0.1.0"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_health_status():
    response = client.get("/api/v1/health/status")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "rag-chat-api"

def test_readiness_check():
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["database"] is True
    assert response.json()["openai"] is True
    assert response.json()["storage"] is True