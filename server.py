"""libzie — a small local server for organizing course materials (PDFs, slides, etc.).

Uses only the Python standard library. Files live in the `materials/` folder;
the folder structure is exactly the structure on disk (files can also be added from Explorer).
"""
import hmac
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import i18n
import themes
import updater
from i18n import AppError, err_json

FROZEN = getattr(sys, "frozen", False)  # application packaged with PyInstaller
BASE = Path(__file__).resolve().parent
STATIC = Path(getattr(sys, "_MEIPASS", BASE)) / "static"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", 8765))
PORT_TRIES = 1 if "PORT" in os.environ else 11  # if PORT is not given, start at 8765 and use the first free port


def documents_dir():
    """The user's Documents folder (may be redirected to OneDrive); falls back to ~/Documents."""
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.c_wchar_p()
            import uuid
            guid = ctypes.create_string_buffer(uuid.UUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7").bytes_le, 16)  # FOLDERID_Documents
            if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(buf)) == 0 and buf.value:
                return Path(buf.value)
        except Exception:  # noqa: BLE001 — the fallback path is enough
            pass
    return Path.home() / "Documents"


def legacy(new, old):
    """Data written by older (Turkish-named) versions: if `old` exists and `new` does not, the packaged app renames it
    once; from source (a developer may have another instance running) the old name is simply kept in use."""
    if new.exists() or not old.exists():
        return new
    if FROZEN:
        try:
            old.rename(new)
            return new
        except OSError:
            pass
    return old


if FROZEN:
    # In the packaged app the data lives outside the app folder: updating/uninstalling does not take the courses along.
    DEFAULT_ROOT = legacy(documents_dir() / "libzie" / "materials", documents_dir() / "libzie" / "kaynaklar")
    _data = Path(os.environ.get("APPDATA") or Path.home()) / "libzie"
    SETTINGS_FILE = legacy(_data / "settings.json", _data / "ayarlar.json")
else:
    DEFAULT_ROOT = legacy(BASE / "materials", BASE / "kaynaklar")
    SETTINGS_FILE = legacy(BASE / "settings.json", BASE / "ayarlar.json")
# Older settings keys (Turkish) are read under their new names; they are written back with the new names.
LEGACY_KEYS = {"kaynak_klasoru": "materials_dir", "arka_planda": "run_in_background", "otomatik_guncelleme": "auto_update",
               "son_otomatik_deneme": "last_auto_attempt", "dil": "lang", "tray_ipucu": "tray_hint_shown"}
# Session key: kept only in the profile folder, which only this Windows user can read. The app/browser opens the address
# `/?k=<key>`, the server stores it in a session cookie (HttpOnly, SameSite=Strict, port-specific name); no request is
# processed without the key. The key is renewed at every server start (start()); a second launch connecting to an open
# libzie reads the current key the running instance wrote to the file and, before connecting, asks the instance to prove
# it knows the key (is_libzie).
SESSION_FILE = Path(os.environ.get("LIBZIE_SESSION_FILE") or Path(os.environ.get("APPDATA") or Path.home()) / "libzie" / "session.key")


def read_token():
    try:
        t = SESSION_FILE.read_text(encoding="utf-8").strip()
        return t if len(t) >= 32 else ""
    except OSError:
        return ""


def new_token():
    t = secrets.token_urlsafe(32)
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(t, encoding="utf-8")
    return t


TOKEN = read_token()  # for connecting to a running instance; renewed when a new server starts


def same(a, b):
    """Constant-time comparison; does not fail even on non-ASCII input."""
    return hmac.compare_digest(str(a).encode("utf-8", "replace"), str(b).encode("utf-8", "replace"))


def proof(nonce):
    return hmac.new(TOKEN.encode(), nonce.encode("utf-8", "replace"), "sha256").hexdigest() if TOKEN and nonce else ""


