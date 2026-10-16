"""libzie — ders kaynaklarını (PDF, slayt vb.) yerel olarak düzenlemek için küçük bir sunucu.

Yalnızca Python standart kütüphanesini kullanır. Dosyalar `kaynaklar/` klasöründe tutulur;
klasör yapısı doğrudan diskteki klasör yapısıdır (Gezgin'den de eklenebilir).
"""
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import guncelleme

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
    warning = ""
    if custom.strip():
        p = parse_dir(custom)
        if p.is_dir():
            return p.resolve(), ""
        warning = f"Ayarlanan kaynak klasörü bulunamadı: {p} — varsayılan klasör gösteriliyor."
    DEFAULT_ROOT.mkdir(parents=True, exist_ok=True)
    return DEFAULT_ROOT.resolve(), warning


ROOT = TRASH = COLOR_FILE = ICON_FILE = None
ROOT_WARNING = ""


def set_root(root, warning=""):
    global ROOT, TRASH, COLOR_FILE, ICON_FILE, ROOT_WARNING
    ROOT, TRASH, COLOR_FILE, ICON_FILE = root, root / ".silinenler", root / ".renkler.json", root / ".ikonlar.json"
    ROOT_WARNING = warning


set_root(*pick_root())


def safe(rel_path):
    """Göreli yolu kaynaklar/ altında mutlak yola çevirir; dışarı çıkmaya izin vermez."""
    p = (ROOT / (rel_path or "")).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError("Geçersiz yol")
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
    if not name or name.startswith(".") or any(c in name for c in '<>:"|?*'):
        raise ValueError("Geçersiz ad")
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
        else:
            subprocess.Popen(f'explorer /select,"{p}"')
    elif sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(p)])
    else:
        subprocess.Popen(["xdg-open", str(p if p.is_dir() else p.parent)])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, p, cache="no-cache"):
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
        path = unquote(urlparse(self.path).path)
        try:
            if path in ("/", "/index.html"):
                return self.send_file(STATIC / "index.html")
            if path == "/api/ping":  # başka bir libzie örneği çalışıyor mu diye bakmak için
                return self.send_json({"app": "libzie"})
            if path == "/api/tree":
                data = tree(ROOT)
                data["colors"] = load_colors()
                data["icons"] = load_icons()
                data["warning"] = ROOT_WARNING
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
                return self.send_file(safe(path[len("/files/"):]))
            if path.startswith("/vendor/"):
                name = path[len("/vendor/"):]
                if not name or "/" in name or "\\" in name or name.startswith("."):
                    raise ValueError("Geçersiz yol")
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
        except ValueError:
            self.send_error(403)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        length = int(self.headers.get("Content-Length", 0))
        try:
            if u.path == "/api/upload":
                d = safe(q.get("dir", ""))
                d.mkdir(parents=True, exist_ok=True)
                target = unique(d / clean_name(q.get("name", "")))
                remaining = length
                with open(target, "wb") as f:
                    while remaining > 0:
                        chunk = self.rfile.read(min(1 << 20, remaining))
                        if not chunk:
                            break
                        f.write(chunk)
                        remaining -= len(chunk)
                return self.send_json({"path": rel(target)})

            body = json.loads(self.rfile.read(length) or b"{}")

            if u.path == "/api/mkdir":
                parent = safe(body.get("dir", ""))
                p = parent / clean_name(body.get("name", ""))
                if p.exists():
                    raise ValueError("Bu adla bir öğe zaten var")
                p.mkdir(parents=True)
                return self.send_json({"path": rel(p)})

            if u.path == "/api/move":
                src = safe(body["from"])
                dst_dir = safe(body.get("dir", ""))
                dst = dst_dir / clean_name(body.get("name") or src.name)
                if src == ROOT or not src.exists():
                    raise ValueError("Öğe bulunamadı")
                if src.is_dir() and (dst_dir == src or src in dst_dir.parents):
                    raise ValueError("Klasör kendi içine taşınamaz")
                if dst.exists() and not os.path.samefile(src, dst):
                    raise ValueError("Hedefte aynı adla bir öğe var")
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
                        raise guncelleme.UpdateError("Bu sürüm otomatik olarak zaten denendi; Ayarlar'dan elle güncelle.")
                    settings["son_otomatik_deneme"] = latest
                    write_settings(settings)
                guncelleme.start_apply()
                return self.send_json({"ok": True})

            if u.path == "/api/settings":
                if ENV_ROOT:
                    raise ValueError("Klasör KAYNAK_KLASORU ortam değişkeniyle sabitlenmiş")
                text = str(body.get("kaynak_klasoru") or "").strip()
                settings = read_settings()
                if text:
                    p = parse_dir(text)
                    if not p.is_dir():
                        raise ValueError(f"Klasör bulunamadı: {p}")
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
                    raise ValueError("Renk yalnızca derslere verilebilir")
                colors = load_colors()
                if body.get("color"):
                    colors[course.name] = str(body["color"])[:16]
                else:
                    colors.pop(course.name, None)
                save_colors(colors)
                return self.send_json({"ok": True})

            if u.path == "/api/icon":
                course = safe(body["path"])
                if course.parent != ROOT or not course.is_dir():
                    raise ValueError("İkon yalnızca derslere verilebilir")
                icon = str(body.get("icon") or "")
                if icon and not re.fullmatch(r"[a-z0-9-]{1,24}", icon):
                    raise ValueError("Geçersiz ikon")
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
                    raise ValueError("Öğe bulunamadı")
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
                    raise ValueError("Öğe bulunamadı")
                dst = safe(body["to"])
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
            self.send_json({"error": str(e)}, 400)


def is_libzie(port):
    try:
        with urllib.request.urlopen(f"http://{HOST}:{port}/api/ping", timeout=1) as r:
            return json.loads(r.read()).get("app") == "libzie"
    except (OSError, ValueError):
        return False


def start():
    """Çalışan libzie varsa ona bağlanır, yoksa boş ilk portta sunucu açar. (url, sunucu|None) döner;
    sunucu yalnızca bu süreç açtıysa vardır (çağıran serve_forever'dan ve kapatmaktan sorumlu)."""
    for port in range(PORT, PORT + PORT_TRIES):
        if is_libzie(port):
            return f"http://{HOST}:{port}", None
        try:
            return f"http://{HOST}:{port}", ThreadingHTTPServer((HOST, port), Handler)
        except OSError:
            continue
    raise SystemExit(f"{PORT} portundan başlayan portlar dolu; PORT ortam değişkeniyle başka bir port seçin.")


def main():
    url, server = start()
    if server is None:
        print(f"libzie zaten çalışıyor: {url}")
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        return
    print(f"libzie çalışıyor: {url}")
    print(f"Dosyalar: {ROOT}")
    if ROOT_WARNING:
        print(f"UYARI: {ROOT_WARNING}")
    print("Kapatmak için bu pencereyi kapatın veya Ctrl+C'ye basın.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
