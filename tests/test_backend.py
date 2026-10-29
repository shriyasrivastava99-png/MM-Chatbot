from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import init_db

client = TestClient(app)


def setup_module():
    init_db()


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["database"]["connected"] is True


def test_conversations():
    # 1. Create conversation
    res = client.post("/api/conversations", json={"title": "Test Thread"})
    assert res.status_code == 200
    conv = res.json()
    assert conv["title"] == "Test Thread"
    conv_id = conv["id"]

    # 2. Get conversations list
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    assert any(c["id"] == conv_id for c in list_res.json())

    # 3. Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200


def test_chat_endpoint():
    res = client.post(
        "/api/chat",
        json={
            "message": "Hello from automated test!",
            "modality": "text",
            "enable_web_search": False,
            "enable_rag": False,
            "is_emotional_mode": False
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert "response_text" in data
    assert len(data["response_text"]) > 0


def test_search_endpoint():
    res = client.post(
        "/api/search",
        json={
            "query": "artificial intelligence",
            "max_results": 2
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "results" in data


def test_document_generate():
    res = client.post(
        "/api/documents/generate",
        json={
            "title": "UnitTestDoc",
            "content": "This is sample generated document text.",
            "file_format": "txt"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert "filename" in data
    assert data["filename"].endswith(".txt")

