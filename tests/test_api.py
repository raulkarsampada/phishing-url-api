from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAFE = "https://www.google.com"
BAD = "http://192.168.4.7/secure-login/verify-account.php?id=1"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_response_schema():
    r = client.post("/check-url", json={"url": SAFE})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"url", "risk_score", "verdict", "red_flags"}
    assert 0 <= body["risk_score"] <= 1


def test_bad_url_scores_higher_than_safe_url():
    safe = client.post("/check-url", json={"url": SAFE}).json()
    bad = client.post("/check-url", json={"url": BAD}).json()
    assert bad["risk_score"] > safe["risk_score"]
    assert bad["risk_score"] >= 0.5
    assert len(bad["red_flags"]) > 0


def test_empty_url_rejected():
    assert client.post("/check-url", json={"url": ""}).status_code == 422


def test_url_with_spaces_rejected():
    assert client.post("/check-url", json={"url": "not a url"}).status_code == 422


def test_missing_field_rejected():
    assert client.post("/check-url", json={}).status_code == 422


def test_model_info():
    r = client.get("/model-info")
    assert r.status_code == 200
    assert "precision" in r.json()