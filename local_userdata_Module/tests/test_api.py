import importlib

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("BOLDMAKER_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("BOLDMAKER_SERVE_FRONTEND", "false")
    import config

    importlib.reload(config)
    import storage

    importlib.reload(storage)
    import main

    importlib.reload(main)
    from fastapi.testclient import TestClient

    return TestClient(main.app)


def login(client, account="test", password="test"):
    response = client.post("/api/auth/login", json={"account": account, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_test_login_and_resource_crud_isolated(client, monkeypatch):
    token_a = login(client)
    import main

    def cloud_profile(url, headers, timeout):
        assert url.endswith("/me")
        assert headers["Authorization"] == "Bearer cloud-token"
        return main.httpx.Response(200, json={"user_id": 2, "username": "user-b", "email": "user-b@example.com"})

    monkeypatch.setattr(main.httpx, "get", cloud_profile)
    cloud_login = client.post("/api/auth/cloud-login", headers={"Authorization": "Bearer cloud-token"})
    assert cloud_login.status_code == 200
    assert cloud_login.json()["uid"] == "2"
    token_b = cloud_login.json()["access_token"]

    uploaded = client.post(
        "/api/resources?kind=image&description=portrait",
        headers=headers(token_a),
        files={"file": ("portrait.jpg", b"image-data", "image/jpeg")},
    )
    assert uploaded.status_code == 201
    resource_id = uploaded.json()["id"]
    assert client.get("/api/resources", headers=headers(token_a)).json()["items"][0]["id"] == resource_id
    assert client.get(f"/api/resources/{resource_id}", headers=headers(token_b)).status_code == 404
    assert client.get(f"/api/resources/{resource_id}/content", headers=headers(token_b)).status_code == 404

    updated = client.put(f"/api/resources/{resource_id}", headers=headers(token_a), json={"description": "updated"})
    assert updated.status_code == 200
    assert updated.json()["description"] == "updated"
    assert client.get(f"/api/resources/{resource_id}/content", headers=headers(token_a)).content == b"image-data"
    second = client.post(
        "/api/resources?kind=image",
        headers=headers(token_a),
        files={"file": ("other.jpg", b"other-data", "image/jpeg")},
    )
    assert second.status_code == 201
    conflict = client.put(f"/api/resources/{resource_id}", headers=headers(token_a), json={"original_name": "other.jpg"})
    assert conflict.status_code == 409
    assert client.get(f"/api/resources/{resource_id}", headers=headers(token_a)).json()["original_name"] == "portrait.jpg"
    assert client.put(f"/api/resources/{resource_id}", headers=headers(token_a), json={"original_name": "renamed.jpg"}).status_code == 200
    assert client.delete(f"/api/resources/{resource_id}", headers=headers(token_a)).status_code == 204
    assert client.get(f"/api/resources/{resource_id}", headers=headers(token_a)).status_code == 404


def test_skill_crud_and_unauthorized_access(client):
    token = login(client)
    no_auth = client.get("/api/skills")
    assert no_auth.status_code == 401

    created = client.post(
        "/api/skills?name=Portrait%20Skill&description=demo",
        headers=headers(token),
        files={"file": ("skill.yaml", b"name: portrait", "text/yaml")},
    )
    assert created.status_code == 201
    skill_id = created.json()["id"]
    assert client.get("/api/skills", headers=headers(token)).json()["items"][0]["name"] == "Portrait Skill"
    assert client.put(f"/api/skills/{skill_id}", headers=headers(token), json={"is_public": True}).json()["is_public"] is True
    assert client.get(f"/api/skills/{skill_id}/content", headers=headers(token)).content == b"name: portrait"
    assert client.delete(f"/api/skills/{skill_id}", headers=headers(token)).status_code == 204
