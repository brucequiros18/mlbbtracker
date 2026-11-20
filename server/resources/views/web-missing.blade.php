<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>MLBB Tracker - web app not built yet</title>
<style>
  :root {
    --bg: #0b1020; --card: #141c36; --border: #26305a;
    --text: #eaf0ff; --text-2: #a9b5d6; --muted: #6f7ca0; --accent: #2e7cd6;
  }
  @media (prefers-color-scheme: light) {
    :root {
      --bg: #eef2fa; --card: #ffffff; --border: #d8e0f0;
      --text: #10182b; --text-2: #4a5578; --muted: #7b87a8; --accent: #1e62d0;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; min-height: 100vh; display: grid; place-items: center;
    background: var(--bg); color: var(--text);
    font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .card {
    max-width: 560px; margin: 24px; padding: 32px;
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
  }
  h1 { font-size: 22px; margin: 0 0 10px; letter-spacing: -0.02em; }
  p { color: var(--text-2); margin: 0 0 12px; }
  code {
    font-family: ui-monospace, "Cascadia Code", Consolas, monospace;
    font-size: 13px; background: var(--bg); border: 1px solid var(--border);
    padding: 2px 6px; border-radius: 6px;
  }
  a { color: var(--accent); }
</style>
</head>
<body>
  <main class="card">
    <h1>The web app has not been built yet</h1>
    <p>
      The API is running, but the React + Vite bundle has not been copied into
      this server's <code>public/app</code> directory.
    </p>
    <p>
      Build it from the repository root with
      <code>npm run build</code> in <code>web/</code>, then copy
      <code>web/dist</code> to <code>server/public/app</code>.
    </p>
    <p><a href="/download">Download the Android app</a> &middot; <a href="/api/v1/health">API health</a></p>
  </main>
</body>
</html>