# Content policy for the app's own page: no eval (cuts font/eval based attacks like pdf.js CVE-2024-4367),
# no scripts/frames from other sites, and the only outbound destination is the weather service.
CSP_APP = ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
           "font-src 'self' data:; media-src 'self'; connect-src 'self' https://api.open-meteo.com https://geocoding-api.open-meteo.com; "
           "frame-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
# User files (except PDF) are served in a sandbox that cannot run scripts: even if HTML/SVG lands in the folder it cannot reach the app's API.
CSP_USER_FILE = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:"
# "Open in default app" only allows these extensions; executable/script types are never opened directly
OPEN_OK = {"pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "heic", "txt", "md", "rtf", "csv", "tsv",
           "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "pages", "numbers", "key", "epub", "djvu",
           "mp4", "m4v", "mov", "mkv", "webm", "avi", "mp3", "wav", "m4a", "flac", "ogg", "zip", "7z", "rar"}
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
MAX_JSON = 1 << 20
# Files uploaded to / renamed within the archive cannot be of a double-click-executable type (so it is not a drop point for malware)
BLOCKED_EXT = {"exe", "com", "scr", "bat", "cmd", "msi", "msp", "ps1", "psm1", "vbs", "vbe", "wsf", "wsh", "hta", "lnk", "url",
               "pif", "cpl", "reg", "scf", "inf", "dll", "sys", "msc", "gadget", "appref-ms"}


def protected_dirs():
    """Locations that cannot be written to: system folders, Startup folders, libzie's own installation and settings."""
    env = os.environ.get
    out = []
    for var in ("WINDIR", "SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432", "ProgramData"):
        if env(var):
            out.append(Path(env(var)))
    for base, tail in (("APPDATA", "Microsoft/Windows/Start Menu"), ("ProgramData", "Microsoft/Windows/Start Menu"),
                       ("APPDATA", "libzie"), ("LOCALAPPDATA", "Programs"), ("USERPROFILE", ".ssh")):
        if env(base):
            out.append(Path(env(base)) / tail)
    return [p.resolve() for p in out]


PROTECTED = protected_dirs()


def check_write(p):
    p = Path(p).resolve()
    for d in PROTECTED:
        if p == d or d in p.parents:
            raise AppError("err.write_blocked")


def check_ext(name):
    if Path(name).suffix.lower().lstrip(".") in BLOCKED_EXT:
        raise AppError("err.ext_blocked")

# Desktop app (app.py): staying in the background when the window closes and bringing the window forward on a second launch
DESKTOP = False        # becomes True when app.py has set up the tray successfully
DESKTOP_HOOKS = {}     # {"show": show the window}


def tray_enabled():
    """Keep running in the background (system tray) when the window is closed (on by default)."""
    return bool(read_settings().get("run_in_background", True))


ENV_ROOT = os.environ.get("LIBZIE_MATERIALS_DIR", "")  # if set, it cannot be changed from the UI


def read_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return {}
        for old, new in LEGACY_KEYS.items():
            if old in data and new not in data:
                data[new] = data[old]
            data.pop(old, None)
        return data
    except (OSError, ValueError):
        return {}


def write_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=1), encoding="utf-8")


def parse_dir(text):
    """Turns the path the user typed into a Path (including the quotes from "Copy as path")."""
    return Path(os.path.expandvars(text.strip().strip("\"'"))).expanduser()


def pick_root():
    """Materials folder: LIBZIE_MATERIALS_DIR environment variable > settings.json > ./materials.
    If the configured folder is missing (e.g. Drive not mounted) the default is used and a warning is returned."""
    custom = ENV_ROOT or str(read_settings().get("materials_dir") or "")
    warning = None
    if custom.strip():
        p = parse_dir(custom)
        if p.is_dir():
            return p.resolve(), ""
        warning = ("warn.root_missing", {"path": str(p)})
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_ROOT.resolve(), warning


ROOT = TRASH = COLOR_FILE = ICON_FILE = None
ROOT_WARNING = None  # (id, variables) or None


