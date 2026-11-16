"""App release manifest and the /download landing page.

A release is whatever `scripts/package_apk.ps1` published into the releases
directory:

    releases/
    ├── latest.json                    # the manifest (single source of truth)
    └── mlbb-tracker-<version>.apk

The download page is plain server-rendered HTML — indexable, fast, and it
works without JavaScript or the Flutter canvas. If no release has been
published the page says so honestly instead of showing a broken link.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

MANIFEST_NAME = "latest.json"

# Filenames we are ever willing to serve from the releases directory.
_APK_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*\.apk$")

_REQUIRED_KEYS = ("version", "file", "size_bytes", "sha256")


def read_manifest(releases_dir: Path) -> dict | None:
    """The published release manifest, or None when nothing is published.

    Read per request (not cached) so publishing a release takes effect
    immediately without a backend restart.
    """
    path = releases_dir / MANIFEST_NAME
    try:
        # utf-8-sig tolerates a BOM (PowerShell's Set-Content adds one).
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    if any(k not in data for k in _REQUIRED_KEYS):
        return None
    file_name = data.get("file")
    if not isinstance(file_name, str) or not _APK_NAME.fullmatch(file_name):
        return None
    return data


def apk_path(releases_dir: Path, filename: str) -> Path | None:
    """Resolve a requested APK filename safely, or None if not allowed.

    Only plain `*.apk` names inside the releases directory itself are served —
    no traversal, no other extensions, no nested paths.
    """
    if not _APK_NAME.fullmatch(filename):
        return None
    root = releases_dir.resolve()
    candidate = (root / filename).resolve()
    if candidate.parent != root or not candidate.is_file():
        return None
    return candidate


def _fmt_size(size_bytes: int | float | str) -> str:
    try:
        size = float(size_bytes)
    except (TypeError, ValueError):
        return "—"
    if size <= 0:
        return "—"
    return f"{size / (1024 * 1024):.1f} MB"


def _fmt_sha(sha: str) -> tuple[str, str]:
    """(short form for the meta row, full form for the <details> block)."""
    sha = str(sha)
    return sha[:12] + "…", sha


def render_download_page(manifest: dict | None) -> str:
    """The /download HTML page. No JavaScript; styles are inline."""
    published = manifest is not None
    version = str(manifest.get("version", "")) if published else ""
    file_name = str(manifest.get("file", "")) if published else ""
    size = _fmt_size(manifest.get("size_bytes")) if published else "—"
    sha_short, sha_full = _fmt_sha(manifest.get("sha256", "")) if published else ("", "")
    released = str(manifest.get("released_at", "")) if published else ""
    min_android = str(manifest.get("min_android", "")) if published else ""
    signed = str(manifest.get("signed_with", "")) if published else ""
    channel = str(manifest.get("channel", "release")) if published else ""
    notes = list(manifest.get("notes") or []) if published else []

    channel_badge = (
        f'<span class="badge badge-{channel}">{channel}</span>'
        if published and channel and channel != "release"
        else ""
    )

    if published:
        release_card = f"""
      <div class="card release">
        <div class="release-head">
          <span class="badge">v{version}</span>{channel_badge}
          <span class="release-date">published {released}</span>
        </div>
        <p class="release-lede">
          The full app for Android — hero analytics, recorded meta history,
          esports standings and your own tracked stats, offline-friendly.
        </p>
        <div class="cta-row">
          <a class="btn btn-primary" href="/downloads/{file_name}" download>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v10m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            Download APK
          </a>
          <a class="btn btn-ghost" href="/">Open the web app</a>
        </div>
        <dl class="meta">
          <div><dt>Version</dt><dd>{version}</dd></div>
          <div><dt>Size</dt><dd>{size}</dd></div>
          <div><dt>Updated</dt><dd>{released}</dd></div>
          {f'<div><dt>Requires</dt><dd>Android {min_android}</dd></div>' if min_android else ''}
          <div><dt>SHA-256</dt><dd><code title="{sha_full}">{sha_short}</code></dd></div>
        </dl>
        <details class="hash">
          <summary>Full checksum &amp; signing</summary>
          <p><code>{sha_full}</code></p>
          <p class="muted">{signed}</p>
        </details>
        {'<details class="notes" open><summary>What&rsquo;s new</summary><ul>' + ''.join(f'<li>{n}</li>' for n in notes) + '</ul></details>' if notes else ''}
      </div>
    """
    else:
        release_card = """
      <div class="card release">
        <div class="release-head">
          <span class="badge badge-pending">no build published yet</span>
        </div>
        <p class="release-lede">
          No public APK has been published from this repository so far — this
          page will carry it the moment one is packaged. Nothing is offered
          for download until a real build exists.
        </p>
        <div class="cta-row">
          <a class="btn btn-primary" href="/">Open the web app</a>
        </div>
        <p class="muted small">
          Maintainers: build one with
          <code>.\\scripts\\package_apk.ps1</code> from the repository root.
        </p>
      </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="description" content="Download MLBB Tracker for Android — live Mobile Legends meta analytics, recorded history and esports standings. Unofficial fan project.">
