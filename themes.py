"""libzie themes: static/themes/<id>.json. The server validates them all, turns them into CSS and embeds it in the main page.

Theme file: { "scheme": "dark" | "light", "vars": { "--bg": "#0e1a2b", ... } }. The file name (without extension) is the theme's id.
Only variables in the ALLOWED list and only color values (#hex, rgb(), hsl()) are accepted, so a theme file cannot slip another CSS
rule, an external resource or </style> into the page. The default theme (DEFAULT) must always exist: variables missing from the
other themes come from it. The theme's display name is kept in the language files under the id `theme.<id>`.
"""
import json
import re
import sys
from pathlib import Path

FROZEN = getattr(sys, "frozen", False)
THEME_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "static" / "themes"
DEFAULT = "navy"
ALLOWED = (
    "--bg", "--side", "--surface", "--hover", "--line", "--line-strong", "--shelf", "--text", "--muted", "--faint",
    "--accent", "--highlight", "--highlight-hover", "--on-accent", "--danger", "--warn", "--shadow", "--scrim",
    "--t-pdf", "--t-slide", "--t-doc", "--t-sheet", "--t-img",
)
_NUM = r"[\d.]+%?"
COLOR = re.compile(r"(?:#[0-9a-fA-F]{3,8}|(?:rgb|hsl)a?\(\s*" + _NUM + r"(?:\s*[,\s]\s*" + _NUM + r"){2}(?:\s*[,/]\s*" + _NUM + r")?\s*\))")
ID = re.compile(r"[a-z][a-z0-9_-]{1,23}")
_cache = None
_warned = set()  # when running from source themes are read on every request; print each warning once


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
                    raise ValueError(f"invalid variable or value: {k}")
                clean[k] = v.strip()
        except (OSError, ValueError, KeyError, TypeError) as e:
            if f.name not in _warned:
                _warned.add(f.name)
                print(f"WARNING: theme {f.name} was not loaded ({e})", file=sys.stderr)
            continue
        out[f.stem] = {"scheme": scheme, "vars": clean}
    if DEFAULT not in out:
        raise SystemExit(f"The default theme file is missing or invalid: {THEME_DIR / (DEFAULT + '.json')}")
    # default theme first, the others alphabetical
    return {DEFAULT: out[DEFAULT], **{k: out[k] for k in sorted(out) if k != DEFAULT}}


def themes():
    """Read once in the packaged app; on every call when running from source (so edits show up)."""
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
    """The CSS of all themes. The default theme is also applied to :root (valid when there is no attribute), and every theme to the
    .theme-prev[data-theme] preview cards. Scrollbar arrows (a data URL cannot take a CSS variable) are generated from the accent color."""
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
    """For the client: [{id, scheme}] (default first). The colors are in the CSS, so they are not here."""
    return [{"id": tid, "scheme": th["scheme"]} for tid, th in themes().items()]
