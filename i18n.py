"""libzie dil dosyaları: static/lang/<dil>.json. Sunucu hata/uyarı metinlerini ve sayfaya gömülen sözlüğü buradan alır.

Anahtarlar kimliktir ('err.exists'); her dil dosyası düz bir {kimlik: metin} sözlüğüdür ("_name" = dilin kendi adı).
Çoğul değerler { "one": ..., "other": ... } nesnesidir. Sunucu hataları metin yerine kimlik taşır (AppError); metni istemci
etkin dilde çevirir, `error` alanındaki Türkçe metin yalnızca varsayılandır (konsol, kimlik sözlükte yoksa).
"""
import json
import re
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
LANG_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "static" / "lang"
DEFAULT = "tr"
_cache = None


def load():
    out = {}
    for f in sorted(LANG_DIR.glob("*.json")):
        if not re.fullmatch(r"[a-z]{2,3}", f.stem):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            out[f.stem] = data
    return out


def dictionary():
    """Tüm diller. Paketlenmiş uygulamada bir kez okunur; kaynak koddan çalışırken her çağrıda (dosya düzenleyince yenilensin)."""
    global _cache
    if _cache is None or not FROZEN:
        _cache = load()
    return _cache


def msg(code, lang=DEFAULT, **vars):
    d = dictionary()
    v = d.get(lang, {}).get(code)
    if v is None:
        v = d.get(DEFAULT, {}).get(code)
    if isinstance(v, dict):
        v = v.get("other")
    if not isinstance(v, str):
        return code
    return re.sub(r"\{(\w+)\}", lambda m: str(vars.get(m.group(1), m.group(0))), v)


def dict_json():
    """Sayfaya <script type=application/json> içine gömülecek metin ('<' kaçırılır: </script> ile kapanamaz)."""
    text = json.dumps(dictionary(), ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class AppError(ValueError):
    """Kimlikli hata: str(e) varsayılan (Türkçe) metin, code/vars istemcinin çevirmesi için."""

    def __init__(self, code, **vars):
        self.code, self.vars = code, vars
        super().__init__(msg(code, DEFAULT, **vars))


def err_json(e):
    if isinstance(e, AppError):
        return {"error": str(e), "code": e.code, "vars": e.vars}
    return {"error": str(e)}
