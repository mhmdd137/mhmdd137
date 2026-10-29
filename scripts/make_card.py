"""Neofetch-style info card. Run again whenever the details change:

    python scripts/make_card.py
"""
from theme import PAD, AMBER, AMBER_SOFT, MUTED, TEXT, FAINT, base_css, esc, panel, scanlines, write

WIDTH, HEIGHT = 480, 460

# (key, [(text, style), ...]); style: "v" plain value, "b" highlighted name
ROWS = [
    ("Name", [("Mohammed Ziada", "b")]),
    ("Role", [("Full-Stack Product Engineer", "v")]),
    ("Builds", [("SaaS products · MVPs · automations", "v")]),
    ("Stack", [("Next.js · TypeScript · PostgreSQL", "v")]),
    ("", [("React · Tailwind · Supabase · n8n", "v")]),
    ("Now", [("Sufria", "b"), (" — WhatsApp ordering SaaS for restaurants", "v")]),
    ("Shipped", [("Mawjood", "b"), (" — volunteer–organization matching", "v")]),
    ("Also", [("Arabic-name duplicate detection prototype", "v")]),
    ("Edu", [("Software Engineering · final year", "v")]),
    ("Base", [("Gaza · GMT+2", "v")]),
    ("Open", [("Freelance with startups & agencies · remote roles", "v")]),
]

X_KEY, X_VAL, Y0, STEP = PAD, PAD + 74, 72, 30


def build() -> str:
    lines = []
    for i, (key, parts) in enumerate(ROWS):
        y = Y0 + i * STEP
        delay = 0.45 + i * 0.1
        bold = ' fill="%s" font-weight="700"' % AMBER_SOFT
        plain = ' fill="%s"' % TEXT
        spans = "".join(
            f"<tspan{bold if s == 'b' else plain}>{esc(t)}</tspan>" for t, s in parts
        )
        lines.append(
            f'<g class="ln" style="animation-delay:{delay:.2f}s">'
            f'<text x="{X_KEY}" y="{y}" class="k">{esc(key)}</text>'
            f'<text x="{X_VAL}" y="{y}" class="v">{spans}</text></g>'
        )

    end = 0.45 + len(ROWS) * 0.1 + 0.2
    y_rule = Y0 + len(ROWS) * STEP - 8
    y_cur = HEIGHT - 26
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Mohammed Ziada — Full-Stack Product Engineer">
  <style>{base_css()}
    .k{{font-size:12px;fill:{AMBER};}}
    .v{{font-size:12px;}}
    .ln{{opacity:0;animation:in .45s cubic-bezier(.2,.7,.2,1) forwards;}}
    @keyframes in{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:none}}}}
    .cur{{opacity:0;animation:show 0s {end:.2f}s forwards, blink 1.1s steps(1) {end:.2f}s infinite;}}
    @keyframes show{{to{{opacity:1}}}}
    @keyframes blink{{50%{{opacity:0}}}}
  </style>{panel(WIDTH, HEIGHT, "whoami")}
  {''.join(lines)}
  <line x1="{X_KEY}" y1="{y_rule}" x2="{WIDTH - PAD}" y2="{y_rule}" stroke="{FAINT}" class="ln" style="animation-delay:{end - 0.2:.2f}s"/>
  <g class="ln" style="animation-delay:{end - 0.1:.2f}s">
    <text x="{X_KEY}" y="{y_cur}" class="prompt"><tspan fill="{AMBER}">mohammed@gaza</tspan><tspan fill="{MUTED}"> ~ $ </tspan></text>
  </g>
  <rect class="cur" x="{X_KEY + 18 * 7.8:.1f}" y="{y_cur - 11}" width="7.8" height="14" fill="{AMBER}"/>
  {scanlines(WIDTH, HEIGHT)}
</svg>
"""


if __name__ == "__main__":
    print("wrote", write("card.svg", build()))
