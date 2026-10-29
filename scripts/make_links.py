"""Small link buttons in the same terminal style. Run again when links change:

    python scripts/make_links.py

The README wraps each image in <a href="...">, so the buttons are clickable.
"""
from theme import AMBER, BG, BORDER, INSET, MUTED, TEXT, base_css, esc, write

LABELS = ["linkedin", "email", "sufria", "mawjood"]

H, PAD, CH = 42, 14, 7.8  # height (incl. the transparent band), side padding, char width at 13px


def chip(label: str) -> str:
    text_w = (2 + len(label)) * CH  # "~/" + label
    w = round(4 + PAD + text_w + 10 + 10 + PAD + 4)  # 4px transparent margin each side
    ax = 4 + PAD + text_w + 10  # arrow position
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{H}" viewBox="0 0 {w} {H}" role="img" aria-label="{esc(label)}">
  <style>{base_css()}</style>
  <rect x="4.5" y="{INSET + 0.5}" width="{w - 9}" height="{H - 2 * INSET - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
  <text x="{4 + PAD}" y="{H / 2 + 4.5}" class="prompt"><tspan fill="{MUTED}">~/</tspan><tspan fill="{TEXT}">{esc(label)}</tspan></text>
  <path d="M{ax:.1f} {H / 2 + 4:.1f} L{ax + 8:.1f} {H / 2 - 4:.1f} M{ax + 2:.1f} {H / 2 - 4:.1f} H{ax + 8:.1f} V{H / 2 + 2:.1f}"
        stroke="{AMBER}" stroke-width="1.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


if __name__ == "__main__":
    for name in LABELS:
        print("wrote", write(f"link-{name}.svg", chip(name)))
