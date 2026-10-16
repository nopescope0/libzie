"""libzie — ders kaynaklarını (PDF, slayt vb.) yerel olarak düzenlemek için küçük bir sunucu.

Yalnızca Python standart kütüphanesini kullanır. Dosyalar `kaynaklar/` klasöründe tutulur;
klasör yapısı doğrudan diskteki klasör yapısıdır (Gezgin'den de eklenebilir).
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

import guncelleme
import i18n
from i18n import AppError, err_json

FROZEN = getattr(sys, "frozen", False)  # PyInstaller ile paketlenmiş uygulama
BASE = Path(__file__).resolve().parent
STATIC = Path(getattr(sys, "_MEIPASS", BASE)) / "static"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", 8765))
PORT_TRIES = 1 if "PORT" in os.environ else 11  # PORT verilmediyse 8765'ten başlayıp ilk boş portu kullan


def documents_dir():
    """Kullanıcının Belgeler klasörü (OneDrive'a yönlendirilmiş olabilir); bulunamazsa ~/Documents."""
    if sys.platform == "win32":
        try:
            import ctypes
            buf = ctypes.c_wchar_p()
            import uuid
            guid = ctypes.create_string_buffer(uuid.UUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7").bytes_le, 16)  # FOLDERID_Documents
            if ctypes.windll.shell32.SHGetKnownFolderPath(guid, 0, None, ctypes.byref(buf)) == 0 and buf.value:
                return Path(buf.value)
        except Exception:  # noqa: BLE001 — yedek yol yeter
            pass
    return Path.home() / "Documents"


if FROZEN:
    # Paketlenmiş uygulamada veri uygulama klasörünün dışında durur: güncelleme/silme dersleri götürmez.
    DEFAULT_ROOT = documents_dir() / "libzie" / "kaynaklar"
    SETTINGS_FILE = Path(os.environ.get("APPDATA") or Path.home()) / "libzie" / "ayarlar.json"
else:
    DEFAULT_ROOT = BASE / "kaynaklar"
    SETTINGS_FILE = BASE / "ayarlar.json"
# Oturum anahtarı: yalnızca bu Windows kullanıcısının okuyabildiği profil klasöründe durur. Uygulama/tarayıcı adresi
# `/?k=<anahtar>` ile açar, sunucu bunu oturum çerezinde (HttpOnly, SameSite=Strict, porta özgü ad) saklar; anahtarsız hiçbir
# istek işlenmez. Anahtar her sunucu başlangıcında yenilenir (start()); açık libzie'ye ikinci bir başlatma, çalışan örneğin
# dosyaya yazdığı güncel anahtarı okuyup bağlanır ve bağlanmadan önce örneğin anahtarı bildiğini kanıtlamasını ister (is_libzie).
SESSION_FILE = Path(os.environ.get("LIBZIE_OTURUM_DOSYASI") or Path(os.environ.get("APPDATA") or Path.home()) / "libzie" / "oturum.key")


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


TOKEN = read_token()  # çalışan bir örneğe bağlanmak için; yeni sunucu açılırken yenilenir


def same(a, b):
    """Sabit zamanlı karşılaştırma; ASCII dışı girdide bile hata vermez."""
    return hmac.compare_digest(str(a).encode("utf-8", "replace"), str(b).encode("utf-8", "replace"))


def proof(nonce):
    return hmac.new(TOKEN.encode(), nonce.encode("utf-8", "replace"), "sha256").hexdigest() if TOKEN and nonce else ""


# Uygulamanın kendi sayfası için içerik politikası: eval yok (pdf.js CVE-2024-4367 gibi font/eval tabanlı saldırıları keser),
# başka sitelerden betik/çerçeve yok, dışarıya yalnızca hava durumu servisi.
CSP_APP = ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
           "font-src 'self' data:; media-src 'self'; connect-src 'self' https://api.open-meteo.com https://geocoding-api.open-meteo.com; "
           "frame-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
# Kullanıcı dosyaları (PDF hariç) betik çalıştıramayan bir kum havuzunda sunulur: içine HTML/SVG düşse bile uygulamanın API'sine erişemez.
CSP_USER_FILE = "sandbox; default-src 'none'; style-src 'unsafe-inline'; img-src data:"
# "Varsayılan uygulamada aç" yalnızca bu uzantılara izin verir; çalıştırılabilir/betik türleri hiçbir zaman doğrudan açılmaz
OPEN_OK = {"pdf", "png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "heic", "txt", "md", "rtf", "csv", "tsv",
           "doc", "docx", "xls", "xlsx", "ppt", "pptx", "odt", "ods", "odp", "pages", "numbers", "key", "epub", "djvu",
           "mp4", "m4v", "mov", "mkv", "webm", "avi", "mp3", "wav", "m4a", "flac", "ogg", "zip", "7z", "rar"}
RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
MAX_JSON = 1 << 20
# Arşive yüklenen/yeniden adlandırılan dosyalar çift tıkla çalışabilen türde olamaz (indirme-bırakma noktası olmasın)
BLOCKED_EXT = {"exe", "com", "scr", "bat", "cmd", "msi", "msp", "ps1", "psm1", "vbs", "vbe", "wsf", "wsh", "hta", "lnk", "url",
               "pif", "cpl", "reg", "scf", "inf", "dll", "sys", "msc", "gadget", "appref-ms"}


def protected_dirs():
    """Yazılamayan konumlar: sistem klasörleri, Başlangıç klasörleri, libzie'nin kendi kurulumu ve ayarları."""
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

ENV_ROOT = os.environ.get("KAYNAK_KLASORU", "")  # ayarlanmışsa arayüzden değiştirilemez


def read_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_settings(settings):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=1), encoding="utf-8")


