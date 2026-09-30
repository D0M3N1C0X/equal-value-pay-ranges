"""
Four SVG charts for the report, hand-written like the ones in pay-transparency-readiness-kit:
validated reference palette, light and dark steps inside each file, a <title> on every mark.
"""
from html import escape

STYLE = """<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7;
        --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --base:#0b0b0b; --up:#e34948; --down:#2a78d6; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#ffffff; --ink2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835;
          --s1:#3987e5; --s2:#d95926; --s3:#199e70; --base:#ffffff; --up:#e66767; --down:#3987e5; }
  }
  text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; fill: var(--ink2); font-size: 12px; }
  .title { fill: var(--ink); font-size: 15px; font-weight: 600; }
  .muted { fill: var(--muted); font-size: 11px; }
  .val { fill: var(--ink); font-variant-numeric: tabular-nums; paint-order: stroke; stroke: var(--surface);
         stroke-width: 4px; stroke-linejoin: round; }
  .inbar { fill: #ffffff; font-weight: 600; font-variant-numeric: tabular-nums; }
</style>"""


def _svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-label="{escape(label)}">{STYLE}<rect width="{w}" height="{h}" rx="8" fill="var(--surface)"/>'
            f'{"".join(body)}</svg>\n')


def m_eur(x, d=1):
    return f"€{x / 1e6:,.{d}f}M"


def _scale(d0, d1, r0, r1):
    return lambda v: r0 + (v - d0) / (d1 - d0) * (r1 - r0)


def _path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)



def pct(x, d=0, signed=False):
    sign = ("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")
    return f"{sign}{abs(x) * 100:.{d}f}%"


def k_eur(x):
    return f"€{x / 1e3:,.0f}k"


def market_position(rows, title, subtitle):
    """rows: (label, payroll / market). Bars from 1.0: above market orange, below blue."""
    W, top, band = 720, 96, 46
    H = top + band * len(rows) + 44
    x0, x1 = 170, W - 90
    lo, hi = 0.8, 1.2
    x = _scale(lo, hi, x0, x1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>',
            f'<text x="24" y="56">{escape(subtitle)}</text>']
    for v in (0.8, 0.9, 1.0, 1.1, 1.2):
        body.append(f'<line x1="{x(v):.1f}" y1="{top - 10}" x2="{x(v):.1f}" y2="{H - 38}" stroke="var(--grid)"/>')
        body.append(f'<text class="muted" x="{x(v):.1f}" y="{H - 20}" text-anchor="middle">{pct(v - 1, 0, True) if v != 1 else "market"}</text>')
    for i, (label, r) in enumerate(rows):
        y = top + i * band
        a, b = sorted((x(1.0), x(r)))
        colour = "var(--s2)" if r > 1 else "var(--s1)"
        body.append(f'<text x="{x0 - 12}" y="{y + 18}" text-anchor="end">{escape(label)}</text>')
        body.append(f'<rect x="{a:.1f}" y="{y + 4}" width="{max(b - a, 1):.1f}" height="22" rx="3" fill="{colour}">'
                    f'<title>{escape(label)}: payroll {pct(r - 1, 1, True)} against market</title></rect>')
        tx, anchor = (b + 8, "start") if r > 1 else (a - 8, "end")
        body.append(f'<text class="val" x="{tx:.1f}" y="{y + 20}" text-anchor="{anchor}">{pct(r - 1, 1, True)}</text>')
    body.append(f'<line x1="{x(1):.1f}" y1="{top - 10}" x2="{x(1):.1f}" y2="{H - 38}" stroke="var(--base)" stroke-width="1.5"/>')
    return _svg(W, H, body, title)


def family_compa(rows, title, subtitle):
    """rows: (family, [compa by country]). Dot = mean of the countries, line = their range."""
    W, top, band = 720, 100, 40
    H = top + band * len(rows) + 44
    x0, x1 = 170, W - 60
    lo, hi = 0.7, 1.5
    x = _scale(lo, hi, x0, x1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>',
            f'<text x="24" y="56">{escape(subtitle)}</text>']
    for v in (0.7, 0.9, 1.0, 1.1, 1.3, 1.5):
        body.append(f'<line x1="{x(v):.1f}" y1="{top - 12}" x2="{x(v):.1f}" y2="{H - 38}" stroke="var(--grid)"/>')
        body.append(f'<text class="muted" x="{x(v):.1f}" y="{H - 20}" text-anchor="middle">{v:.1f}</text>')
    body.append(f'<line x1="{x(1):.1f}" y1="{top - 12}" x2="{x(1):.1f}" y2="{H - 38}" stroke="var(--base)" stroke-width="1.5"/>')
    body.append(f'<text class="muted" x="{x(1) + 6:.1f}" y="{top - 16}">new midpoint</text>')
    for i, (fam, vals) in enumerate(rows):
        y = top + i * band + 12
        mean = sum(vals) / len(vals)
        colour = "var(--s2)" if mean > 1 else "var(--s1)"
        body.append(f'<text x="{x0 - 12}" y="{y + 4}" text-anchor="end">{escape(fam)}</text>')
        body.append(f'<line x1="{x(min(vals)):.1f}" y1="{y}" x2="{x(max(vals)):.1f}" y2="{y}" stroke="{colour}" '
                    f'stroke-width="3" stroke-linecap="round" opacity="0.45"/>')
        body.append(f'<circle cx="{x(mean):.1f}" cy="{y}" r="6" fill="{colour}"><title>{escape(fam)}: '
                    f'{mean:.2f} on average, {min(vals):.2f} to {max(vals):.2f} across countries</title></circle>')
        body.append(f'<text class="val" x="{x(max(vals)) + 10:.1f}" y="{y + 4}">{mean:.2f}</text>')
    return _svg(W, H, body, title)


