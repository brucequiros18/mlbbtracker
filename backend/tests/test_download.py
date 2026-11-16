"""Tests for the /download landing page and the APK release plumbing.

The page must be honest: a published release renders a real download link and
metadata; an empty releases directory renders "no build published yet" rather
than a broken link.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app

MANIFEST = {
    "version": "0.8.0+8",
    "channel": "preview",
    "file": "mlbb-tracker-0.8.0.apk",
    "size_bytes": 23_500_000,
    "sha256": "a" * 64,
    "released_at": "2026-11-16",
    "min_android": "5.0 (API 21)",
    "signed_with": "debug keys — preview build, not store-signed",
    "notes": ["Recorded history chart", "Download page"],
}


@pytest.fixture
def releases_client(tmp_path, monkeypatch):
    """App wired to a throwaway releases directory."""
    releases = tmp_path / "releases"
    releases.mkdir()
    monkeypatch.setenv("MLBB_RELEASES_DIR", str(releases))
    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as client:
        yield client, releases
    get_settings.cache_clear()


def _publish(releases, manifest: dict, *, payload: bytes = b"fake-apk-bytes") -> None:
    (releases / "latest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (releases / manifest["file"]).write_bytes(payload)


# — The page ————————————————————————————————————————————————————————


def test_download_page_renders_published_release(releases_client):
    client, releases = releases_client
    _publish(releases, MANIFEST)

    resp = client.get("/download")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    assert "Content-Security-Policy" in resp.headers
    body = resp.text
    assert "MLBB Tracker" in body
    assert "v0.8.0+8" in body
    assert f'href="/downloads/{MANIFEST["file"]}"' in body
    assert "Download APK" in body
    assert "22.4 MB" in body  # 23.5e6 bytes
    assert MANIFEST["sha256"] in body  # full hash in the details block
    assert "preview" in body
    assert "Recorded history chart" in body


def test_download_page_is_honest_when_nothing_is_published(releases_client):
    client, _releases = releases_client

    resp = client.get("/download")

    assert resp.status_code == 200
    body = resp.text
    assert "No public APK has been published" in body
    assert "/downloads/" not in body  # no fake download link
    assert 'href="/"' in body  # the web app is still offered


def test_download_page_ignores_a_corrupt_manifest(releases_client):
    client, releases = releases_client
    (releases / "latest.json").write_text("{not json", encoding="utf-8")

    resp = client.get("/download")

    assert resp.status_code == 200
    assert "No public APK has been published" in resp.text


def test_download_page_ignores_manifest_with_unsafe_filename(releases_client):
    client, releases = releases_client
    bad = dict(MANIFEST, file="../../backend/app/main.py")
    (releases / "latest.json").write_text(json.dumps(bad), encoding="utf-8")

    resp = client.get("/download")

    assert "No public APK has been published" in resp.text


# — The file ————————————————————————————————————————————————————————


def test_apk_download_serves_with_android_mime_and_attachment(releases_client):
    client, releases = releases_client
    _publish(releases, MANIFEST)

    resp = client.get(f"/downloads/{MANIFEST['file']}")

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/vnd.android.package-archive"
    assert f'attachment; filename="{MANIFEST["file"]}"' in resp.headers["content-disposition"]
    assert resp.content == b"fake-apk-bytes"


@pytest.mark.parametrize(
    "name",
    [
        "missing.apk",
        "not-an-apk.txt",
        "app-release.apk.bak",
        "..%2Fapp%2Fmain.py",
        "%2E%2E%2Fsecret.apk",
        "sub/dir/file.apk",
    ],
)
def test_apk_download_rejects_anything_but_plain_apk_names(releases_client, name):
    client, releases = releases_client
    _publish(releases, MANIFEST)

    resp = client.get(f"/downloads/{name}")

    assert resp.status_code == 404


# — JSON manifest ————————————————————————————————————————————————————


def test_app_release_endpoint_returns_the_manifest(releases_client):
    client, releases = releases_client
    _publish(releases, MANIFEST)

    resp = client.get("/api/v1/app/release")

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["version"] == MANIFEST["version"]
    assert body["data"]["sha256"] == MANIFEST["sha256"]
    assert body["meta"]["sources"] == []


def test_app_release_endpoint_404_until_published(releases_client):
    client, _releases = releases_client

    resp = client.get("/api/v1/app/release")

    assert resp.status_code == 404
    assert resp.json()["code"] == "NOT_FOUND"