def set_root(root, warning=None):
    global ROOT, TRASH, COLOR_FILE, ICON_FILE, ROOT_WARNING
    ROOT = root
    TRASH = legacy(root / ".trash", root / ".silinenler")
    COLOR_FILE = legacy(root / ".colors.json", root / ".renkler.json")
    ICON_FILE = legacy(root / ".icons.json", root / ".ikonlar.json")
    ROOT_WARNING = warning


set_root(*pick_root())


def safe(rel_path):
    """Turns a relative path into an absolute one under the materials folder; refuses to leave it."""
    p = (ROOT / (rel_path or "")).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise AppError("err.bad_path")
    return p


def rel(p):
    return p.relative_to(ROOT).as_posix()


def unique(p):
    if not p.exists():
        return p
    i = 2
    while True:
        candidate = p.with_name(f"{p.stem} ({i}){p.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def clean_name(name):
    name = Path(str(name).replace("\\", "/")).name.strip()
    if (not name or name.startswith(".") or name.endswith(".") or any(c in name for c in '<>:"|?*')
            or any(ord(c) < 32 for c in name) or name.split(".")[0].strip().lower() in RESERVED):
        raise AppError("err.bad_name")
    return name


def load_colors():
    try:
        data = json.loads(COLOR_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_colors(colors):
    COLOR_FILE.write_text(json.dumps(colors, ensure_ascii=False, indent=1), encoding="utf-8")


def load_icons():
    """The chosen icons of the courses ({course name: icon id}); if none is chosen the UI picks a default by order."""
    try:
        data = json.loads(ICON_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_icons(icons):
    ICON_FILE.write_text(json.dumps(icons, ensure_ascii=False, indent=1), encoding="utf-8")


def move_course_meta(old, new):
    """A course's color and icon are updated in the record files too when the course is renamed/moved/deleted (new=None: delete)."""
    for load, save in ((load_colors, save_colors), (load_icons, save_icons)):
        data = load()
        value = data.pop(old, None)
        if value is not None:
            if new is not None:
                data[new] = value
            save(data)


def tree(d):
    folders, files = [], []
    for e in sorted(d.iterdir(), key=lambda e: e.name.lower()):
        if e.name.startswith("."):
            continue
        if e.is_dir():
            folders.append(tree(e))
        elif e.is_file():
            st = e.stat()
            files.append({
                "name": e.name,
                "path": rel(e),
                "size": st.st_size,
                "mtime": st.st_mtime,
                "ext": e.suffix.lower().lstrip("."),
            })
    return {
        "name": "" if d == ROOT else d.name,
        "path": "" if d == ROOT else rel(d),
        "folders": folders,
        "files": files,
    }


def open_with_system(p):
    if p.is_file() and p.suffix.lower().lstrip(".") not in OPEN_OK:
        raise AppError("err.open_blocked")
    if sys.platform == "win32":
        os.startfile(p)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p)])


