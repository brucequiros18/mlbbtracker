from __future__ import annotations


def test_standings_returns_rows(client):
    resp = client.get("/api/v1/esports/id/standings")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["count"] == 2
    top = body["data"][0]
    # camelCase wire format
    assert top["teamCode"] == "TLPH"
    assert top["matchWins"] == 12
    assert top["matchLosses"] == 2
    assert top["netGameWin"] == 19
    assert {s["name"] for s in body["meta"]["sources"]} == {"Rone Arena API"}


def test_standings_sorted_by_rank(client):
    rows = client.get("/api/v1/esports/my/standings").json()["data"]
    ranks = [r["rank"] for r in rows]
    assert ranks == sorted(ranks)


def test_standings_rejects_unknown_league(client):
    resp = client.get("/api/v1/esports/xx/standings")
    assert resp.status_code == 422
    assert resp.json()["code"] == "VALIDATION_ERROR"
