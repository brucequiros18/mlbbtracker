<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<meta name="description" content="Download MLBB Tracker for Android - live Mobile Legends meta analytics, recorded history and esports standings. Unofficial fan project.">
<meta name="theme-color" content="#faf9f5">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="MLBB Tracker">
<link rel="apple-touch-icon" href="/app-assets/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<title>Download MLBB Tracker</title>
<style>
  :root {
    --bg: #faf9f5; --bg-2: #f0eee6; --card: #ffffff; --border: #e5e1d8;
    --text: #1f1e1d; --text-2: #57564f; --muted: #8a867a;
    --accent: #c15f3c; --accent-soft: rgba(193,95,60,.12);
    --ok: #5f7d42; --warn: #a87e2f;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #262624; --bg-2: #2e2d2a; --card: #31302d; --border: #44433e;
      --text: #f5f4ef; --text-2: #b5b1a5; --muted: #87837a;
      --accent: #d97757; --accent-soft: rgba(217,119,87,.16);
      --ok: #9db880; --warn: #d9a662;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font: 16px/1.6 "Inter", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  h1, h2 { font-family: "Lora", "Iowan Old Style", Georgia, serif; }
  .wrap { max-width: 640px; margin: 0 auto; padding: 48px 20px 64px; }
  .hero { text-align: center; margin-bottom: 28px; }
  .logo {
    width: 76px; height: 76px; border-radius: 20px; margin: 0 auto 16px;
    background: linear-gradient(135deg, #d97757, #b85433);
    display: grid; place-items: center;
    box-shadow: 0 8px 28px rgba(201,100,66,.32);
  }
  .logo svg { width: 40px; height: 40px; }
  h1 { font-size: 28px; margin: 0 0 6px; letter-spacing: -0.02em; }
  .tagline { color: var(--text-2); margin: 0; }
  .fan-note { color: var(--muted); font-size: 13px; margin-top: 8px; }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 24px; margin-bottom: 16px;
  }
  .release-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .badge {
    display: inline-block; padding: 3px 10px; border-radius: 999px;
    font-size: 13px; font-weight: 600; letter-spacing: .02em;
    background: var(--accent-soft); color: var(--accent);
  }
  .badge-preview { background: rgba(245,184,91,.14); color: var(--warn); }
  .badge-pending { background: rgba(245,184,91,.14); color: var(--warn); }
  .release-date { color: var(--muted); font-size: 13px; }
  .release-lede { color: var(--text-2); margin: 12px 0 20px; }
  .cta-row { display: flex; gap: 12px; flex-wrap: wrap; }
  .btn {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 12px 22px; border-radius: 12px; text-decoration: none;
    font-weight: 600; font-size: 15px; transition: transform .15s ease, opacity .15s ease;
    border: 0; cursor: pointer; font-family: inherit;
  }
  .btn:hover { transform: translateY(-1px); }
  .btn:active { transform: translateY(0); }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-primary svg { width: 18px; height: 18px; }
  .btn-ghost { color: var(--text); border: 1px solid var(--border); background: var(--bg-2); }
  .meta {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px 20px; margin: 22px 0 4px; padding: 16px 0 0;
    border-top: 1px solid var(--border);
  }
  .meta dt { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
  .meta dd { margin: 2px 0 0; font-weight: 600; font-size: 14px; word-break: break-all; }
  details { margin-top: 14px; color: var(--text-2); font-size: 14px; }
  summary { cursor: pointer; color: var(--accent); font-weight: 600; }
  details p { margin: 10px 0 0; word-break: break-all; }
  details ul { margin: 10px 0 0; padding-left: 20px; }
  details li { margin-bottom: 6px; }
  .muted { color: var(--muted); }
  .small { font-size: 13px; }
  code {
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 12.5px; background: var(--bg-2); border: 1px solid var(--border);
    padding: 1px 6px; border-radius: 6px;
  }
  .steps ol { margin: 12px 0 0; padding-left: 22px; color: var(--text-2); }
  .steps li { margin-bottom: 10px; }
  .steps b { color: var(--text); }
  h2 { font-size: 17px; margin: 0 0 4px; letter-spacing: -0.01em; }
  .install p { color: var(--text-2); margin: 8px 0 16px; }
  .install .status { color: var(--ok); font-size: 14px; margin: 0 0 14px; }
  .install-help { margin: 18px 0 16px; padding-top: 16px; border-top: 1px solid var(--border); }
  .install-help p { margin: 0 0 8px; }
  .install-help ul { margin: 0; padding-left: 20px; color: var(--text-2); font-size: 14px; }
  .install-help li { margin-bottom: 6px; }
  .install-help b { color: var(--text); }
  [hidden] { display: none !important; }
  footer {
    text-align: center; color: var(--muted); font-size: 13px;
    margin-top: 36px; line-height: 1.7;
  }
  footer a { color: var(--text-2); }
  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 8px; }
  @media (max-width: 480px) {
    .wrap { padding: 32px 16px 48px; }
    .cta-row .btn { flex: 1 1 100%; justify-content: center; }
  }
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
    <p class="fan-note">Unofficial fan project &mdash; not affiliated with or endorsed by Moonton.</p>
  </header>

  @if ($manifest)
    <div class="card release">
      <div class="release-head">
        <span class="badge">v{{ $manifest['version'] }}</span>
        @if (($manifest['channel'] ?? 'release') !== 'release')
          <span class="badge badge-preview">{{ $manifest['channel'] }}</span>
        @endif
        <span class="release-date">published {{ $manifest['released_at'] ?? 'unknown date' }}</span>
      </div>
      <p class="release-lede">
        The full app for Android &mdash; hero analytics, recorded meta history,
        esports standings and your own tracked stats, offline-friendly.
      </p>
      <div class="cta-row">
        <a class="btn btn-primary" href="{{ url('/downloads/'.$fileName) }}" download>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v10m0 0 4-4m-4 4-4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          Download APK
        </a>
        <a class="btn btn-ghost" href="/">Open the web app</a>
      </div>
      <dl class="meta">
        <div><dt>Version</dt><dd>{{ $manifest['version'] }}</dd></div>
        <div><dt>Size</dt><dd>{{ $size }}</dd></div>
        <div><dt>Updated</dt><dd>{{ $manifest['released_at'] ?? 'unknown' }}</dd></div>
        @if (! empty($manifest['min_android']))
          <div><dt>Requires</dt><dd>Android {{ $manifest['min_android'] }}</dd></div>
        @endif
        <div><dt>SHA-256</dt><dd><code title="{{ $sha256 }}">{{ Str::limit($sha256, 12) }}</code></dd></div>
      </dl>
      <details class="hash">
        <summary>Full checksum & signing</summary>
        <p><code>{{ $sha256 }}</code></p>
        <p class="muted">{{ $manifest['signed_with'] ?? '' }}</p>
      </details>
      @if (! empty($manifest['notes']))
        <details class="notes" open>
          <summary>What&rsquo;s new</summary>
          <ul>
            @foreach ($manifest['notes'] as $note)
              <li>{{ $note }}</li>
            @endforeach
          </ul>
        </details>
      @endif
    </div>
  @else
    <div class="card release">
      <div class="release-head">
        <span class="badge badge-pending">no build published yet</span>
      </div>
      <p class="release-lede">
        No public APK has been published from this repository so far &mdash; this
        page will carry it the moment one is packaged. Nothing is offered
        for download until a real build exists.
      </p>
      <div class="cta-row">
        <a class="btn btn-primary" href="/">Open the web app</a>
      </div>
      <p class="muted small">
        Maintainers: build one with
        <code>.\scripts\package_apk.ps1</code> from the repository root.
      </p>
    </div>
  @endif

  <section class="card steps">
    <h2>Install on Android</h2>
    <ol>
      <li><b>Download the APK</b> above and open it from your notifications or file manager.</li>
      <li>If asked, <b>allow installs from this source</b> &mdash; Android requires this for apps outside the Play Store.</li>
      <li><b>Tap Install</b>, then open MLBB Tracker from your home screen.</li>
    </ol>
  </section>

  <section class="card install">
    <h2>Install the web app</h2>
    <p>
      The same app runs in your browser &mdash; no APK, no store, no update step.
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
    <a href="/">Web app</a> &middot; <a href="/api/v1/health">API health</a>
  </footer>
</main>
<script src="/download-assets/install.js" defer></script>
</body>
</html>
