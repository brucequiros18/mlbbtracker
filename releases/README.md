# Published releases

This directory holds the **build artifacts** served by the download page:

```
releases/
├── latest.json              # manifest: version, size, SHA-256, notes
└── mlbb-tracker-<ver>.apk   # the APK itself
```

Both are generated — they are git-ignored on purpose:

- the APK is a large binary that does not belong in source control;
- `latest.json` must never point at an APK that isn't actually present, so
  committing it without the file would create a broken download link.

## Publish a release

From the repository root:

```powershell
.\scripts\package_apk.ps1 -Notes "What changed`nSecond line"
```

The script builds `flutter build apk --release`, copies the APK here, computes
its SHA-256, reads the real `minSdk` from the artifact with `aapt2`, and writes
`latest.json`.

## How it is served

| Route | Behaviour |
|---|---|
| `GET /download` | HTML landing page rendered from `latest.json` |
| `GET /downloads/<file>` | The APK (`application/vnd.android.package-archive`, attachment) |
| `GET /api/v1/app/release` | The manifest as JSON (`404 NOT_FOUND` when unpublished) |

The manifest is read per request, so publishing takes effect immediately —
no backend restart needed.

## No release yet?

If `latest.json` is absent, `/download` renders an honest "no build published
yet" state instead of a broken link. Nothing is fabricated.

## Signing

Until a release keystore is configured, Flutter signs release builds with the
debug keys. `latest.json` records this (`signed_with`), and the page labels the
build **preview**. Configure `android/key.properties` + a signing config in
`android/app/build.gradle.kts` before distributing through a store.
