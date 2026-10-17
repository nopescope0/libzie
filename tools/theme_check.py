"""Theme check: python tools/theme_check.py

Validates static/themes/*.json (the same rules as themes.py) and measures each theme's readability with WCAG contrast
ratios. Body text needs at least 4.5:1, large/decorative elements 3:1. Exit code: 1 if there are errors.
Python standard library only. Semi-transparent (rgba) values are computed by blending them onto the background.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import themes as theme_files  # noqa: E402


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
    return None, 1.0  # hsl: not checked


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


# (foreground, background, minimum ratio, description)
CHECKS = [
    ("--text", "--bg", 7, "body text / background"), ("--text", "--surface", 7, "text / card surface"), ("--text", "--side", 7, "text / sidebar"),
    ("--text", "--hover", 4.5, "text / selected item"), ("--muted", "--bg", 4.5, "muted text / background"), ("--muted", "--surface", 4.5, "muted text / card"),
    ("--muted", "--side", 4.5, "muted text / sidebar"), ("--faint", "--bg", 4.5, "small text / background"), ("--faint", "--surface", 4.5, "small text / card"),
    ("--faint", "--side", 4.5, "small text / sidebar"), ("--accent", "--bg", 4.5, "accent text / background"), ("--accent", "--surface", 4.5, "accent text / card"),
    ("--accent", "--side", 3, "accent icon / sidebar"), ("--on-accent", "--highlight", 4.5, "primary button text"),
    ("--on-accent", "--highlight-hover", 4.5, "primary button (hover)"), ("--danger", "--surface", 4.5, "error text / card"),
    ("--danger", "--bg", 4.5, "error text / background"), ("--warn", "--bg", 4.5, "warning text / background"), ("--line-strong", "--bg", 1.5, "strong line / background"),
    ("--t-pdf", "--surface", 4.5, "PDF badge"), ("--t-slide", "--surface", 4.5, "slide badge"), ("--t-doc", "--surface", 4.5, "document badge"),
    ("--t-sheet", "--surface", 4.5, "sheet badge"), ("--t-img", "--surface", 4.5, "image badge"),
]

errors = 0
loaded = theme_files.load()
base = loaded[theme_files.DEFAULT]["vars"]
print("themes:", ", ".join(loaded), "| default:", theme_files.DEFAULT)
for tid, th in loaded.items():
    v = {**base, **th["vars"]}
    missing = [k for k in theme_files.ALLOWED if k not in v]
    if missing:
        print(f"[{tid}] ERROR missing variable: {missing}")
        errors += 1
    bg = parse(v["--bg"])
    bg_rgb = bg[0]
    for fg_k, bg_k, need, label in CHECKS:
        fg_c, bgc = parse(v[fg_k]), parse(v[bg_k])
        if fg_c[0] is None or bgc[0] is None:
            continue
        base_rgb = over(bgc, bg_rgb) if bgc[1] < 1 else bgc[0]
        r = ratio(over(fg_c, (base_rgb,)), base_rgb)
        flag = "" if r >= need else "  <-- TOO LOW"
        if r < need:
            errors += 1
        print(f"[{tid}] {label:32s} {fg_k:>12} / {bg_k:<18} {r:5.2f}:1 (min {need}){flag}")
    others = [k for k in th["vars"] if k not in theme_files.ALLOWED]
    if others:
        print(f"[{tid}] ERROR variable not allowed: {others}")
        errors += 1
print("result:", "OK" if not errors else f"{errors} problems")
sys.exit(1 if errors else 0)