def ranges(rows, title, subtitle, unit=1e3):
    """rows: (grade, min, mid, max, [(family, current midpoint)]). New range as a bar, current band
    midpoints of the roles in the grade as dots."""
    W, top, band = 720, 100, 44
    H = top + band * len(rows) + 60
    x0, x1 = 90, W - 40
    hi = max(max(r[3] for r in rows), max(m for r in rows for _, m in r[4])) * 1.05
    x = _scale(0, hi, x0, x1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>',
            f'<text x="24" y="56">{escape(subtitle)}</text>']
    step = 20000 if hi < 160000 else 40000
    v = 0
    while v <= hi:
        body.append(f'<line x1="{x(v):.1f}" y1="{top - 12}" x2="{x(v):.1f}" y2="{H - 54}" stroke="var(--grid)"/>')
        body.append(f'<text class="muted" x="{x(v):.1f}" y="{H - 36}" text-anchor="middle">{k_eur(v)}</text>')
        v += step
    for i, (g, lo, mid, mx, current) in enumerate(rows):
        y = top + i * band
        body.append(f'<text x="{x0 - 14}" y="{y + 18}" text-anchor="end">Grade {g}</text>')
        body.append(f'<rect x="{x(lo):.1f}" y="{y + 6}" width="{x(mx) - x(lo):.1f}" height="18" rx="3" fill="var(--s1)" '
                    f'opacity="0.35"><title>Grade {g}: {k_eur(lo)} to {k_eur(mx)}, midpoint {k_eur(mid)}</title></rect>')
        body.append(f'<line x1="{x(mid):.1f}" y1="{y + 3}" x2="{x(mid):.1f}" y2="{y + 27}" stroke="var(--s1)" stroke-width="2.5"/>')
        for fam, m in current:
            body.append(f'<circle cx="{x(m):.1f}" cy="{y + 15}" r="4.5" fill="var(--s2)" stroke="var(--surface)" '
                        f'stroke-width="1.5"><title>{escape(fam)}: current midpoint {k_eur(m)}</title></circle>')
    ly = H - 18
    body.append(f'<rect x="{x0}" y="{ly - 10}" width="22" height="10" rx="2" fill="var(--s1)" opacity="0.35"/>'
                f'<text class="muted" x="{x0 + 28}" y="{ly}">new range, with its midpoint</text>')
    body.append(f'<circle cx="{x0 + 250}" cy="{ly - 5}" r="4.5" fill="var(--s2)"/>'
                f'<text class="muted" x="{x0 + 260}" y="{ly}">current band midpoint of a role in the grade</text>')
    return _svg(W, H, body, title)


def positions(rows, title, subtitle):
    """rows: (label, below, within, above) as shares. One stacked bar per country."""
    W, top, band = 720, 110, 44
    H = top + band * len(rows) + 20
    x0, x1 = 170, W - 40
    x = _scale(0, 1, x0, x1)
    body = [f'<text class="title" x="24" y="34">{escape(title)}</text>',
            f'<text x="24" y="56">{escape(subtitle)}</text>']
    for k, (name, colour) in enumerate((("Below the minimum", "var(--s1)"), ("Within", "var(--axis)"),
                                        ("Above the maximum", "var(--s2)"))):
        lx = x0 + k * 170
        body.append(f'<rect x="{lx}" y="76" width="12" height="12" rx="2" fill="{colour}"/>'
                    f'<text x="{lx + 18}" y="86">{name}</text>')
    for i, (label, b, w, a) in enumerate(rows):
        y = top + i * band
        body.append(f'<text x="{x0 - 12}" y="{y + 19}" text-anchor="end">{escape(label)}</text>')
        start = 0.0
        for share, colour, name in ((b, "var(--s1)", "below the minimum"), (w, "var(--axis)", "within the range"),
                                    (a, "var(--s2)", "above the maximum")):
            body.append(f'<rect x="{x(start):.1f}" y="{y + 4}" width="{x(start + share) - x(start):.1f}" height="24" '
                        f'fill="{colour}"><title>{escape(label)}: {pct(share)} {name}</title></rect>')
            if share >= 0.06 and name != "within the range":
                body.append(f'<text class="inbar" x="{x(start + share / 2):.1f}" y="{y + 21}" text-anchor="middle">{pct(share)}</text>')
            start += share
    return _svg(W, H, body, title)
