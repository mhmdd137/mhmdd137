"""Draw the last 12 weeks of contributions as two animated SVGs.

Runs daily in GitHub Actions. No token needed: it reads the same public
calendar the profile page uses. Standard library only.

    python scripts/update_activity.py              # fetch live data
    python scripts/update_activity.py data.json    # use a saved file (offline preview)
    python scripts/update_activity.py --placeholder

Two images instead of one wide panel: side by side on a computer, stacked on
a phone, so the labels stay readable there.
"""
import json
import re
import sys
import urllib.request
from datetime import date, timedelta

from theme import AMBER, FAINT, LEVELS, MUTED, PAD, base_css, panel, scanlines, write

USER = "mhmdd137"
WEEKS = 12
HEIGHT = 304
GRAPH_W, STATS_W = 410, 420  # 410 + 420 = 830, the same row width as portrait + card
STYLE = f".lbl{{font-size:11px;fill:{MUTED};}}"


LEVEL_GUESS = [0, 1, 3, 6, 10]  # rough count per color level, only if the page stops listing counts


def fetch() -> list[dict]:
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-activity-svg"},
    )
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")

    # One element per day, carrying data-date and data-level (a <td> today, a <rect> in older layouts)
    cells = {}  # element id -> (date, level, count or None)
    for n, tag in enumerate(re.findall(r'<[a-z]+\b[^>]*\bdata-date="[\d-]+"[^>]*>', html)):
        lv = re.search(r'data-level="(\d)"', tag)
        if not lv:
            continue
        d = re.search(r'data-date="([\d-]+)"', tag).group(1)
        i = re.search(r'\bid="([^"]+)"', tag)
        c = re.search(r'data-count="(\d+)"', tag)
        cells[i.group(1) if i else f"_{n}"] = (d, min(int(lv.group(1)), 4), int(c.group(1)) if c else None)

    tips = {}  # element id -> count, from the hover tooltips ("3 contributions on …")
    for for_id, text in re.findall(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*([\d,]+)\s+contribution", text)
        tips[for_id] = int(m.group(1).replace(",", "")) if m else 0

    if not cells:
        raise SystemExit("Could not read the contributions calendar (page layout changed?)")
    days = {}
    for key, (d, lv, c) in cells.items():
        count = c if c is not None else tips.get(key, LEVEL_GUESS[lv])
        days[d] = {"date": d, "level": lv, "count": count}
    return sorted(days.values(), key=lambda x: x["date"])


def window(days: list[dict]) -> list[dict]:
    """The last 12 calendar columns, Sunday-first like GitHub."""
    last = date.fromisoformat(days[-1]["date"])
    first = last - timedelta(days=(last.weekday() + 1) % 7) - timedelta(weeks=WEEKS - 1)
    return [d for d in days if date.fromisoformat(d["date"]) >= first]


def stats(days: list[dict]) -> dict:
    """Only numbers that never collapse overnight: no 'current streak'."""
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max((d["count"] for d in days), default=0)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    return {"total": total, "active": active, "days": len(days), "best": best, "longest": longest}


def svg_open(width: int, label: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{HEIGHT}" '
            f'viewBox="0 0 {width} {HEIGHT}" role="img" aria-label="{label}">')


def graph(days: list[dict]) -> str:
    """Left image: the heatmap."""
    first = date.fromisoformat(days[0]["date"])
    cell, gap = 21, 5
    gx, gy = PAD + 44, 78  # grid origin (weekday labels sit in the 44px to its left)

    rects, months = [], []
    last_month, last_col = None, -9
    for d in days:
        dt = date.fromisoformat(d["date"])
        col = (dt - first).days // 7
        row = (dt.weekday() + 1) % 7
        x, y = gx + col * (cell + gap), gy + row * (cell + gap)
        delay = 0.35 + (col + row) * 0.035
        rects.append(
            f'<rect class="c" style="animation-delay:{delay:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" '
            f'rx="4" fill="{LEVELS[d["level"]]}"><title>{d["count"]} on {d["date"]}</title></rect>'
        )
        # Month label above the first column of each month (skip if cramped)
        if row == 0 and dt.month != last_month and col - last_col >= 2:
            months.append(f'<text x="{x}" y="{gy - 12}" class="lbl">{dt.strftime("%b")}</text>')
            last_month, last_col = dt.month, col

    weekdays = "".join(
        f'<text x="{gx - 10}" y="{gy + r * (cell + gap) + 15}" class="lbl" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    ly = gy + 7 * (cell + gap) + 12
    legend = (
        f'<text x="{gx}" y="{ly + 10}" class="lbl">less</text>'
        + "".join(f'<rect x="{gx + 36 + i * 16}" y="{ly}" width="12" height="12" rx="3" fill="{c}"/>'
                  for i, c in enumerate(LEVELS))
        + f'<text x="{gx + 36 + 5 * 16 + 4}" y="{ly + 10}" class="lbl">more</text>'
    )
    return f"""{svg_open(GRAPH_W, f"Contribution heatmap, last {WEEKS} weeks")}
  <style>{base_css()}{STYLE}
    .c{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s cubic-bezier(.2,.7,.2,1) forwards;}}
    @keyframes pop{{from{{opacity:0;transform:scale(.4)}}to{{opacity:1;transform:none}}}}
  </style>{panel(GRAPH_W, HEIGHT, f"activity --last {WEEKS}w")}
  {''.join(months)}{weekdays}
  {''.join(rects)}
  {legend}
  {scanlines(GRAPH_W, HEIGHT)}
</svg>
"""


def summary(days: list[dict]) -> str:
    """Right image: four numbers."""
    s = stats(days)
    tiles = [
        (f"{s['total']}", "contributions"),
        (f"{s['active']}/{s['days']}", "active days"),
        (f"{s['best']}", "best single day"),
        (f"{s['longest']}d", "longest streak"),
    ]
    sx0, sy0, th = PAD, 78, 84
    tw = (STATS_W - 2 * PAD - 12) / 2
    tile_svg = []
    for i, (num, label) in enumerate(tiles):
        x = sx0 + (i % 2) * (tw + 12)
        y = sy0 + (i // 2) * (th + 12)
        tile_svg.append(
            f'<g class="st" style="animation-delay:{0.9 + i * 0.12:.2f}s">'
            f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{th}" rx="8" fill="none" stroke="{FAINT}"/>'
            f'<text x="{x + 16:.1f}" y="{y + 44}" class="num">{num}</text>'
            f'<text x="{x + 16:.1f}" y="{y + 66}" class="lbl">{label}</text></g>'
        )
    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    span = f"{first.strftime('%b %-d')} – {last.strftime('%b %-d, %Y')} · refreshed daily"
    return f"""{svg_open(STATS_W, f"{s['total']} contributions in the last {WEEKS} weeks")}
  <style>{base_css()}{STYLE}
    .num{{font-size:30px;font-weight:700;fill:{AMBER};}}
    .st{{opacity:0;animation:in .5s cubic-bezier(.2,.7,.2,1) forwards;}}
    @keyframes in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
  </style>{panel(STATS_W, HEIGHT, "activity --summary")}
  {''.join(tile_svg)}
  <text x="{sx0}" y="{sy0 + 2 * th + 12 + 24}" class="lbl">{span}</text>
  {scanlines(STATS_W, HEIGHT)}
</svg>
"""


def placeholder(width: int, prompt: str) -> str:
    """Shown only until the first workflow run replaces it with real data."""
    return f"""{svg_open(width, "Activity loading")}
  <style>{base_css()}{STYLE}</style>{panel(width, HEIGHT, prompt)}
  <text x="{PAD}" y="80" class="lbl">fetching contributions …</text>
  {scanlines(width, HEIGHT)}
</svg>
"""


if __name__ == "__main__":
    if sys.argv[1:] == ["--placeholder"]:
        print("wrote", write("activity-graph.svg", placeholder(GRAPH_W, f"activity --last {WEEKS}w")))
        print("wrote", write("activity-stats.svg", placeholder(STATS_W, "activity --summary")))
        sys.exit()
    all_days = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else fetch()
    recent = window(all_days)
    print("wrote", write("activity-graph.svg", graph(recent)))
    print("wrote", write("activity-stats.svg", summary(recent)))
