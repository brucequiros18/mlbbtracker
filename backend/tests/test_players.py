from __future__ import annotations


def test_player_lookup_is_unsupported(client):
    resp = client.get("/api/v1/players/123456789/1234")
    assert resp.status_code == 501
    body = resp.json()
    assert body["code"] == "NOT_SUPPORTED"
    assert "details" in body


def test_player_lookup_validates_digits(client):
    resp = client.get("/api/v1/players/abc/1234")
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