<title>Download MLBB Tracker</title>
<style>
  :root {{
    --bg: #111318; --bg-2: #171a22; --card: #1b1f29; --border: #262b38;
    --text: #f5f5f7; --text-2: #a4a8b4; --muted: #747b8b;
    --accent: #8b7cff; --accent-soft: rgba(139,124,255,.16);
    --ok: #39d6a3; --warn: #f5b85b;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{
      --bg: #f6f7fb; --bg-2: #ffffff; --card: #ffffff; --border: #e2e5ee;
      --text: #14161c; --text-2: #4b5162; --muted: #8a90a2;
      --accent: #6c5ce7; --accent-soft: rgba(108,92,231,.10);
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  .wrap {{ max-width: 640px; margin: 0 auto; padding: 48px 20px 64px; }}
  .hero {{ text-align: center; margin-bottom: 28px; }}
  .logo {{
    width: 76px; height: 76px; border-radius: 20px; margin: 0 auto 16px;
    background: linear-gradient(135deg, var(--accent), #5646d6);
    display: grid; place-items: center;
    box-shadow: 0 8px 28px rgba(108,92,231,.35);
  }}
  .logo svg {{ width: 40px; height: 40px; }}
  h1 {{ font-size: 28px; margin: 0 0 6px; letter-spacing: -0.02em; }}
  .tagline {{ color: var(--text-2); margin: 0; }}
  .fan-note {{ color: var(--muted); font-size: 13px; margin-top: 8px; }}
  .card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 24px; margin-bottom: 16px;
  }}
  .release-head {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .badge {{
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 13px; font-weight: 600; letter-spacing: .02em;
    background: var(--accent-soft); color: var(--accent);
  }}
  .badge-preview {{ background: rgba(245,184,91,.14); color: var(--warn); }}
  .badge-pending {{ background: rgba(245,184,91,.14); color: var(--warn); }}
  .release-date {{ color: var(--muted); font-size: 13px; }}
  .release-lede {{ color: var(--text-2); margin: 12px 0 20px; }}
  .cta-row {{ display: flex; gap: 12px; flex-wrap: wrap; }}
  .btn {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 12px 22px; border-radius: 12px; text-decoration: none;
    font-weight: 600; font-size: 15px; transition: transform .15s ease, opacity .15s ease;
  }}
  .btn:hover {{ transform: translateY(-1px); }}
  .btn:active {{ transform: translateY(0); }}
  .btn-primary {{ background: var(--accent); color: #fff; }}
  .btn-primary svg {{ width: 18px; height: 18px; }}
  .btn-ghost {{ color: var(--text); border: 1px solid var(--border); background: var(--bg-2); }}
  .meta {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px 20px; margin: 22px 0 4px; padding: 16px 0 0;
    border-top: 1px solid var(--border);
  }}
  .meta dt {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
  .meta dd {{ margin: 2px 0 0; font-weight: 600; font-size: 14px; word-break: break-all; }}
  details {{ margin-top: 14px; color: var(--text-2); font-size: 14px; }}
  summary {{ cursor: pointer; color: var(--accent); font-weight: 600; }}
  details p {{ margin: 10px 0 0; word-break: break-all; }}
  details ul {{ margin: 10px 0 0; padding-left: 20px; }}
  details li {{ margin-bottom: 6px; }}
  .muted {{ color: var(--muted); }}
  .small {{ font-size: 13px; }}
  code {{
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 12.5px; background: var(--bg-2); border: 1px solid var(--border);
    padding: 1px 6px; border-radius: 6px;
  }}
  .steps ol {{ margin: 12px 0 0; padding-left: 22px; color: var(--text-2); }}
  .steps li {{ margin-bottom: 10px; }}
  .steps b {{ color: var(--text); }}
  h2 {{ font-size: 17px; margin: 0 0 4px; letter-spacing: -0.01em; }}
  .webapp p {{ color: var(--text-2); margin: 8px 0 18px; }}
  footer {{
    text-align: center; color: var(--muted); font-size: 13px;
    margin-top: 36px; line-height: 1.7;
  }}
  footer a {{ color: var(--text-2); }}
  :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 8px; }}
  @media (max-width: 480px) {{
    .wrap {{ padding: 32px 16px 48px; }}
    .cta-row .btn {{ flex: 1 1 100%; justify-content: center; }}
  }}
</style>
</head>
<body>
<main class="wrap">
  <header class="hero">
    <div class="logo" aria-hidden="true">
      <svg viewBox="0 0 24 24"><path d="M4 17 9 9l4 5 3-4 4 7" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="9" r="1.6" fill="#fff"/><circle cx="16" cy="10" r="1.6" fill="#fff"/></svg>
    </div>
    <h1>MLBB Tracker</h1>
    <p class="tagline">Live meta analytics for Mobile Legends: Bang Bang</p>
    <p class="fan-note">Unofficial fan project — not affiliated with or endorsed by Moonton.</p>
  </header>
  {release_card}
  <section class="card steps">
    <h2>Install on Android</h2>
    <ol>
      <li><b>Download the APK</b> above and open it from your notifications or file manager.</li>
      <li>If asked, <b>allow installs from this source</b> — Android requires this for apps outside the Play Store.</li>
      <li><b>Tap Install</b>, then open MLBB Tracker from your home screen.</li>
    </ol>
  </section>
  <section class="card webapp">
    <h2>Prefer not to install anything?</h2>
    <p>
      The web app is the same codebase, served from this site: rankings,
      hero pages, esports standings and the full player connect flow. It can
      also be installed to your home screen from your browser menu.
    </p>
    <a class="btn btn-ghost" href="/">Open the web app</a>
  </section>
  <footer>
    Data: Rone Arena community API &middot; MLBBDex (CC BY-SA).<br>
    Mobile Legends: Bang Bang is a trademark of Shanghai Moonton Technology.<br>
    <a href="/">Web app</a> &middot; <a href="/docs">API docs</a>
  </footer>
</main>
</body>
</html>
"""
