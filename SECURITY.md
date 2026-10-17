# Security

## Found a vulnerability?

Please do not open a public issue. Instead use this repository's **Security → Report a vulnerability** (private security advisory) section. If you can, include: the affected version, step-by-step instructions to reproduce it, and its impact. I try to answer reports within a few days.

## The libzie security model

libzie is a single-user app that runs only on your own computer. The server listens only on `127.0.0.1`; it cannot be reached from the network. Even so, these measures keep another website open in your browser, or another program on the same computer, from using this local server:

- **Session key:** A random key is kept in `%APPDATA%\libzie\session.key`, a file only your Windows account can read, and it is renewed at every start. The app opens the address with the key, and the server keeps it in a session cookie (`HttpOnly`, `SameSite=Strict`, a port-specific name). No API request is processed without the key.
- **Protection against a fake libzie:** Before connecting to an already open libzie, the process on the other side is asked to prove with an HMAC that it knows the key; if it cannot, the key is never sent. The server takes the port with `SO_EXCLUSIVEADDRUSE`, so no other program can bind the same port and steal connections.
- **Write restrictions:** System folders, the Startup folder and libzie's own installation and settings folders cannot be written to; executable types such as `.exe`, `.bat`, `.ps1` and `.lnk` cannot be uploaded to the archive or renamed to such an extension.
- **Requests from other sites are rejected (CSRF / DNS rebinding):** The `Host`, `Origin` and `Sec-Fetch-Site` headers are checked, and every request that changes state requires a custom header (`X-Libzie`).
- **Opening files uses an allow list:** "Open in default app" works only for document, image, audio/video and archive types; `.exe`, `.bat`, `.lnk`, `.ps1`, `.py` and the like are never opened directly.
- **User files are served in a sandbox:** Files other than PDFs come with `Content-Security-Policy: sandbox`; a malicious SVG/HTML file that lands in your folder cannot run scripts and cannot reach the app's API.
- **Strict content policy:** The app page has no `eval`, and loads only its own files and the weather service. pdf.js runs with `isEvalSupported: false` (against attacks such as CVE-2024-4367).
- **Path safety:** All paths are confined to the `materials` folder; Windows reserved names (`CON`, `NUL`…) and invalid names are rejected.

## Update security

The in-app update downloads only from this repository's GitHub releases, over HTTPS; it verifies the size and the SHA-256 digest of the downloaded file (the one GitHub provides, or `SHA256SUMS.txt` in the release). If there is no digest the update is not made. The app is **not code-signed**, so Windows SmartScreen may show a warning. Every release is published with a `SHA256SUMS.txt`; to verify a file you downloaded by hand:

```
certutil -hashfile libzie-setup.exe SHA256
```

The value printed must match the line in `SHA256SUMS.txt`. The only trustworthy source is this repository's **Releases** page.

## Known limits

- A malicious program running under the same Windows account can already reach your files; libzie does not protect against that.
- There is no code signature (see above).
- pdf.js 3.11.174 is used (another current version needs ES modules). Mitigations against the known eval-based vulnerability are in place; the PDF-handling code still runs inside the browser/WebView2 sandbox.
