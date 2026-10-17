"""Language file check: python tools/i18n_check.py

Compares static/lang/*.json with the ids used in the code:
  - ids used in the code but missing from the English (default) dictionary  → ERROR
  - ids missing in other languages, placeholder ({n}, {name}) mismatches, broken plural structures → ERROR
  - ids that are not used anywhere → warning
Exit code: 1 if there are errors. Python standard library only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANG_DIR = ROOT / "static" / "lang"
DEFAULT = "en"
ID_RE = r"[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+"
PLACEHOLDER = re.compile(r"\{(\w+)\}")

langs = {}
for f in sorted(LANG_DIR.glob("*.json")):
    langs[f.stem] = json.loads(f.read_text(encoding="utf-8"))
if DEFAULT not in langs:
    sys.exit(f"ERROR: default language file missing: {LANG_DIR / (DEFAULT + '.json')}")
base = {k for k in langs[DEFAULT] if not k.startswith("_")}
prefixes = {k.split(".")[0] for k in base}

# ---- usages in the code
html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
py = "\n".join((ROOT / n).read_text(encoding="utf-8") for n in ("server.py", "updater.py", "tray.py", "app.py"))
used = {}


def add(i, where):
    used.setdefault(i, where)


# index.html: every string that looks like an id and starts with a known prefix, and the data-i* attributes
for m in re.finditer(r"""(['"`])(""" + ID_RE + r""")\1""", html):
    if m.group(2).split(".")[0] in prefixes:
        add(m.group(2), "index.html")
for m in re.finditer(r"""data-i(?:-title|-ph|-aria|-html)?="(""" + ID_RE + r""")\"""", html):
    add(m.group(1), "index.html data-i")
# WMO codes
w0 = html.find("const WMO = {")
if w0 >= 0:
    for code in re.findall(r"(\d+): 'wmo\.\d+'", html[w0:html.index("};", w0)]):
        add(f"wmo.{code}", "WMO")
# server: AppError / UpdateError / deny / msg
for m in re.finditer(r"""(?:AppError|UpdateError|deny\(\d+,|msg)\(?\s*"(""" + ID_RE + r""")\"""", py):
    add(m.group(1), "python")
for m in re.finditer(r"""\(\s*"(""" + ID_RE + r""")\"\s*,\s*\{""", py):  # warning = ("warn.x", {...})
    add(m.group(1), "python")
for m in re.finditer(r"""error_code="(""" + ID_RE + r""")\"""", py):
    add(m.group(1), "python")

errors, warns = [], []
for i, where in sorted(used.items()):
    if i not in base:
        errors.append(f"used in the code but missing from {DEFAULT}.json: {i}  ({where})")
for lang, d in langs.items():
    keys = {k for k in d if not k.startswith("_")}
    if "_name" not in d:
        errors.append(f"{lang}.json: '_name' (the language's own name) is missing")
    for k in sorted(base - keys):
        errors.append(f"missing in {lang}.json: {k}")
    for k in sorted(keys - base):
        warns.append(f"extra in {lang}.json (not in the default): {k}")
    for k in keys & base:
        v, b = d[k], langs[DEFAULT][k]
        if isinstance(v, dict) and (not v.get("other") or not all(isinstance(x, str) for x in v.values())):
            errors.append(f"{lang}.json {k}: plural object needs 'other' and its values must be text")
        texts = lambda x: list(x.values()) if isinstance(x, dict) else [x]
        ph = lambda x: set().union(*(set(PLACEHOLDER.findall(t)) for t in texts(x) if isinstance(t, str)))
        if ph(v) != ph(b):
            errors.append(f"{lang}.json {k}: placeholders do not match {DEFAULT}: {sorted(ph(v))} ≠ {sorted(ph(b))}")
# theme names are built dynamically (t('theme.' + id)): every theme file needs a theme.<id>
for tf in sorted((ROOT / "static" / "themes").glob("*.json")):
    add(f"theme.{tf.stem}", "theme file")
    if f"theme.{tf.stem}" not in base:
        errors.append(f"theme {tf.name} has no theme.{tf.stem} (display name) in {DEFAULT}.json")
add("theme.auto", "theme picker")
for k in sorted(base - set(used)):
    warns.append(f"not used anywhere: {k}")

print(f"languages: {', '.join(langs)} · ids: {len(base)} · used in code: {len(used)}")
for w in warns:
    print("warning:", w)
for e in errors:
    print("ERROR:", e)
print("result:", "OK" if not errors else f"{len(errors)} errors")
sys.exit(1 if errors else 0)