def parse_dir(text):
    """Kullanıcının yazdığı yolu Path'e çevirir ("Yol olarak kopyala" tırnakları dahil)."""
    return Path(os.path.expandvars(text.strip().strip("\"'"))).expanduser()


def pick_root():
    """Kaynak klasörü: KAYNAK_KLASORU ortam değişkeni > ayarlar.json > ./kaynaklar.
    Ayarlı klasör yoksa (ör. Drive kapalı) varsayılana dönülür ve uyarı verilir."""
    custom = ENV_ROOT or str(read_settings().get("kaynak_klasoru") or "")
    warning = None
    if custom.strip():
        p = parse_dir(custom)
        if p.is_dir():
            return p.resolve(), ""
        warning = ("warn.root_missing", {"path": str(p)})
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_ROOT.resolve(), warning


ROOT = TRASH = COLOR_FILE = ICON_FILE = None
ROOT_WARNING = None  # (kimlik, değişkenler) ya da None


def set_root(root, warning=None):
    global ROOT, TRASH, COLOR_FILE, ICON_FILE, ROOT_WARNING
    ROOT, TRASH, COLOR_FILE, ICON_FILE = root, root / ".silinenler", root / ".renkler.json", root / ".ikonlar.json"
    ROOT_WARNING = warning


set_root(*pick_root())


