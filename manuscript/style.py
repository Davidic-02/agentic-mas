"""Shared visual language for the chapter's figures.

One palette, one set of shadows, one card treatment, so the three figures
read as a set rather than as three separate drawings.
"""

FONT = "Arial"

INK = "#0F2740"       # near-black blue, for primary text
PRIMARY = "#1B4F80"
PRIMARY_2 = "#2E74B5"
ACCENT = "#3E8FD0"
MUTED = "#7A8899"
BORDER = "#D6E3F0"
TINT = "#F4F8FC"
PAPER = "#FDFEFF"

OK_FG, OK_BG, OK_BD = "#1E7A46", "#EFF7F1", "#B9DCC5"
BAD_FG, BAD_BG, BAD_BD = "#B3261E", "#FDF3F2", "#EFC6C2"
WARN_FG, WARN_BG, WARN_BD = "#8A6100", "#FFF9EC", "#E8D3A0"

DEFS = f"""  <defs>
    <linearGradient id="gPrimary" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#23598C"/>
      <stop offset="100%" stop-color="{PRIMARY}"/>
    </linearGradient>
    <linearGradient id="gAccent" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3D84C4"/>
      <stop offset="100%" stop-color="{PRIMARY_2}"/>
    </linearGradient>
    <filter id="lift" x="-30%" y="-30%" width="160%" height="180%">
      <feDropShadow dx="0" dy="1.4" stdDeviation="2.2"
                    flood-color="#0F2740" flood-opacity="0.13"/>
    </filter>
    <filter id="liftSoft" x="-30%" y="-30%" width="160%" height="180%">
      <feDropShadow dx="0" dy="1" stdDeviation="1.6"
                    flood-color="#0F2740" flood-opacity="0.08"/>
    </filter>
    <marker id="arw" markerWidth="8" markerHeight="8" refX="7" refY="4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0.5,1 L7,4 L0.5,7" fill="none" stroke="{PRIMARY}"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arwMute" markerWidth="8" markerHeight="8" refX="7" refY="4"
            orient="auto" markerUnits="strokeWidth">
      <path d="M0.5,1 L7,4 L0.5,7" fill="none" stroke="{MUTED}"
            stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>"""


def card(x, y, w, h, r=9, fill="#FFFFFF", stroke=BORDER, sw=1.1, lift="liftSoft"):
    f = f' filter="url(#{lift})"' if lift else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{f}/>')


def solid(x, y, w, h, r=9, grad="gPrimary"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
            f'fill="url(#{grad})" filter="url(#lift)"/>')


def txt(x, y, s, size=13, fill=INK, weight="normal", anchor="start",
        spacing=None, style=None):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}"{a}{ls}{st}>{s}</text>')


def eyebrow(x, y, s, fill=MUTED):
    """Small-caps section label with tracking."""
    return txt(x, y, s.upper(), size=10.5, fill=fill, weight="bold", spacing="1.3")


def link(x1, y1, x2, y2, muted=False, dash=None, width=1.5):
    c = MUTED if muted else PRIMARY
    m = "arwMute" if muted else "arw"
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" '
            f'stroke-width="{width}" stroke-linecap="round"{d} '
            f'marker-end="url(#{m})"/>')


def plain(x1, y1, x2, y2, color=BORDER, width=1.4):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round"/>')


def note(x, y, w, h, title, lines, fg, bg, bd):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{bg}" '
           f'stroke="{bd}" stroke-width="1.1"/>',
           txt(x + 16, y + 24, title, size=12.5, fill=fg, weight="bold")]
    for i, ln in enumerate(lines):
        out.append(txt(x + 16, y + 44 + i * 17, ln, size=11.8, fill=INK))
    return "\n  ".join(out)


def cross(cx, cy, r=6.5, w=2.1, color=BAD_FG):
    return (f'<g stroke="{color}" stroke-width="{w}" stroke-linecap="round">'
            f'<line x1="{cx-r}" y1="{cy-r}" x2="{cx+r}" y2="{cy+r}"/>'
            f'<line x1="{cx-r}" y1="{cy+r}" x2="{cx+r}" y2="{cy-r}"/></g>')


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}">\n{DEFS}\n'
            f'  <rect width="{w}" height="{h}" fill="{PAPER}"/>\n  {body}\n</svg>\n')
