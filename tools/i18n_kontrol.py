"""Dil dosyası denetimi: python tools/i18n_kontrol.py

static/lang/*.json dosyalarını koddaki kimlik kullanımlarıyla karşılaştırır:
  - kodda kullanılan ama Türkçe (varsayılan) sözlükte olmayan kimlikler  → HATA
  - başka dillerde eksik kimlikler, yer tutucu ({n}, {name}) uyuşmazlıkları, bozuk çoğul yapıları → HATA
  - hiçbir yerde kullanılmayan kimlikler → uyarı
Çıkış kodu: hata varsa 1. Yalnızca Python standart kütüphanesi.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANG_DIR = ROOT / "static" / "lang"
DEFAULT = "tr"
ID_RE = r"[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+"
PLACEHOLDER = re.compile(r"\{(\w+)\}")

langs = {}
for f in sorted(LANG_DIR.glob("*.json")):
    langs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
if DEFAULT not in langs:
    sys.exit(f"HATA: varsayılan dil dosyası yok: {LANG_DIR / (DEFAULT + '.json')}")
base = {k for k in langs[DEFAULT] if not k.startswith("_")}
prefixes = {k.split(".")[0] for k in base}

# ---- koddaki kullanımlar
html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
py = "\n".join((ROOT / n).read_text(encoding="utf-8") for n in ("server.py", "guncelleme.py"))
used = {}


def add(i, where):
    used.setdefault(i, where)


# index.html: kimliğe benzeyen ve bilinen bir önekle başlayan her dizge, data-i* öznitelikleri
for m in re.finditer(r"""(['"`])(""" + ID_RE + r""")\1""", html):
    if m.group(2).split(".")[0] in prefixes:
        add(m.group(2), "index.html")
for m in re.finditer(r"""data-i(?:-title|-ph|-aria|-html)?="(""" + ID_RE + r""")\"""", html):
    add(m.group(1), "index.html data-i")
# WMO kodları
w0 = html.find("const WMO = {")
if w0 >= 0:
    for code in re.findall(r"(\d+): 'wmo\.\d+'", html[w0:html.index("};", w0)]):
        add(f"wmo.{code}", "WMO")
# sunucu: AppError / UpdateError / deny / msg
for m in re.finditer(r"""(?:AppError|UpdateError|deny\(\d+,|msg)\(?\s*"(""" + ID_RE + r""")\"""", py):
    add(m.group(1), "python")
for m in re.finditer(r"""\(\s*"(""" + ID_RE + r""")\"\s*,\s*\{""", py):  # warning = ("warn.x", {...})
    add(m.group(1), "python")
for m in re.finditer(r"""error_code="(""" + ID_RE + r""")\"""", py):
    add(m.group(1), "python")

errors, warns = [], []
for i, where in sorted(used.items()):
    if i not in base:
        errors.append(f"kodda kullanılıyor ama {DEFAULT}.json'da yok: {i}  ({where})")
for lang, d in langs.items():
    keys = {k for k in d if not k.startswith("_")}
    if "_name" not in d:
        errors.append(f"{lang}.json: '_name' (dilin kendi adı) yok")
    for k in sorted(base - keys):
        errors.append(f"{lang}.json'da eksik: {k}")
    for k in sorted(keys - base):
        warns.append(f"{lang}.json'da fazladan (varsayılanda yok): {k}")
    for k in keys & base:
        v, b = d[k], langs[DEFAULT][k]
        if isinstance(v, dict) and (not v.get("other") or not all(isinstance(x, str) for x in v.values())):
            errors.append(f"{lang}.json {k}: çoğul nesnesinde 'other' zorunlu ve değerler metin olmalı")
        texts = lambda x: list(x.values()) if isinstance(x, dict) else [x]
        ph = lambda x: set().union(*(set(PLACEHOLDER.findall(t)) for t in texts(x) if isinstance(t, str)))
        if ph(v) != ph(b):
            errors.append(f"{lang}.json {k}: yer tutucular {DEFAULT} ile uyuşmuyor: {sorted(ph(v))} ≠ {sorted(ph(b))}")
# tema adları dinamik kurulur (t('theme.' + kimlik)): her tema dosyası için theme.<kimlik> gerekir
for tf in sorted((ROOT / "static" / "themes").glob("*.json")):
    add(f"theme.{tf.stem}", "tema dosyası")
    if f"theme.{tf.stem}" not in base:
        errors.append(f"{tf.name} teması için {DEFAULT}.json'da theme.{tf.stem} (görünen ad) yok")
add("theme.auto", "tema seçici")
for k in sorted(base - set(used)):
    warns.append(f"hiçbir yerde kullanılmıyor: {k}")

print(f"diller: {', '.join(langs)} · kimlik: {len(base)} · koddaki kullanım: {len(used)}")
for w in warns:
    print("uyarı:", w)
for e in errors:
    print("HATA:", e)
print("sonuç:", "TAMAM" if not errors else f"{len(errors)} hata")
sys.exit(1 if errors else 0)
