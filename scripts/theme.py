"""Shared look for every SVG on the profile: colors, font, panel frame.

Standard library only, so the daily GitHub Action needs no installs.
"""
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = Path(__file__).resolve().parent / "fonts"

# Amber phosphor on warm near-black. One accent, no rainbow.
BG = "#0e0c09"
BORDER = "#2b241a"
AMBER = "#ffb000"
AMBER_SOFT = "#d9a441"
TEXT = "#eadcc0"
MUTED = "#7d6b4f"
FAINT = "#3a3125"
PORTRAIT = "#f1e7d3"  # ivory: the portrait reads like a black-and-white photo; amber stays the accent

# Heatmap levels 0..4 (none -> brightest)
LEVELS = ["#1c1812", "#4d3500", "#8a5c00", "#cc8800", "#ffb000"]

# Transparent band on every side of every frame. Two neighbouring images then
# show a 10px gap, both side by side (computer) and stacked (phone), and stacked
# frames line up on the same left and right edges.
INSET = 5
PAD = INSET + 18  # where content starts, from the image edge

FONT_STACK = "'JBM', 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def font_face() -> str:
    """Embed the subset font so the SVG looks the same on every machine."""
    rules = []
    for weight in (400, 700):
        data = base64.b64encode((FONTS / f"jbm-{weight}.woff2").read_bytes()).decode()
        rules.append(
            "@font-face{font-family:'JBM';font-weight:%d;"
            "src:url(data:font/woff2;base64,%s) format('woff2');}" % (weight, data)
        )
    return "".join(rules)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def panel(width: int, height: int, prompt: str) -> str:
    """Rounded dark window with a one-line shell prompt as its title."""
    x0, w = INSET, width - 2 * INSET
    return f"""
  <defs>
    <pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse">
      <rect width="4" height="1" fill="#ffffff" opacity="0.025"/>
    </pattern>
  </defs>
  <rect x="{x0 + 0.5}" y="{INSET + 0.5}" width="{w - 1}" height="{height - 2 * INSET - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <text x="{x0 + 18}" y="27" class="prompt"><tspan fill="{AMBER}">mohammed@gaza</tspan><tspan fill="{MUTED}"> ~ $ </tspan><tspan fill="{TEXT}">{esc(prompt)}</tspan></text>
  <line x1="{x0 + 18}" y1="40" x2="{x0 + w - 18}" y2="40" stroke="{FAINT}"/>"""


def scanlines(width: int, height: int) -> str:
    x0, w = INSET, width - 2 * INSET
    return (f'<rect x="{x0 + 1}" y="{INSET + 1}" width="{w - 2}" height="{height - 2 * INSET - 2}" rx="10" '
            f'fill="url(#scan)" pointer-events="none"/>')


def base_css() -> str:
    return (
        font_face()
        + f"text{{font-family:{FONT_STACK};}}"
        + ".prompt{font-size:13px;}"
        + "@media (prefers-reduced-motion: reduce){*{animation:none!important;opacity:1!important;}}"
    )


def write(name: str, svg: str) -> Path:
    out = ROOT / "assets" / name
    out.write_text(svg, encoding="utf-8")
    return out
