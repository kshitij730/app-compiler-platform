from fastapi.testclient import TestClient

from src.main import app


def test_compile_endpoint_returns_executable_result():
    client = TestClient(app)
    response = client.post("/compile", json={"prompt": "Build an ecommerce app with products, orders, payments, dashboard and admin analytics."})

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime"]["executable"] is True
    assert payload["validation_after_repair"]["ok"] is True
    assert "compiled_config" in payload
