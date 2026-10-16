"""libzie güncelleme: GitHub sürümlerini denetler; paketlenen Windows uygulamasında yeni sürümü indirip uygular.

Yalnızca Python standart kütüphanesini kullanır. İndirme adresi istemciden alınmaz: sunucu sürüm bilgisini
her seferinde GitHub'dan kendisi okur, yalnızca bu deponun sürüm dosyalarını indirir.
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

VERSION = "0.1.3"  # GitHub Actions, sürüm etiketinden (v0.1.3 → 0.1.3) derleme sırasında bu satırı yeniden yazar
REPO = "nopescope0/libzie"
FROZEN = getattr(sys, "frozen", False)
# Yalnızca geliştirirken (paketlenmemiş çalışmada) deneme içindir: sahte bir sürüm sunucusuna yönlendirir, indirme adresi denetimi kapanır.
# Paketlenen uygulamada bu ortam değişkeni yok sayılır.
TEST_API = "" if FROZEN else os.environ.get("LIBZIE_GUNCELLEME_URL", "")
API = TEST_API or f"https://api.github.com/repos/{REPO}/releases/latest"
ASSETS = {"kurulum": "libzie-kurulum.exe", "tasinabilir": "libzie-tasinabilir.exe"}

EXIT_HOOKS = []  # app.py: uygulama os._exit ile kapanmadan önce çalışır (tepsi simgesini kaldırır)
_lock = threading.Lock()
_state = {"phase": "idle", "done": 0, "total": 0, "error": "", "error_code": "", "error_vars": {}}  # idle | downloading | restarting | error


class UpdateError(AppError):
    """Kimlikli güncelleme hatası (UpdateError("upd.err.no_release")); metin static/lang/*.json içindedir."""


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    """İndirme yönlendirmeleri (GitHub → CDN) yalnızca https'e gidebilir; düz http'ye düşürülemez."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not TEST_API and not newurl.lower().startswith("https://"):
            raise UpdateError("upd.err.redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_opener = urllib.request.build_opener(_HttpsOnly)


def kind():
    """kurulum: sihirbazla kurulmuş · tasinabilir: tek dosya exe · kaynak: python server.py (uygulama içinden güncellenmez)"""
    if not FROZEN or sys.platform != "win32":
        return "kaynak"
    return "kurulum" if (Path(sys.executable).parent / "unins000.exe").exists() else "tasinabilir"


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
        # Bu kurulum türünün dosyası sürüme eklenmemişse (derleme sürüyor ya da başarısız) güncelleme sunulmaz
        "downloadable": k == "kaynak" or ASSETS[k] in names,
        "url": rel.get("html_url") or f"https://github.com/{REPO}/releases",
    }


def status():
    with _lock:
        return dict(_state)


def _set(**kw):
    with _lock:
        _state.update(kw)


def _clean_env():
    """PyInstaller'ın tek dosya sürümü kendi geçici klasörünü ortam değişkenleriyle çocuk süreçlere taşır;
    yeni libzie bunları devralırsa silinmiş klasörü arar. Başlatılan süreçlere geçirmeden önce temizlenir."""
    return {k: v for k, v in os.environ.items() if not k.startswith("_PYI") and k != "_MEIPASS2"}


def _detached(console):
    """Bu süreç kapansa da yaşayan süreç. Betik (cmd) için gizli bir konsol gerekir: konsolsuz çalışan cmd'de
    `ping` beklemesi hemen biter ve yeniden deneme döngüsü uygulama kapanmadan tükenir."""
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
    """İndirilecek dosyanın beklenen SHA-256 özeti: GitHub'ın asset `digest` alanı, yoksa sürümdeki SHA256SUMS.txt.
    İkisi de yoksa güncelleme yapılmaz (boyut/başlık denetimi tek başına yetmez)."""
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
        probe = folder / ".libzie-yazma-denemesi"
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
move /y "%LIBZIE_YENI%" "%LIBZIE_EXE%" >nul 2>&1
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
        if k == "tasinabilir" and not _can_write(exe.parent):
            raise UpdateError("upd.err.not_writable", dir=str(exe.parent))
        for old in Path(tempfile.gettempdir()).glob("libzie-guncelleme-*"):  # önceki denemelerin artıkları
            shutil.rmtree(old, ignore_errors=True)
        work = Path(tempfile.mkdtemp(prefix="libzie-guncelleme-"))  # tahmin edilemez, yalnızca bu kullanıcıya açık klasör
        dest = work / ASSETS[k]
        _download(url, dest, int(asset.get("size") or 0), digest)

        if k == "kurulum":
            # Sihirbaz çalışan libzie'yi kapatır, dosyaları yenileyip uygulamayı yeniden açar (libzie.iss: WizardSilent)
            subprocess.Popen([str(dest), "/SILENT", "/CLOSEAPPLICATIONS", "/SUPPRESSMSGBOXES", "/NORESTART"], **_detached(False))
        else:
            bat = work / "degistir.bat"
            bat.write_text(_SWAP_BAT, encoding="ascii")
            env = _clean_env()
            env.update(LIBZIE_YENI=str(dest).replace("/", "\\"), LIBZIE_EXE=str(exe).replace("/", "\\"))  # move eğik çizgiyi sevmez
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
    except Exception as e:  # noqa: BLE001 — hata arayüze gösterilir
        _set(phase="error", error=i18n.msg("upd.err.failed", error=str(e)), error_code="upd.err.failed", error_vars={"error": str(e)})


def start_apply():
    if kind() == "kaynak":
        raise UpdateError("upd.err.from_source")
    with _lock:
        if _state["phase"] in ("downloading", "restarting"):
            raise UpdateError("upd.err.in_progress")
        _state.update(phase="downloading", done=0, total=0, error="", error_code="", error_vars={})
    threading.Thread(target=_run, daemon=True).start()
