{{flutter_js}}
{{flutter_build_config}}

// MLBB Tracker ships its own service worker (web/sw.js): it caches the app
// shell for offline use and never caches API responses. Flutter's generated
// worker is a deprecated self-unregistering stub, and it would replace ours
// (same scope), so the loader is called without serviceWorkerSettings.
_flutter.loader.load();
