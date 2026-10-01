"""Generate in-article diagrams as SVG in SplitHaus brand colors (BRAND_GUIDELINES.md 3.2, 3.3).

Run: python3 make_diagrams.py  -> writes to content/site/images and the app's public/blog/images.
Diagrams are hypothetical examples; captions in the articles say so.
"""
import html, os

OUT_DIRS = ['/home/general/splithaus_run/content/site/images',
            '/home/general/splithaus_run/blog-impl/beach-mgr/apps/splithaus/public/blog/images']
CREAM, CARD, NAVY, MUTED, BORDER, SAND, TERRA_DEEP = '#faf6ef', '#ffffff', '#10242b', '#5b6b6b', '#d8cab0', '#d8cab0', '#a84e32'
GROUP = {'A': ('#c05c3e', '#ffffff'), 'B': ('#356f66', '#ffffff'), 'C': ('#1a3a4a', '#ffffff')}
OPEN_FILL, OPEN_STROKE = '#ffffff', '#b9a98c'
FONT = "'Hanken Grotesk', 'Helvetica Neue', Arial, sans-serif"
SERIF = "Newsreader, Georgia, 'Times New Roman', serif"
e = html.escape


def svg(w, h, body, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" '
            f'aria-labelledby="t d"><title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc>'
            f'<rect width="{w}" height="{h}" rx="16" fill="{CREAM}"/>{body}</svg>\n')


def text(x, y, s, size=14, weight=400, fill=NAVY, anchor='start', family=FONT, spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ''
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}>{e(s)}</text>')


def who_gets_july():
    """Compact on purpose: it must stay legible at phone width (about 340px)."""
    cell, gap = 62, 6
    rows = [
        ('Fixed weeks', 'Group B has July every year', ['BBBB'] * 3),
        ('Take turns in a rotation', 'July moves to different groups', ['CCAA', 'AABB', 'BBCC']),
        ('Draft your dates', 'Pick order rotates, so July changes hands', ['CABC', 'ACBA', 'BCAB']),
    ]
    left, top, year_h = 96, 108, 46
    W = left + 4 * (cell + gap) + 24
    block_h = 64 + 3 * year_h + 22
    H = top + len(rows) * block_h + 36
    b = [text(24, 40, 'WHO GETS JULY?', 15, 700, TERRA_DEEP, spacing=2.4),
         text(24, 72, 'Three groups, three years', 26, 400, NAVY, family=SERIF)]
    for i in range(4):
        b.append(text(left + i * (cell + gap) + cell / 2, top - 8, f'Wk {i + 1}', 14, 600, MUTED, 'middle'))
    for r, (name, hint, years) in enumerate(rows):
        y = top + r * block_h
        if r:
            b.append(f'<line x1="24" x2="{W - 24}" y1="{y + 4}" y2="{y + 4}" stroke="{BORDER}"/>')
        b.append(text(24, y + 34, name, 20, 700))
        b.append(text(24, y + 58, hint, 17, 400, MUTED))
        for yr, pattern in enumerate(years):
            yy = y + 70 + yr * year_h
            b.append(text(left - 12, yy + 27, f'Year {yr + 1}', 15, 600, MUTED, 'end'))
            for i, g in enumerate(pattern):
                x = left + i * (cell + gap)
                fill, ink = GROUP[g]
                b.append(f'<rect x="{x}" y="{yy}" width="{cell}" height="38" rx="8" fill="{fill}"/>')
                b.append(text(x + cell / 2, yy + 26, g, 18, 700, ink, 'middle'))
    b.append(text(24, H - 16, 'Example only', 14, 400, MUTED))
    desc = ('Hypothetical example of the four July weeks over three years for Groups A, B and C. With fixed weeks, '
            'Group B has all of July every year. With turns in a rotation, July moves to different groups each year. '
            'In a draft whose pick order rotates, the July weeks are split across the groups and change hands each year.')
    return svg(W, H, ''.join(b), 'Who gets July under three ways of sharing', desc)


def release_date():
    W, H = 960, 330
    b = [text(32, 44, 'A RELEASE DATE', 12, 600, TERRA_DEEP, spacing=2.2),
         text(32, 72, 'Unused time opens to everyone 14 days before', 22, 400, NAVY, family=SERIF)]
    x0, x1, ly = 70, 890, 200
    b.append(f'<line x1="{x0}" x2="{x1}" y1="{ly}" y2="{ly}" stroke="{BORDER}" stroke-width="3" stroke-linecap="round"/>')
    stops = [
        (x0 + 40, 'Spring', 'Group 1 has July 22 to 26', 'Nobody from Group 1 books it.', 'A', False),
        (480, 'July 8', 'Release date', 'Not booked 14 days before, so it opens to everyone.', None, True),
        (x1 - 40, 'July 22 to 26', 'Group 2 books it', 'The rule was agreed in advance.', 'B', False),
    ]
    for x, when, head, note, g, is_open in stops:
        if is_open:
            b.append(f'<circle cx="{x}" cy="{ly}" r="14" fill="{OPEN_FILL}" stroke="{TERRA_DEEP}" stroke-width="3"/>')
        else:
            b.append(f'<circle cx="{x}" cy="{ly}" r="14" fill="{GROUP[g][0]}"/>')
        b.append(text(x, ly - 30, when, 13, 600, MUTED, 'middle'))
        b.append(text(x, ly + 44, head, 16, 600, NAVY, 'middle'))
        # wrap note into two lines
        words, lines, cur = note.split(), [], ''
        for w in words:
            if len(cur) + len(w) + 1 > 34:
                lines.append(cur); cur = w
            else:
                cur = (cur + ' ' + w).strip()
        lines.append(cur)
        for i, ln in enumerate(lines):
            b.append(text(x, ly + 66 + i * 18, ln, 13, 400, MUTED, 'middle'))
    b.append(text(W - 32, H - 18, 'Example only', 12, 400, MUTED, 'end'))
    desc = ('Hypothetical example. Group 1 has July 22 to 26 but does not book it. On July 8, 14 days before, the '
            'dates open to everyone. Group 2 books them.')
    return svg(W, H, ''.join(b), 'How a release date works', desc)


files = {
    'who-gets-july-three-ways.svg': who_gets_july(),
}
for d in OUT_DIRS:
    os.makedirs(d, exist_ok=True)
    for name, body in files.items():
        open(f'{d}/{name}', 'w').write(body)
print({k: len(v) for k, v in files.items()})
