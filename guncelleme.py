"""libzie güncelleme: GitHub sürümlerini denetler; paketlenen Windows uygulamasında yeni sürümü indirip uygular.

Yalnızca Python standart kütüphanesini kullanır. İndirme adresi istemciden alınmaz: sunucu sürüm bilgisini
her seferinde GitHub'dan kendisi okur, yalnızca bu deponun sürüm dosyalarını indirir.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

VERSION = "0.1.2"  # GitHub Actions, sürüm etiketinden (v0.1.3 → 0.1.3) derleme sırasında bu satırı yeniden yazar
REPO = "nopescope0/libzie"
# Yalnızca deneme içindir: sahte bir sürüm sunucusuna yönlendirir (indirme adresi denetimi de kapanır)
API = os.environ.get("LIBZIE_GUNCELLEME_URL") or f"https://api.github.com/repos/{REPO}/releases/latest"
ASSETS = {"kurulum": "libzie-kurulum.exe", "tasinabilir": "libzie-tasinabilir.exe"}
FROZEN = getattr(sys, "frozen", False)

_lock = threading.Lock()
_state = {"phase": "idle", "done": 0, "total": 0, "error": ""}  # idle | downloading | restarting | error


class UpdateError(Exception):
    pass


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
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise UpdateError("Yayınlanmış bir sürüm bulunamadı.") from e
        if e.code in (403, 429):
            raise UpdateError("GitHub şu an istek kabul etmiyor; biraz sonra tekrar dene.") from e
        raise UpdateError(f"Sürüm bilgisi alınamadı (GitHub {e.code}).") from e
    except (OSError, ValueError) as e:
        raise UpdateError("Sürüm bilgisi alınamadı; internet bağlantını kontrol et.") from e


def check():
    rel = fetch_release()
    tag = str(rel.get("tag_name") or "")
    if not tag:
        raise UpdateError("Sürüm bilgisi okunamadı.")
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
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
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
        raise UpdateError("İndirilen dosya eksik; tekrar dene.")
    with open(dest, "rb") as f:
        if f.read(2) != b"MZ":
            raise UpdateError("İndirilen dosya geçerli bir uygulama değil.")
    if digest.startswith("sha256:") and sha.hexdigest() != digest[7:].lower():
        raise UpdateError("İndirilen dosyanın doğrulaması tutmadı; tekrar dene.")


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
            raise UpdateError("libzie zaten güncel.")
        asset = next((a for a in rel.get("assets") or [] if a.get("name") == ASSETS[k]), None)
        if not asset:
            raise UpdateError("Bu sürümün indirme dosyası henüz hazır değil; birkaç dakika sonra tekrar dene.")
        url = str(asset.get("browser_download_url") or "")
        if not os.environ.get("LIBZIE_GUNCELLEME_URL") and not url.startswith(f"https://github.com/{REPO}/releases/download/"):
            raise UpdateError("Beklenmeyen indirme adresi; güncelleme iptal edildi.")
        exe = Path(sys.executable)
        if k == "tasinabilir" and not _can_write(exe.parent):
            raise UpdateError(f"{exe.parent} klasörüne yazılamıyor; uygulamayı yazılabilir bir klasöre taşı ya da kurulum sürümünü kullan.")
        work = Path(tempfile.gettempdir()) / "libzie-guncelleme"
        work.mkdir(parents=True, exist_ok=True)
        dest = work / ASSETS[k]
        _download(url, dest, int(asset.get("size") or 0), str(asset.get("digest") or ""))

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
        threading.Timer(1.5, lambda: os._exit(0)).start()
    except UpdateError as e:
        _set(phase="error", error=str(e))
    except Exception as e:  # noqa: BLE001 — hata arayüze gösterilir
        _set(phase="error", error=f"Güncelleme başarısız: {e}")


def start_apply():
    if kind() == "kaynak":
        raise UpdateError("Kaynak koddan çalışırken uygulama içinden güncellenemez; depoyu git pull ile güncelle.")
    with _lock:
        if _state["phase"] in ("downloading", "restarting"):
            raise UpdateError("Güncelleme zaten sürüyor.")
        _state.update(phase="downloading", done=0, total=0, error="")
    threading.Thread(target=_run, daemon=True).start()
