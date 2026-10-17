"""libzie updater: checks GitHub releases; in the packaged Windows app it downloads and applies the new version.

Uses only the Python standard library. The download address is never taken from the client: the server reads the release
information from GitHub itself every time and downloads only this repository's release files.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

import i18n
from i18n import AppError

VERSION = "0.1.3"  # GitHub Actions rewrites this line at build time from the release tag (v0.1.3 → 0.1.3)
REPO = "nopescope0/libzie"
FROZEN = getattr(sys, "frozen", False)
# Only for trying things out during development (unpackaged runs): points at a fake release server, and the download address check is off.
# In the packaged app this environment variable is ignored.
TEST_API = "" if FROZEN else os.environ.get("LIBZIE_UPDATE_URL", "")
API = TEST_API or f"https://api.github.com/repos/{REPO}/releases/latest"
ASSETS = {"installer": "libzie-setup.exe", "portable": "libzie-portable.exe"}

EXIT_HOOKS = []  # app.py: run before the app closes with os._exit (removes the tray icon)
_lock = threading.Lock()
_state = {"phase": "idle", "done": 0, "total": 0, "error": "", "error_code": "", "error_vars": {}}  # idle | downloading | restarting | error


class UpdateError(AppError):
    """Update error with an id (UpdateError("upd.err.no_release")); the text is in static/lang/*.json."""


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    """Download redirects (GitHub → CDN) may only go to https; they cannot be downgraded to plain http."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not TEST_API and not newurl.lower().startswith("https://"):
            raise UpdateError("upd.err.redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_HttpsOnly)


def kind():
    """installer: installed with the wizard · portable: single-file exe · source: python server.py (not updated from within the app)"""
    if not FROZEN or sys.platform != "win32":
        return "source"
    return "installer" if (Path(sys.executable).parent / "unins000.exe").exists() else "portable"


def parse_version(text):
    return tuple(int(n) for n in re.findall(r"\d+", str(text).split("-")[0])) or (0,)


def fetch_release():
    req = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": f"libzie/{VERSION}"})
    try:
        with _opener.open(req, timeout=8) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise UpdateError("upd.err.no_release") from e
        if e.code in (403, 429):
            raise UpdateError("upd.err.rate_limited") from e
        raise UpdateError("upd.err.version_http", code=e.code) from e
    except (OSError, ValueError) as e:
        raise UpdateError("upd.err.offline") from e


def check():
    rel = fetch_release()
    tag = str(rel.get("tag_name") or "")
    if not tag:
        raise UpdateError("upd.err.unreadable")
    k = kind()
    names = {a.get("name") for a in rel.get("assets") or []}
    return {
        "current": VERSION,
        "latest": tag.lstrip("vV"),
        "available": parse_version(tag) > parse_version(VERSION),
        "kind": k,
        # If this install type's file is not attached to the release (build in progress or failed) no update is offered
        "downloadable": k == "source" or ASSETS[k] in names,
        "url": rel.get("html_url") or f"https://github.com/{REPO}/releases",
    }


def status():
    with _lock:
        return dict(_state)


def _set(**kw):
    with _lock:
        _state.update(kw)


def _clean_env():
    """PyInstaller's single-file build passes its temporary folder to child processes through environment variables;
    if the new libzie inherits them it looks for the deleted folder. They are removed before being passed to launched processes."""
    return {k: v for k, v in os.environ.items() if not k.startswith("_PYI") and k != "_MEIPASS2"}


def _detached(console):
    """A process that outlives this one. The script (cmd) needs a hidden console: in a console-less cmd the `ping` wait
    ends immediately and the retry loop runs out before the app has closed."""
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0) if console else getattr(subprocess, "DETACHED_PROCESS", 0)
    return {"creationflags": flags, "close_fds": True, "env": _clean_env()}


def _download(url, dest, size, digest):
    req = urllib.request.Request(url, headers={"User-Agent": f"libzie/{VERSION}"})
    sha = hashlib.sha256()
    with _opener.open(req, timeout=30) as r, open(dest, "wb") as f:
        _set(total=int(r.headers.get("Content-Length") or size or 0), done=0)
        while True:
            chunk = r.read(1 << 18)
            if not chunk:
                break
            f.write(chunk)
            sha.update(chunk)
            _set(done=_state["done"] + len(chunk))
    got = dest.stat().st_size
    if size and got != size:
        raise UpdateError("upd.err.incomplete")
    with open(dest, "rb") as f:
        if f.read(2) != b"MZ":
            raise UpdateError("upd.err.not_app")
    if sha.hexdigest() != digest[7:].lower():
        raise UpdateError("upd.err.checksum_bad")


def _expected_digest(rel, asset):
    """The expected SHA-256 digest of the file to download: GitHub's asset `digest` field, else SHA256SUMS.txt in the release.
    If neither exists no update is made (a size/header check alone is not enough)."""
    digest = str(asset.get("digest") or "")
    if digest.startswith("sha256:") and re.fullmatch(r"[0-9a-fA-F]{64}", digest[7:]):
        return digest.lower()
    sums = next((a for a in rel.get("assets") or [] if a.get("name") == "SHA256SUMS.txt"), None)
    url = str((sums or {}).get("browser_download_url") or "")
    if url and (TEST_API or url.startswith(f"https://github.com/{REPO}/releases/download/")):
        try:
            with _opener.open(urllib.request.Request(url, headers={"User-Agent": f"libzie/{VERSION}"}), timeout=15) as r:
                text = r.read(1 << 16).decode("utf-8", "replace")
            for line in text.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1].lstrip("*") == asset.get("name") and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
                    return "sha256:" + parts[0].lower()
        except (OSError, UpdateError):
            pass
    raise UpdateError("upd.err.no_checksum")


def _can_write(folder):
    try:
        probe = folder / ".libzie-write-test"
        probe.write_bytes(b"")
        probe.unlink()
        return True
    except OSError:
        return False


_SWAP_BAT = """@echo off
rem libzie portable update: swaps in the new exe once the app has exited, then starts it
set n=0
:wait
set /a n+=1
if %n% gtr 90 exit /b 1
ping 127.0.0.1 -n 2 >nul
move /y "%LIBZIE_NEW%" "%LIBZIE_EXE%" >nul 2>&1
if errorlevel 1 goto wait
start "" "%LIBZIE_EXE%"
(goto) 2>nul & del "%~f0"
"""


def _run():
    try:
        k = kind()
        rel = fetch_release()
        if parse_version(rel.get("tag_name", "")) <= parse_version(VERSION):
            raise UpdateError("upd.err.up_to_date")
        asset = next((a for a in rel.get("assets") or [] if a.get("name") == ASSETS[k]), None)
        if not asset:
            raise UpdateError("upd.err.asset_missing")
        url = str(asset.get("browser_download_url") or "")
        if not TEST_API and not url.startswith(f"https://github.com/{REPO}/releases/download/"):
            raise UpdateError("upd.err.bad_url")
        digest = _expected_digest(rel, asset)
        exe = Path(sys.executable)
        if k == "portable" and not _can_write(exe.parent):
            raise UpdateError("upd.err.not_writable", dir=str(exe.parent))
        for pattern in ("libzie-update-*", "libzie-guncelleme-*"):
            for old in Path(tempfile.gettempdir()).glob(pattern):  # leftovers of earlier attempts
                shutil.rmtree(old, ignore_errors=True)
        work = Path(tempfile.mkdtemp(prefix="libzie-update-"))  # unpredictable, accessible only to this user
        dest = work / ASSETS[k]
        _download(url, dest, int(asset.get("size") or 0), digest)

        if k == "installer":
            # The wizard closes the running libzie, refreshes the files and reopens the app (libzie.iss: WizardSilent)
            subprocess.Popen([str(dest), "/SILENT", "/CLOSEAPPLICATIONS", "/SUPPRESSMSGBOXES", "/NORESTART"], **_detached(False))
        else:
            bat = work / "swap.bat"
            bat.write_text(_SWAP_BAT, encoding="ascii")
            env = _clean_env()
            env.update(LIBZIE_NEW=str(dest).replace("/", "\\"), LIBZIE_EXE=str(exe).replace("/", "\\"))  # move does not like forward slashes
            subprocess.Popen(["cmd", "/c", str(bat)], **{**_detached(True), "env": env})
        _set(phase="restarting")
        def _bye():
            for fn in EXIT_HOOKS:
                try:
                    fn()
                except Exception:  # noqa: BLE001
                    pass
            os._exit(0)
        threading.Timer(1.5, _bye).start()
    except UpdateError as e:
        _set(phase="error", error=str(e), error_code=e.code, error_vars=e.vars)
    except Exception as e:  # noqa: BLE001 — the error is shown in the UI
        _set(phase="error", error=i18n.msg("upd.err.failed", error=str(e)), error_code="upd.err.failed", error_vars={"error": str(e)})


def start_apply():
    if kind() == "source":
        raise UpdateError("upd.err.from_source")
    with _lock:
        if _state["phase"] in ("downloading", "restarting"):
            raise UpdateError("upd.err.in_progress")
        _state.update(phase="downloading", done=0, total=0, error="", error_code="", error_vars={})
    threading.Thread(target=_run, daemon=True).start()
