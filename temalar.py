"""libzie temaları: static/themes/<kimlik>.json. Sunucu hepsini doğrulayıp CSS'e çevirir ve ana sayfaya gömer.

Tema dosyası: { "scheme": "dark" | "light", "vars": { "--bg": "#0e1a2b", ... } }. Dosya adı (uzantısız) temanın kimliğidir.
Yalnızca ALLOWED listesindeki değişkenler ve yalnızca renk değerleri (#hex, rgb(), hsl()) kabul edilir; böylece bir tema dosyası sayfaya
başka bir CSS kuralı, dış kaynak ya da </style> sokamaz. Varsayılan tema (DEFAULT) her zaman bulunmalıdır: öteki temalarda eksik
değişkenler onunkilerden gelir. Temanın görünen adı dil dosyalarında `theme.<kimlik>` kimliğiyle tutulur.
"""
import json
import re
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
THEME_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "static" / "themes"
DEFAULT = "dark"
ALLOWED = (
    "--bg", "--side", "--surface", "--hover", "--line", "--line-strong", "--shelf", "--text", "--muted", "--faint",
    "--accent", "--highlight", "--highlight-hover", "--on-accent", "--danger", "--warn", "--shadow", "--scrim",
    "--t-pdf", "--t-slide", "--t-doc", "--t-sheet", "--t-img",
)
_NUM = r"[\d.]+%?"
COLOR = re.compile(r"(?:#[0-9a-fA-F]{3,8}|(?:rgb|hsl)a?\(\s*" + _NUM + r"(?:\s*[,\s]\s*" + _NUM + r"){2}(?:\s*[,/]\s*" + _NUM + r")?\s*\))")
ID = re.compile(r"[a-z][a-z0-9_-]{1,23}")
_cache = None
_warned = set()  # kaynak koddan çalışırken tema her istekte okunur; aynı uyarı bir kez yazılsın


def load():
    out = {}
    for f in sorted(THEME_DIR.glob("*.json")):
        if not ID.fullmatch(f.stem):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            scheme = data["scheme"]
            vars_ = data["vars"]
            if scheme not in ("dark", "light") or not isinstance(vars_, dict):
                raise ValueError("scheme/vars")
            clean = {}
            for k, v in vars_.items():
                if k not in ALLOWED or not isinstance(v, str) or not COLOR.fullmatch(v.strip()):
                    raise ValueError(f"geçersiz değişken ya da değer: {k}")
                clean[k] = v.strip()
        except (OSError, ValueError, KeyError, TypeError) as e:
            if f.name not in _warned:
                _warned.add(f.name)
                print(f"UYARI: {f.name} teması yüklenmedi ({e})", file=sys.stderr)
            continue
        out[f.stem] = {"scheme": scheme, "vars": clean}
    if DEFAULT not in out:
        raise SystemExit(f"Varsayılan tema dosyası yok ya da geçersiz: {THEME_DIR / (DEFAULT + '.json')}")
    # varsayılan tema önce, ötekiler alfabetik
    return {DEFAULT: out[DEFAULT], **{k: out[k] for k in sorted(out) if k != DEFAULT}}


def themes():
    """Paketlenmiş uygulamada bir kez okunur; kaynak koddan çalışırken her çağrıda (dosya düzenleyince yenilensin)."""
    global _cache
    if _cache is None or not FROZEN:
        _cache = load()
    return _cache


def _arrow(path, color):
    c = color.lstrip("#") if re.fullmatch(r"#[0-9a-fA-F]{6}", color) else "ff8a3d"
    return ('url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 10 10\'%3E%3Cpath d=\'' + path +
            '\' fill=\'none\' stroke=\'%23' + c + '\' stroke-opacity=\'.75\' stroke-width=\'1.6\' stroke-linecap=\'round\' stroke-linejoin=\'round\'/%3E%3C/svg%3E")')


ARROWS = {
    "vertical:decrement": "M2 6.5 5 3.5 8 6.5", "vertical:increment": "M2 3.5 5 6.5 8 3.5",
    "horizontal:decrement": "M6.5 2 3.5 5 6.5 8", "horizontal:increment": "M3.5 2 6.5 5 3.5 8",
}


def css():
    """Tüm temaların CSS'i. Varsayılan tema ek olarak :root'a (öznitelik yokken de geçerli), her tema da .theme-prev[data-theme]
    önizleme kartlarına uygulanır. Kaydırma çubuğu okları (veri adresi olduğundan CSS değişkeni alamaz) vurgu renginden üretilir."""
    default_vars = themes()[DEFAULT]["vars"]
    parts = []
    for tid, th in themes().items():
        sel = [f':root[data-theme="{tid}"]', f'.theme-prev[data-theme="{tid}"]']
        if tid == DEFAULT:
            sel.insert(0, ":root")
        body = "".join(f"{k}:{v};" for k, v in th["vars"].items()) + f"color-scheme:{th['scheme']};"
        parts.append(",".join(sel) + "{" + body + "}")
        accent = th["vars"].get("--accent", default_vars.get("--accent", "#ff8a3d"))
        scope = ":root" if tid == DEFAULT else f':root[data-theme="{tid}"]'
        for kind, path in ARROWS.items():
            parts.append(f"{scope} ::-webkit-scrollbar-button:single-button:{kind}{{background-image:{_arrow(path, accent)}}}")
    return "\n".join(parts)


def meta():
    """İstemci için: [{id, scheme}] (varsayılan ilk). Renkler CSS'te olduğundan burada yoktur."""
    return [{"id": tid, "scheme": th["scheme"]} for tid, th in themes().items()]