def safe(rel_path):
    """Göreli yolu kaynaklar/ altında mutlak yola çevirir; dışarı çıkmaya izin vermez."""
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
    """Derslerin seçili ikonları ({ders adı: ikon kimliği}); seçilmemişse arayüz sıraya göre varsayılanı verir."""
    try:
        data = json.loads(ICON_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_icons(icons):
    ICON_FILE.write_text(json.dumps(icons, ensure_ascii=False, indent=1), encoding="utf-8")


def move_course_meta(old, new):
    """Dersin rengi ve ikonu, ders yeniden adlandırılınca/taşınınca/silinince kayıt dosyalarında da güncellenir (new=None: sil)."""
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
        text = " / ".join(dict.fromkeys(i18n.msg(key, lang) for lang in (i18n.DEFAULT, "en")))  # "Türkçe / English"
        data = f"<!doctype html><meta charset=utf-8><title>libzie</title><p>{text}</p>".encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def cookie_name(self):
        return f"libzie_k_{self.server.server_address[1]}"  # çerezler port ayırmaz: örnekler birbirinin çerezini ezmesin

    def has_token(self):
        name = self.cookie_name()
        for part in self.headers.get("Cookie", "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name and TOKEN and same(v, TOKEN):
                return True
        return False

    def guard(self, post):
        """İstek bu uygulamanın kendi sayfasından mı geliyor? Değilse yanıtı verir ve False döner.
        Host denetimi DNS rebinding'i, Sec-Fetch-Site/Origin ve özel başlık başka sitelerden gelen istekleri (CSRF) keser."""
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
        """Oturum anahtarı: `/?k=...` ile gelinirse çerez verilip temiz adrese yönlendirilir; çerezsiz istek 401 alır."""
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
        """Uygulama sayfası: dil sözlükleri (static/lang/*.json) sayfaya gömülür, ek istek ve gecikme olmaz."""
        page = (STATIC / "index.html").read_text(encoding="utf-8").replace("/*I18N*/", i18n.dict_json(), 1)
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
        if p.suffix == ".js":  # Windows kayıt defteri .js'i bazen text/plain verir; worker için gerekli
            ctype = "text/javascript; charset=utf-8"
        else:
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            if ctype.startswith("text/"):
                ctype += "; charset=utf-8"
        size = p.stat().st_size
        start, end, status = 0, size - 1, 200
        # Tek aralıklı "Range" desteği: pdf.js ve tarayıcının PDF görüntüleyicisi büyük dosyaları parça parça okuyabilsin
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
            if p.suffix.lower() != ".pdf":  # Chrome'un PDF görüntüleyicisi kum havuzu ilkesiyle çalışmaz; PDF'te betik sayfaya erişemez
                self.send_header("Content-Security-Policy", CSP_USER_FILE)
        elif p == STATIC / "index.html":
            self.send_header("Content-Security-Policy", CSP_APP)
            self.send_header("X-Frame-Options", "DENY")
        elif p.suffix == ".js":
            self.send_header("Content-Security-Policy", "script-src 'self'")  # pdf.js çalışanında da eval yok
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
                # Başka bir libzie örneği çalışıyor mu diye bakmak için (anahtarsız). Gelen rastgele sayıya anahtarla HMAC döner:
                # istemci, anahtarı göndermeden önce karşıdakinin gerçekten bu kullanıcının libzie'si olduğunu doğrulayabilir.
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
                    "configured": ENV_ROOT or str(read_settings().get("kaynak_klasoru") or ""),
                    "locked": bool(ENV_ROOT),
                    "version": guncelleme.VERSION,
                    "update_kind": guncelleme.kind(),
                    "auto_update": bool(read_settings().get("otomatik_guncelleme")),
                })
            if path == "/api/update/check":
                return self.send_json(guncelleme.check())
            if path == "/api/update/status":
                return self.send_json(guncelleme.status())
            if path.startswith("/files/"):
                return self.send_file(safe(path[len("/files/"):]), user=True)
            if path.startswith("/vendor/"):
                name = path[len("/vendor/"):]
                if not name or "/" in name or "\\" in name or name.startswith("."):
                    raise AppError("err.bad_path")
                return self.send_file(STATIC / "vendor" / name, cache="public, max-age=86400")
            if path == "/api/preview":
                # Ayarlar'da yol yazılırken: "bu klasörde N ders, M dosya var" (yalnızca okur)
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
        except Exception as e:  # noqa: BLE001 — hatayı arayüze ilet
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
                    check_ext(dst.name)  # yeniden adlandırarak yürütülebilir türe çevirmek de engellenir
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

            if u.path == "/api/update/settings":
                settings = read_settings()
                settings["otomatik_guncelleme"] = bool(body.get("auto"))
                write_settings(settings)
                return self.send_json({"auto": settings["otomatik_guncelleme"]})

            if u.path == "/api/update/apply":
                if body.get("auto"):
                    # Açılışta otomatik güncelleme her sürümü yalnızca bir kez dener: başarısız olursa her açılışta döngüye girmez
                    latest = guncelleme.check()["latest"]
                    settings = read_settings()
                    if settings.get("son_otomatik_deneme") == latest:
                        raise guncelleme.UpdateError("upd.err.auto_tried")
                    settings["son_otomatik_deneme"] = latest
                    write_settings(settings)
                guncelleme.start_apply()
                return self.send_json({"ok": True})

            if u.path == "/api/settings":
                if ENV_ROOT:
                    raise AppError("err.root_locked")
                text = str(body.get("kaynak_klasoru") or "").strip()
                settings = read_settings()
                if text:
                    p = parse_dir(text)
                    if not p.is_dir():
                        raise AppError("err.folder_missing", path=str(p))
                    settings["kaynak_klasoru"] = str(p.resolve())
                    new_root = p.resolve()
                else:
                    settings.pop("kaynak_klasoru", None)
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
                # "Geri al": .silinenler içindeki öğeyi eski yoluna döndürür (ad çakışırsa " (2)" eklenir)
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
        except Exception as e:  # noqa: BLE001 — hatayı arayüze ilet
            self.send_json(err_json(e), 400)


