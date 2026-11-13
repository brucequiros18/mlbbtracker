from __future__ import annotations


def test_list_heroes_merges_providers(client):
    resp = client.get("/api/v1/heroes")
    assert resp.status_code == 200
    body = resp.json()
    names = [h["name"] for h in body["data"]]
    assert "Khufra" in names
    khufra = next(h for h in body["data"] if h["name"] == "Khufra")
    # identity from Rone, roles from MLBBDex, tier from MLBBDex rankings
    assert khufra["id"] == 78
    assert khufra["slug"] == "khufra"
    assert khufra["roles"] == ["Tank"]
    assert khufra["tier"] == "A+"
    assert body["meta"]["count"] == len(body["data"])
    assert {s["name"] for s in body["meta"]["sources"]} == {"Rone Arena API", "MLBBDex"}


def test_list_heroes_role_filter(client):
    resp = client.get("/api/v1/heroes", params={"role": "Tank"})
    assert resp.status_code == 200
    assert [h["name"] for h in resp.json()["data"]] == ["Khufra"]


def test_rankings_sorted_by_win_rate(client):
    resp = client.get("/api/v1/heroes/rankings", params={"days": 7, "sort": "win_rate"})
    assert resp.status_code == 200
    rows = resp.json()["data"]
    assert rows[0]["name"] == "Masha"
    assert rows[0]["win_rate"] > rows[1]["win_rate"]
    assert rows[1]["id"] == 78


def test_hero_trends_sorted_ascending(client):
    resp = client.get("/api/v1/heroes/khufra/trends", params={"days": 7})
    assert resp.status_code == 200
    body = resp.json()
    dates = [p["date"] for p in body["data"]]
    assert dates == sorted(dates)
    assert body["meta"]["count"] == 2
    assert body["data"][0]["win_rate"] < body["data"][1]["win_rate"]


def test_hero_trends_not_found(client):
    resp = client.get("/api/v1/heroes/does-not-exist/trends")
    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"


def test_hero_detail_by_slug(client):
    resp = client.get("/api/v1/heroes/khufra")
    assert resp.status_code == 200
    hero = resp.json()["data"]
    assert hero["id"] == 78
    assert hero["skills"][0]["name"] == "Spell Curse"
    assert hero["rank_stat"]["win_rate"] > 0
    # relations resolved from Rone ids to names
    assert "Balmond" in hero["strong_against"]
    assert "Ruby" in hero["weak_against"]


def test_hero_detail_by_numeric_id(client):
    resp = client.get("/api/v1/heroes/88")
    assert resp.status_code == 200
    assert resp.json()["data"]["slug"] == "masha"


def test_hero_detail_not_found_returns_envelope(client):
    resp = client.get("/api/v1/heroes/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "error"
    assert body["code"] == "NOT_FOUND"
