"""Tema denetimi: python tools/tema_kontrol.py

static/themes/*.json dosyalarını doğrular (temalar.py ile aynı kurallar) ve her temanın okunabilirliğini WCAG kontrast
oranlarıyla ölçer. Düz metin/gövde için en az 4,5:1, büyük/dekoratif öğeler için 3:1 aranır. Çıkış kodu: hata varsa 1.
Yalnızca Python standart kütüphanesi. Yarı saydam (rgba) değerler zemine karıştırılarak hesaplanır.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import temalar  # noqa: E402


def parse(c):
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) in (3, 4):
            h = "".join(x * 2 for x in h)
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (r, g, b), a
    nums = [float(x.rstrip("%")) for x in re.findall(r"[\d.]+%?", c)]
    if c.startswith("rgb"):
        return tuple(nums[:3]), (nums[3] if len(nums) > 3 else 1.0)
    return None, 1.0  # hsl: denetlenmez


def over(fg, bg):
    (r, g, b), a = fg
    return tuple(a * f + (1 - a) * k for f, k in zip((r, g, b), bg[0]))


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# (ön plan, arka plan, en az oran, açıklama)
CHECKS = [
    ("--text", "--bg", 7, "gövde metni / zemin"), ("--text", "--surface", 7, "metin / kart yüzeyi"), ("--text", "--side", 7, "metin / kenar çubuğu"),
    ("--text", "--hover", 4.5, "metin / seçili öğe"), ("--muted", "--bg", 4.5, "soluk metin / zemin"), ("--muted", "--surface", 4.5, "soluk metin / kart"),
    ("--muted", "--side", 4.5, "soluk metin / kenar çubuğu"), ("--faint", "--bg", 4.5, "küçük metin / zemin"), ("--faint", "--surface", 4.5, "küçük metin / kart"),
    ("--faint", "--side", 4.5, "küçük metin / kenar çubuğu"), ("--accent", "--bg", 4.5, "vurgu metni / zemin"), ("--accent", "--surface", 4.5, "vurgu metni / kart"),
    ("--accent", "--side", 3, "vurgu simgesi / kenar çubuğu"), ("--on-accent", "--highlight", 4.5, "birincil düğme metni"),
    ("--on-accent", "--highlight-hover", 4.5, "birincil düğme (üzerine gelince)"), ("--danger", "--surface", 4.5, "hata metni / kart"),
    ("--danger", "--bg", 4.5, "hata metni / zemin"), ("--warn", "--bg", 4.5, "uyarı metni / zemin"), ("--line-strong", "--bg", 1.5, "belirgin çizgi / zemin"),
    ("--t-pdf", "--surface", 4.5, "PDF rozeti"), ("--t-slide", "--surface", 4.5, "slayt rozeti"), ("--t-doc", "--surface", 4.5, "belge rozeti"),
    ("--t-sheet", "--surface", 4.5, "tablo rozeti"), ("--t-img", "--surface", 4.5, "görsel rozeti"),
]

errors = 0
themes = temalar.load()
base = themes[temalar.DEFAULT]["vars"]
print("temalar:", ", ".join(themes), "| varsayılan:", temalar.DEFAULT)
for tid, th in themes.items():
    v = {**base, **th["vars"]}
    missing = [k for k in temalar.ALLOWED if k not in v]
    if missing:
        print(f"[{tid}] HATA eksik değişken: {missing}")
        errors += 1
    bg = parse(v["--bg"])
    bg_rgb = bg[0]
    for fg_k, bg_k, need, label in CHECKS:
        fg_c, bgc = parse(v[fg_k]), parse(v[bg_k])
        if fg_c[0] is None or bgc[0] is None:
            continue
        base_rgb = over(bgc, bg_rgb) if bgc[1] < 1 else bgc[0]
        r = ratio(over(fg_c, (base_rgb,)), base_rgb)
        flag = "" if r >= need else "  <-- YETERSİZ"
        if r < need:
            errors += 1
        print(f"[{tid}] {label:32s} {fg_k:>12} / {bg_k:<18} {r:5.2f}:1 (en az {need}){flag}")
    others = [k for k in th["vars"] if k not in temalar.ALLOWED]
    if others:
        print(f"[{tid}] HATA izin verilmeyen değişken: {others}")
        errors += 1
print("sonuç:", "TAMAM" if not errors else f"{errors} sorun")
sys.exit(1 if errors else 0)
