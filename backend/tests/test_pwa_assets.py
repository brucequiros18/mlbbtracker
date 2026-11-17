"""Guards for the installable web app (PWA) assets.

These check the source files in `mobile/web/` rather than a running server:
the build copies them verbatim, so a regression here breaks installability
and offline support in production.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[2] / "mobile" / "web"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((WEB / "manifest.json").read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


# — Manifest ——————————————————————————————————————————————————————————


def test_manifest_is_installable(manifest):
    assert manifest["name"]
    assert manifest["short_name"]
    assert manifest["description"]
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["display"] in {"standalone", "minimal-ui", "fullscreen"}
    assert manifest["theme_color"] == "#111318"
    assert manifest["background_color"] == "#111318"


def test_manifest_ships_any_and_maskable_icons_at_both_sizes(manifest):
    icons = manifest["icons"]
    by_purpose: dict[str, set[int]] = {}
    for icon in icons:
        purpose = icon.get("purpose", "any")
        by_purpose.setdefault(purpose, set()).add(int(icon["sizes"].split("x")[0]))

    assert by_purpose.get("any") == {192, 512}
    assert by_purpose.get("maskable") == {192, 512}

    for icon in icons:
        path = WEB / icon["src"]
        assert path.is_file(), f"missing icon {icon['src']}"
        assert icon["type"] == "image/png"
        expected = int(icon["sizes"].split("x")[0])
        assert _png_size(path) == (expected, expected)


def test_manifest_shortcuts_point_at_real_routes(manifest):
    routes = {"/#/home", "/#/players", "/#/heroes", "/#/leaderboards", "/#/saved", "/#/esports"}
    shortcuts = manifest["shortcuts"]
    assert shortcuts
    for shortcut in shortcuts:
        assert shortcut["url"].startswith("/#/")
        assert shortcut["url"] in routes, shortcut["url"]


# — Service worker ——————————————————————————————————————————————————————


def test_service_worker_precaches_the_shell_and_spares_the_api():
    source = (WEB / "sw.js").read_text(encoding="utf-8")

    assert "CACHE_VERSION" in source
    assert "/main.dart.js" in source
    assert "/flutter_bootstrap.js" in source
    assert "/assets/FontManifest.json" in source
    assert "/canvaskit/canvaskit.wasm" in source
    # API and release routes must never be served from the cache.
    assert r"/^\/api(\/|$)/" in source
    assert r"/^\/download(\/|$)/" in source
    # Navigations fall back to the cached shell.
    assert "networkFirstNavigation" in source


def test_index_registers_our_worker_and_not_flutters_stub():
    html = (WEB / "index.html").read_text(encoding="utf-8")

    assert "navigator.serviceWorker.register('sw.js')" in html
    assert "flutter_service_worker" not in html
    assert 'rel="manifest"' in html
    assert 'apple-touch-icon' in html


def test_bootstrap_does_not_load_flutters_deprecated_worker():
    source = (WEB / "flutter_bootstrap.js").read_text(encoding="utf-8")

    assert "{{flutter_js}}" in source
    assert "{{flutter_build_config}}" in source
    assert "_flutter.loader.load();" in source
    # No serviceWorkerSettings: that would replace sw.js (same scope) with
    # Flutter's self-unregistering stub.
    assert "serviceWorkerSettings:" not in source