def reveal(p):
    if sys.platform == "win32":
        if p.is_dir():
            os.startfile(p)
        elif '"' in str(p):
            raise AppError("err.bad_path")
        else:
            subprocess.Popen(f'explorer /select,"{p}"')
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p if p.is_dir() else p.parent)])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def hosts(self):
        port = self.server.server_address[1]
        return {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}

    def deny(self, code, key):
        text = " / ".join(dict.fromkeys(i18n.msg(key, lang) for lang in (i18n.DEFAULT, "tr")))  # "English / Türkçe"
        data = f"<!doctype html><meta charset=utf-8><title>libzie</title><p>{text}</p>".encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def cookie_name(self):
        return f"libzie_k_{self.server.server_address[1]}"  # cookies do not separate ports: instances must not overwrite each other's cookie

    def has_token(self):
        name = self.cookie_name()
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name and TOKEN and same(v, TOKEN):
                return True
        return False

    def guard(self, post):
        """Does the request come from this app's own page? If not, sends the response and returns False.
        The Host check stops DNS rebinding; Sec-Fetch-Site/Origin and the custom header stop requests from other sites (CSRF)."""
        if self.headers.get("Host", "") not in self.hosts():
            self.deny(403, "http.bad_request")
            return False
        site = self.headers.get("Sec-Fetch-Site")
        if site and site not in ("same-origin", "none"):
            self.deny(403, "http.cross_site")
            return False
        if post:
            origin = self.headers.get("Origin")
            if (origin and origin not in {f"http://{h}" for h in self.hosts()}) or self.headers.get("X-Libzie") != "1":
                self.deny(403, "http.cross_site")
                return False
        return True

    def authorized(self, path, query):
        """Session key: if `/?k=...` arrives a cookie is set and the client is redirected to the clean address; a request without the cookie gets 401."""
        if path == "/" and TOKEN and same((query.get("k") or [""])[0], TOKEN):
            self.send_response(302)
            self.send_header("Set-Cookie", f"{self.cookie_name()}={TOKEN}; Path=/; HttpOnly; SameSite=Strict")
            self.send_header("Location", "/")
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return False
        if not self.has_token():
            self.deny(401, "http.no_access")
            return False
        return True

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def send_index(self):
        """App page: the language dictionaries (static/lang/*.json) are embedded in the page, so there is no extra request or delay."""
        page = ((STATIC / "index.html").read_text(encoding="utf-8").replace("/*I18N*/", i18n.dict_json(), 1)
                .replace("/*THEMES*/", themes.css(), 1).replace("/*THEMES_JSON*/", json.dumps(themes.meta(), separators=(",", ":")), 1))
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP_APP)
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, p, cache="no-cache", user=False):
        if not p.is_file():
            return self.send_error(404)
        if p.suffix == ".js":  # the Windows registry sometimes gives .js as text/plain; the worker needs the right type
            ctype = "text/javascript; charset=utf-8"
        else:
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            if ctype.startswith("text/"):
                ctype += "; charset=utf-8"
        size = p.stat().st_size
        start, end, status = 0, size - 1, 200
        # Single-range "Range" support: so pdf.js and the browser's PDF viewer can read big files in chunks
        rng = self.headers.get("Range", "")
        if rng.startswith("bytes=") and "," not in rng:
            try:
                a, b = rng[6:].split("-", 1)
                if a:
                    start = int(a)
                    end = min(int(b), size - 1) if b else size - 1
                else:
                    start = max(0, size - int(b))
                if start > end or start >= size:
                    raise ValueError
                status = 206
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(max(0, end - start + 1)))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Disposition", f"inline; filename*=UTF-8''{quote(p.name)}")
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Referrer-Policy", "no-referrer")
        if user:
            if p.suffix.lower() != ".pdf":  # Chrome's PDF viewer does not work under the sandbox policy; scripts in a PDF cannot reach the page
                self.send_header("Content-Security-Policy", CSP_USER_FILE)
        elif p == STATIC / "index.html":
            self.send_header("Content-Security-Policy", CSP_APP)
            self.send_header("X-Frame-Options", "DENY")
        elif p.suffix == ".js":
            self.send_header("Content-Security-Policy", "script-src 'self'")  # no eval in the pdf.js worker either
        self.end_headers()
        with open(p, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = f.read(min(1 << 20, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_GET(self):
        u = urlparse(self.path)
        path = unquote(u.path)
        try:
            if not self.guard(False):
                return
            if path == "/api/ping":
                # For checking whether another libzie instance is running (no key needed). It answers the random number with an
                # HMAC under the key: before sending the key the client can verify the other side really is this user's libzie.
                nonce = (parse_qs(u.query).get("n") or [""])[0][:64]
                return self.send_json({"app": "libzie", "proof": proof(nonce)})
            if not self.authorized(path, parse_qs(u.query)):
                return
            if path in ("/", "/index.html"):
                return self.send_index()
            if path == "/api/tree":
                data = tree(ROOT)
                data["colors"] = load_colors()
                data["icons"] = load_icons()
                data["warning"] = i18n.msg(ROOT_WARNING[0], **ROOT_WARNING[1]) if ROOT_WARNING else ""
                data["warning_code"] = ROOT_WARNING[0] if ROOT_WARNING else ""
                data["warning_vars"] = ROOT_WARNING[1] if ROOT_WARNING else {}
                return self.send_json(data)
            if path == "/api/settings":
                return self.send_json({
                    "root": str(ROOT),
                    "default": str(DEFAULT_ROOT.resolve()),
                    "configured": ENV_ROOT or str(read_settings().get("materials_dir") or ""),
                    "locked": bool(ENV_ROOT),
                    "version": updater.VERSION,
                    "update_kind": updater.kind(),
                    "auto_update": bool(read_settings().get("auto_update")),
                    "desktop": DESKTOP,
                    "tray": tray_enabled(),
                })
            if path == "/api/update/check":
                return self.send_json(updater.check())
            if path == "/api/update/status":
                return self.send_json(updater.status())
            if path.startswith("/files/"):
                return self.send_file(safe(path[len("/files/"):]), user=True)
            if path.startswith("/vendor/"):
                name = path[len("/vendor/"):]
                if not name or "/" in name or "\\" in name or name.startswith("."):
                    raise AppError("err.bad_path")
                return self.send_file(STATIC / "vendor" / name, cache="public, max-age=86400")
            if path == "/api/preview":
                # While typing a path in Settings: "this folder has N courses, M files" (read-only)
                text = (parse_qs(urlparse(self.path).query).get("path") or [""])[0]
                folder = parse_dir(text) if text.strip() else DEFAULT_ROOT
                try:
                    if not folder.is_dir():
                        return self.send_json({"exists": False})
                    courses = sum(1 for e in folder.iterdir() if e.is_dir() and not e.name.startswith("."))
                    files, capped = 0, False
                    for _, dirs, names in os.walk(folder):
                        dirs[:] = [d for d in dirs if not d.startswith(".")]
                        files += sum(1 for n in names if not n.startswith("."))
                        if files >= 20000:
                            capped = True
                            break
                except OSError:
                    return self.send_json({"exists": False})
                return self.send_json({"exists": True, "courses": courses, "files": files, "capped": capped})
            self.send_error(404)
        except AppError as e:
            if e.code == "err.bad_path":
                self.send_error(403)
            else:
                self.send_json(err_json(e), 400)
        except ValueError:
            self.send_error(403)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001 — pass the error on to the UI
            self.send_json(err_json(e), 400)

    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if not self.guard(True) or not self.authorized(u.path, {}):
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
            except ValueError:
                length = -1
            if length < 0:
                raise AppError("err.bad_request")
            if u.path == "/api/upload":
                d = safe(q.get("dir", ""))
                check_write(d)
                name = clean_name(q.get("name", ""))
                check_ext(name)
                d.mkdir(parents=True, exist_ok=True)
                target = unique(d / name)
                remaining = length
                with open(target, "wb") as f:
                    while remaining > 0:
                        chunk = self.rfile.read(min(1 << 20, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                return self.send_json({"path": rel(target)})

            if length > MAX_JSON:
                raise AppError("err.too_large")
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise AppError("err.bad_request")

            if u.path == "/api/mkdir":
                parent = safe(body.get("dir", ""))
                check_write(parent)
                p = parent / clean_name(body.get("name", ""))
                if p.exists():
                    raise AppError("err.exists")
                p.mkdir(parents=True)
                return self.send_json({"path": rel(p)})

            if u.path == "/api/move":
                src = safe(body["from"])
                dst_dir = safe(body.get("dir", ""))
                dst = dst_dir / clean_name(body.get("name") or src.name)
                check_write(dst_dir)
                if dst.suffix.lower() != src.suffix.lower():
                    check_ext(dst.name)  # renaming a file into an executable type is blocked too
                if src == ROOT or not src.exists():
                    raise AppError("err.not_found")
                if src.is_dir() and (dst_dir == src or src in dst_dir.parents):
                    raise AppError("err.move_into_self")
                if dst.exists() and not os.path.samefile(src, dst):
                    raise AppError("err.dest_exists")
                dst_dir.mkdir(parents=True, exist_ok=True)
                os.rename(src, dst)
                if src.parent == ROOT:
                    move_course_meta(src.name, dst.name if dst.parent == ROOT else None)
                return self.send_json({"path": rel(dst)})

            if u.path == "/api/settings/general":
                # General tab: background running and UI language (also kept on the server so the tray menu knows the language)
                settings = read_settings()
                if "tray" in body:
                    settings["run_in_background"] = bool(body["tray"])
                if "lang" in body:
                    lang = str(body["lang"])
                    if lang != "auto" and lang not in i18n.dictionary():
                        raise AppError("err.bad_request")
                    settings["lang"] = lang
                write_settings(settings)
                return self.send_json({"tray": tray_enabled()})

            if u.path == "/api/desktop/show":
                show = DESKTOP_HOOKS.get("show")
                if show:
                    show()
                return self.send_json({"ok": bool(show)})

            if u.path == "/api/update/settings":
                settings = read_settings()
                settings["auto_update"] = bool(body.get("auto"))
                write_settings(settings)
                return self.send_json({"auto": settings["auto_update"]})

            if u.path == "/api/update/apply":
                if body.get("auto"):
                    # Automatic update on startup tries each version only once: if it fails it does not loop on every launch
                    latest = updater.check()["latest"]
                    settings = read_settings()
                    if settings.get("last_auto_attempt") == latest:
                        raise updater.UpdateError("upd.err.auto_tried")
                    settings["last_auto_attempt"] = latest
                    write_settings(settings)
                updater.start_apply()
                return self.send_json({"ok": True})

            if u.path == "/api/settings":
                if ENV_ROOT:
                    raise AppError("err.root_locked")
                text = str(body.get("materials_dir") or "").strip()
                settings = read_settings()
                if text:
                    p = parse_dir(text)
                    if not p.is_dir():
                        raise AppError("err.folder_missing", path=str(p))
                    settings["materials_dir"] = str(p.resolve())
                    new_root = p.resolve()
                else:
                    settings.pop("materials_dir", None)
                    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
                    new_root = DEFAULT_ROOT.resolve()
                write_settings(settings)
                set_root(new_root)
                return self.send_json({"root": str(ROOT)})

            if u.path == "/api/color":
                course = safe(body["path"])
                if course.parent != ROOT or not course.is_dir():
                    raise AppError("err.color_course_only")
                colors = load_colors()
                if body.get("color"):
                    if not re.fullmatch(r"#[0-9a-fA-F]{3,8}", str(body["color"])):
                        raise AppError("err.bad_color")
                    colors[course.name] = str(body["color"])
                else:
                    colors.pop(course.name, None)
                save_colors(colors)
                return self.send_json({"ok": True})

            if u.path == "/api/icon":
                course = safe(body["path"])
                if course.parent != ROOT or not course.is_dir():
                    raise AppError("err.icon_course_only")
                icon = str(body.get("icon") or "")
                if icon and not re.fullmatch(r"[a-z0-9-]{1,24}", icon):
                    raise AppError("err.bad_icon")
                icons = load_icons()
                if icon:
                    icons[course.name] = icon
                else:
                    icons.pop(course.name, None)
                save_icons(icons)
                return self.send_json({"ok": True})

            if u.path == "/api/delete":
                src = safe(body["path"])
                if src == ROOT or not src.exists():
                    raise AppError("err.not_found")
                if src.parent == ROOT:
                    move_course_meta(src.name, None)
                TRASH.mkdir(exist_ok=True)
                trashed = unique(TRASH / src.name)
                shutil.move(str(src), str(trashed))
                return self.send_json({"ok": True, "trash": trashed.name})

            if u.path == "/api/restore":
                # "Undo": moves the item in the trash folder back to its old path (" (2)" is appended on a name clash)
                src = TRASH / clean_name(body["trash"])
                if not src.exists():
                    raise AppError("err.not_found")
                dst = safe(body["to"])
                check_write(dst.parent)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst = unique(dst)
                shutil.move(str(src), str(dst))
                return self.send_json({"path": rel(dst)})

            if u.path == "/api/open":
                open_with_system(safe(body["path"]))
                return self.send_json({"ok": True})

            if u.path == "/api/reveal":
                reveal(safe(body.get("path", "")))
                return self.send_json({"ok": True})

            self.send_error(404)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:  # noqa: BLE001 — pass the error on to the UI
            self.send_json(err_json(e), 400)


class Server(ThreadingHTTPServer):
    """On Windows, SO_REUSEADDR lets another program bind the same port and steal connections;
    SO_EXCLUSIVEADDRUSE prevents that (if the port is taken, binding raises OSError and the next port is tried)."""
    allow_reuse_address = False

    def server_bind(self):
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def is_libzie(port):
    """Is this user's libzie running on this port? A listener that does not prove with HMAC that it knows the key is not trusted
    (otherwise another account could occupy the port and receive the session key along with the address)."""
    if not TOKEN:
        return False
    nonce = secrets.token_hex(16)
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/ping?n={nonce}", timeout=1) as r:
            data = json.loads(r.read())
        return data.get("app") == "libzie" and same(data.get("proof", ""), proof(nonce))
    except (OSError, ValueError, AttributeError):
        return False


def request_show(url):
    """If another libzie desktop app is already running (its window may be hidden), brings it to the front. True on success."""
    port = url.rsplit(":", 1)[1]
    req = urllib.request.Request(f"{url}/api/desktop/show", data=b"{}", method="POST", headers={
        "Content-Type": "application/json", "X-Libzie": "1", "Origin": url, "Cookie": f"libzie_k_{port}={TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return json.loads(r.read()).get("ok") is True
    except (OSError, ValueError):
        return False


def ui_lang():
    """Tray menu language: the language the user chose in libzie, or the Windows UI language if it is 'auto'."""
    import tray
    pref = str(read_settings().get("lang") or "auto")
    return pref if pref in i18n.dictionary() else tray.system_lang()


def launch_url(url):
    """The address the app window/browser opens: carries the session key once; the server sets a cookie and cleans the address."""
    return f"{url}/?k={TOKEN}"


def start():
    """Connects to a running libzie if there is one, otherwise starts a server on the first free port. Returns (url, server|None);
    the server exists only if this process started it (the caller is responsible for serve_forever and shutting down)."""
    for port in range(PORT, PORT + PORT_TRIES):
        if is_libzie(port):
            return f"http://{HOST}:{port}", None
        try:
            srv = Server((HOST, port), Handler)
        except OSError:
            continue
        global TOKEN
        TOKEN = new_token()  # new key at every start: a captured old key is useless
        return f"http://{HOST}:{port}", srv
    raise SystemExit(f"The ports starting at {PORT} are all in use; pick another port with the PORT environment variable.")


def main():
    url, server = start()
    if server is None:
        print(f"libzie is already running: {url}")
        if "--no-browser" not in sys.argv:
            webbrowser.open(launch_url(url))
        return
    print(f"libzie is running: {url}")
    print(f"Files: {ROOT}")
    if ROOT_WARNING:
        print(f"WARNING: {i18n.msg(ROOT_WARNING[0], **ROOT_WARNING[1])}")
    print("To stop, close this window or press Ctrl+C.")
    print(f"To open in the browser (this address is private to you, do not share it): {launch_url(url)}")
    if "--no-browser" not in sys.argv:
        webbrowser.open(launch_url(url))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
