from __future__ import annotations


def test_health_reports_capabilities(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["capabilities"]["hero_catalog"] is True
    assert body["capabilities"]["hero_detail"] is True
    assert body["capabilities"]["player_lookup"] is False
    assert body["providers"]["player"] == "unavailable"


def test_index_metadata(client):
    resp = client.get("/api/meta")
    assert resp.status_code == 200
    assert resp.json()["api"] == "/api/v1"


def test_root_serves_app_or_index(client):
    """`/` is the web app when a build exists, otherwise the JSON index."""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert ("<!DOCTYPE html" in body) or ('"api"' in body)
