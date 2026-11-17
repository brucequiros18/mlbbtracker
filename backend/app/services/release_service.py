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

import base64
import hashlib
import html
import json
import re
from pathlib import Path

MANIFEST_NAME = "latest.json"

# Filenames we are ever willing to serve from the releases directory.
_APK_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*\.apk$")

_REQUIRED_KEYS = ("version", "file", "size_bytes", "sha256")

# The only script on /download: service-worker registration + the browser's
# install prompt. Kept as a constant so its SHA-256 can be pinned in the CSP
# instead of allowing 'unsafe-inline'.
INSTALL_SCRIPT = """(function () {
  var standalone =
    window.matchMedia('(display-mode: standalone)').matches ||
    navigator.standalone === true;

  var button = document.getElementById('install-button');
  var status = document.getElementById('install-status');
  var hint = document.getElementById('install-hint');
  if (!button || !status) return;

  function installed() {
    button.hidden = true;
    if (hint) hint.hidden = true;
    status.textContent =
      'Installed - open MLBB Tracker from your home screen or app list.';
    status.hidden = false;
  }

  if (standalone) { installed(); return; }

  // Registering the worker makes this page installable on a first visit too.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(function () {});
  }

  var prompt = null;
  window.addEventListener('beforeinstallprompt', function (event) {
    event.preventDefault();
    prompt = event;
    button.hidden = false;
    status.hidden = true;
  });

  button.addEventListener('click', function () {
    if (!prompt) return;
    var current = prompt;
    prompt = null;
    button.hidden = true;
    current.prompt();
    current.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        status.textContent = 'Installing...';
        status.hidden = false;
      } else {
        status.textContent =
          'Install cancelled - you can install any time from your browser menu.';
        status.hidden = false;
      }
    });
  });

  window.addEventListener('appinstalled', installed);
})();"""


def _script_hash(source: str) -> str:
    digest = hashlib.sha256(source.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


# /download is intentionally script-light: one inline script, pinned by hash,
# plus the manifest and the service worker it registers.
DOWNLOAD_CSP = (
    "default-src 'none'; "
    f"script-src 'sha256-{_script_hash(INSTALL_SCRIPT)}'; "
    "style-src 'unsafe-inline'; img-src 'self' data:; "
    "manifest-src 'self'; worker-src 'self'; "
    "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def _esc(value: object) -> str:
    """Escape any manifest-derived value before putting it in the page."""
    return html.escape(str(value), quote=True)



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
    """The /download HTML page. One inline script, pinned by CSP hash."""
    published = manifest is not None
    version = _esc(manifest.get("version", "")) if published else ""
    file_name = _esc(manifest.get("file", "")) if published else ""
    size = _fmt_size(manifest.get("size_bytes")) if published else "—"
    if published:
        sha_short_raw, sha_full_raw = _fmt_sha(manifest.get("sha256", ""))
        sha_short, sha_full = _esc(sha_short_raw), _esc(sha_full_raw)
    else:
        sha_short = sha_full = ""
    released = _esc(manifest.get("released_at", "")) if published else ""
    min_android = _esc(manifest.get("min_android", "")) if published else ""
    signed = _esc(manifest.get("signed_with", "")) if published else ""
    channel = _esc(manifest.get("channel", "release")) if published else ""
    channel_class = re.sub(r"[^a-z0-9-]", "", str(manifest.get("channel", "")) if published else "")
    notes = [_esc(note) for note in (manifest.get("notes") or [])] if published else []

    channel_badge = (
        f'<span class="badge badge-{channel_class}">{channel}</span>'
        if published and channel_class and channel != "release"
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

    # The JS contains braces, so it is interpolated as a prebuilt string
    # rather than inlined into this f-string.
    install_script = f"<script>{INSTALL_SCRIPT}</script>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="description" content="Download MLBB Tracker for Android — live Mobile Legends meta analytics, recorded history and esports standings. Unofficial fan project.">
<meta name="theme-color" content="#111318">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="MLBB Tracker">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
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
    border: 0; cursor: pointer; font-family: inherit;
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
  .install p {{ color: var(--text-2); margin: 8px 0 16px; }}
  .install .status {{ color: var(--ok); font-size: 14px; margin: 0 0 14px; }}
  .install-help {{ margin: 18px 0 16px; padding-top: 16px; border-top: 1px solid var(--border); }}
  .install-help p {{ margin: 0 0 8px; }}
  .install-help ul {{ margin: 0; padding-left: 20px; color: var(--text-2); font-size: 14px; }}
  .install-help li {{ margin-bottom: 6px; }}
  .install-help b {{ color: var(--text); }}
  [hidden] {{ display: none !important; }}
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
  <section class="card install">
    <h2>Install the web app</h2>
    <p>
      The same app runs in your browser — no APK, no store, no update step.
      Installed, it opens in its own window and keeps its shell cached, so it
      still launches offline; live data needs a connection.
    </p>
    <p class="status" id="install-status" role="status" hidden></p>
    <button class="btn btn-primary" id="install-button" type="button" hidden>
      Install the web app
    </button>
    <div class="install-help" id="install-hint">
      <p class="muted small">No install button? Add it from your browser menu:</p>
      <ul>
        <li><b>Chrome or Edge (desktop):</b> the install icon in the address bar, or menu &rarr; <b>Install page as app</b>.</li>
        <li><b>Chrome (Android):</b> menu &rarr; <b>Add to Home screen</b> &rarr; <b>Install</b>.</li>
        <li><b>Safari (iOS):</b> Share &rarr; <b>Add to Home Screen</b>.</li>
      </ul>
    </div>
    <div class="cta-row">
      <a class="btn btn-ghost" href="/">Open the web app</a>
    </div>
  </section>
  <footer>
    Data: Rone Arena community API &middot; MLBBDex (CC BY-SA).<br>
    Mobile Legends: Bang Bang is a trademark of Shanghai Moonton Technology.<br>
    <a href="/">Web app</a> &middot; <a href="/docs">API docs</a>
  </footer>
</main>
{install_script}
</body>
</html>
"""
