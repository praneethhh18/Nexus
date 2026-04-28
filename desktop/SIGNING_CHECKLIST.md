# Desktop installer signing — checklist

The setup wizard, tray, and main window are wired up. Before the installer
is fit to send to a paying customer, it needs to be **code-signed** so
Windows SmartScreen and macOS Gatekeeper don't scare the user away with a
"this app is from an unknown developer" warning.

This document is the punch-list. Run through it once; the build commands at
the bottom will then produce signed artefacts.

---

## Windows — what you need

1. **Code-signing certificate.** Two options:

   | Type | Cost (annual) | SmartScreen reputation |
   |---|---|---|
   | OV (Organisation Validated) | ~$80–150 | Builds slowly over downloads |
   | EV (Extended Validation)    | ~$300–400 | Trusted immediately |

   For a first commercial release, OV is fine. Vendors: Sectigo, DigiCert,
   GlobalSign, SSL.com.

2. **Verify the cert is installed** in `Windows Certificate Manager →
   Personal → Certificates`. Note the *thumbprint*.

3. **Add this to `desktop/package.json`** under `build.win`:
   ```json
   "win": {
     "target": [{ "target": "nsis", "arch": ["x64"] }],
     "icon": "assets/icon.ico",
     "certificateSubjectName": "Your Company Pvt Ltd",
     "signingHashAlgorithms": ["sha256"],
     "rfc3161TimeStampServer": "http://timestamp.digicert.com"
   }
   ```
   electron-builder will use the Personal cert store automatically. For CI,
   use `CSC_LINK` (.pfx as base64) and `CSC_KEY_PASSWORD` env vars instead.

4. **Test it**: after `npm run dist:win`, the resulting `.exe` should show
   a publisher line in the UAC prompt. Right-click → Properties → Digital
   Signatures should show a valid timestamp.

---

## macOS — what you need

1. **Apple Developer Program** membership ($99 / year).
2. **Two certs** in Keychain:
   - "Developer ID Application: Your Name" — signs the .app bundle.
   - "Developer ID Installer: Your Name" — signs the .pkg installer.
3. **App-specific password** (Apple ID → Sign-in & Security → App-specific
   passwords) for notarisation.
4. **Add to `desktop/package.json`** under `build.mac`:
   ```json
   "mac": {
     "target": [{ "target": "dmg", "arch": ["universal"] }],
     "icon": "assets/icon.icns",
     "category": "public.app-category.productivity",
     "hardenedRuntime": true,
     "gatekeeperAssess": false,
     "entitlements": "build/entitlements.mac.plist",
     "entitlementsInherit": "build/entitlements.mac.plist",
     "notarize": {
       "teamId": "YOUR_TEAM_ID"
     }
   }
   ```
5. Set env before building:
   ```bash
   export APPLE_ID="you@example.com"
   export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
   export APPLE_TEAM_ID="ABCD1234EF"
   ```
6. **`build/entitlements.mac.plist`** — minimal version:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/>
     <key>com.apple.security.cs.allow-jit</key><true/>
     <key>com.apple.security.network.client</key><true/>
   </dict>
   </plist>
   ```
   `network.client` is needed for the Ollama probe, model pull, and the
   FastAPI backend probe.

---

## Linux

Linux installers don't need signing in the OS sense, but you should still:

- Generate a `SHA256SUMS` file alongside the AppImage / .deb so users can
  verify integrity.
- Sign the SHA256SUMS with your GPG key (`gpg --detach-sign SHA256SUMS`).
- Publish your public key on a keyserver and link it from the download page.

---

## Build commands (after the above is configured)

```bash
cd desktop
npm install

# Windows installer (x64 .exe via NSIS)
npm run dist:win

# macOS installer (universal .dmg)
npm run dist:mac

# Linux artefacts (.AppImage + .deb)
npm run dist:linux
```

Outputs land in `desktop/dist/`.

---

## Distribution

1. **Don't host installers in the GitHub repo** — they bloat clones. Use
   GitHub Releases (`gh release create v2.1.0 dist/*`) or a CDN.
2. **Auto-update**: electron-builder ships with `electron-updater`. Wire it
   to a static JSON feed or to GitHub Releases. Worth doing before v3.
3. **Crash reports**: hook `app.on('render-process-gone')` and ship a
   minidump to Sentry. Free tier is enough until you have ~200 users.

---

## Sanity-check the wizard before signing

Run from the project root:

```bash
cd desktop
npm install
npm start          # opens setup wizard against your local Ollama
```

Confirm:
- [ ] Wizard appears on first launch.
- [ ] Ollama detection works (running + missing).
- [ ] "Install Ollama" button opens https://ollama.com/download in browser.
- [ ] Model pull shows live percentage and byte counts.
- [ ] Embedding pull shows the same.
- [ ] Backend probe flips to ✓ once `uvicorn api.server:app` is up.
- [ ] "Open NexusAgent" button is disabled until all four steps are green.
- [ ] After clicking it, main window appears, wizard closes.
- [ ] Re-launching the app skips the wizard (`.setup-complete` marker exists).
- [ ] Tray menu's "Re-run setup wizard…" deletes the marker and re-shows it.

If everything above is true, you're ready to ship.
