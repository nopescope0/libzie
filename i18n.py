"""libzie language files: static/lang/<lang>.json. The server takes error/warning texts and the dictionary embedded in the page from here.

Keys are ids ('err.exists'); each language file is a flat {id: text} dictionary ("_name" = the language's own name).
Plural values are { "one": ..., "other": ... } objects. Server errors carry an id instead of text (AppError); the client translates
the text into the active language, the English text in the `error` field is only the default (console, or if the id is not in the dictionary).
"""
import json
import re
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
LANG_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "static" / "lang"
DEFAULT = "en"
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
    """All languages. Read once in the packaged app; on every call when running from source (so edits show up)."""
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
    """Text to embed in the page inside <script type=application/json> ('<' is escaped: it cannot close with </script>)."""
    text = json.dumps(dictionary(), ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class AppError(ValueError):
    """Error with an id: str(e) is the default (English) text, code/vars are for the client to translate."""

    def __init__(self, code, **vars):
        self.code, self.vars = code, vars
        super().__init__(msg(code, DEFAULT, **vars))


def err_json(e):
    if isinstance(e, AppError):
        return {"error": str(e), "code": e.code, "vars": e.vars}
    return {"error": str(e)}