class Server(ThreadingHTTPServer):
    """Windows'ta SO_REUSEADDR başka bir programın aynı porta ortak bağlanıp bağlantıları çalmasına izin verir;
    SO_EXCLUSIVEADDRUSE bunu engeller (port doluysa bağlanma OSError verir ve sıradaki port denenir)."""
    allow_reuse_address = False

    def server_bind(self):
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def is_libzie(port):
    """Bu portta bu kullanıcının libzie'si mi çalışıyor? Anahtarı bildiğini HMAC ile kanıtlamayan dinleyiciye güvenilmez
    (aksi halde başka bir hesap portu işgal edip adresle birlikte oturum anahtarını alabilirdi)."""
    if not TOKEN:
        return False
    nonce = secrets.token_hex(16)
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/ping?n={nonce}", timeout=1) as r:
            data = json.loads(r.read())
        return data.get("app") == "libzie" and same(data.get("proof", ""), proof(nonce))
    except (OSError, ValueError, AttributeError):
        return False


def launch_url(url):
    """Uygulama penceresinin/tarayıcının açacağı adres: oturum anahtarını bir kez taşır, sunucu çerez verip adresi temizler."""
    return f"{url}/?k={TOKEN}"


def start():
    """Çalışan libzie varsa ona bağlanır, yoksa boş ilk portta sunucu açar. (url, sunucu|None) döner;
    sunucu yalnızca bu süreç açtıysa vardır (çağıran serve_forever'dan ve kapatmaktan sorumlu)."""
    for port in range(PORT, PORT + PORT_TRIES):
        if is_libzie(port):
            return f"http://{HOST}:{port}", None
        try:
            srv = Server((HOST, port), Handler)
        except OSError:
            continue
        global TOKEN
        TOKEN = new_token()  # her başlangıçta yeni anahtar: ele geçirilmiş eski anahtar işe yaramaz
        return f"http://{HOST}:{port}", srv
    raise SystemExit(f"{PORT} portundan başlayan portlar dolu; PORT ortam değişkeniyle başka bir port seçin.")


def main():
    url, server = start()
    if server is None:
        print(f"libzie zaten çalışıyor: {url}")
        if "--no-browser" not in sys.argv:
            webbrowser.open(launch_url(url))
        return
    print(f"libzie çalışıyor: {url}")
    print(f"Dosyalar: {ROOT}")
    if ROOT_WARNING:
        print(f"UYARI: {i18n.msg(ROOT_WARNING[0], **ROOT_WARNING[1])}")
    print("Kapatmak için bu pencereyi kapatın veya Ctrl+C'ye basın.")
    print(f"Tarayıcıda açmak için (bu adres sana özel, paylaşma): {launch_url(url)}")
    if "--no-browser" not in sys.argv:
        webbrowser.open(launch_url(url))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
