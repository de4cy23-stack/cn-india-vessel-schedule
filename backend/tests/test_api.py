from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_web_ui_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "中印船期查询" in response.text


def test_ports_endpoint():
    response = client.get("/ports")
    assert response.status_code == 200
    codes = {item["code"] for item in response.json()}
    assert {"CNNGB", "CNSHA", "INNSA", "INMUN"} <= codes


def test_search_resolves_aliases_without_enabled_carriers():
    response = client.get(
        "/search",
        params={
            "origin": "宁波",
            "destination": "JNPT",
            "date_from": "2026-09-20",
            "weeks": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["origin"] == "CNNGB"
    assert body["destination"] == "INNSA"
    assert body["results"] == []


def test_unknown_port_returns_400():
    response = client.get(
        "/search",
        params={
            "origin": "UNKNOWN PORT",
            "destination": "INNSA",
            "date_from": "2026-09-20",
        },
    )
    assert response.status_code == 400
