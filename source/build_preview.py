"""Render SplitHaus blog drafts into a static preview site.

Article layout mirrors app/blog/[slug]/page.tsx, plus the guide-hub structure approved 2026-10-01:
hub page = H1 + intro, Start here, topic sections (card grids), FAQ, Playbook CTA;
article = breadcrumb with topic, hero, Short answer, table of contents, body, Related guides cards.
"""
import re, json, html, os, markdown

SRC = '/home/general/splithaus_run/content/drafts'
OUT = '/home/general/splithaus_run/content/site'
LIVE = 'https://www.splithaus.com'

# Every planned post. Only posts with a draft file render as real cards; the rest show as
# "Coming soon" in this preview so the full structure is visible. The real /blog lists published posts only.
POSTS = [
    # n, slug, topic, image, alt, short title for placeholder cards
    (1, 'how-to-share-a-vacation-home-with-family', 'calendar', 'share.webp', 'A lake house with a dock and canoes on calm water', None),
    (5, 'who-gets-the-fourth-of-july', 'calendar', 'fourth.webp', 'A lakeside cabin porch with red, white, and blue bunting and a table set for dinner', None),
    (8, 'when-one-family-never-uses-the-vacation-home', 'calendar', 'unused.webp', 'A porch with four chairs, one empty and set a little apart, by an open front door', None),
    (10, 'vacation-home-calendar-template', 'calendar', None, None, 'Replacing the family spreadsheet: a vacation home calendar template'),
    (2, 'family-cabin-rules-template', 'rules', 'rules.webp', 'A cabin door with a checklist, a key, and a pet bed', None),
    (6, 'shared-vacation-home-agreement-calendar', 'rules', None, None, 'The calendar clauses of a shared vacation home agreement'),
    (9, 'annual-vacation-home-meeting-agenda', 'rules', None, None, 'Running the annual vacation home meeting'),
    (4, 'inheriting-a-vacation-home-with-siblings', 'family', 'siblings.webp', 'A beach house with three doors and a row of chairs facing the sea', None),
    (7, 'how-to-share-a-vacation-house-with-friends', 'family', None, None, 'How to share a vacation house with friends'),
    (11, 'get-every-household-involved-shared-house', 'family', None, None, 'Getting every household to take part'),
    (12, 'five-generations-one-house', 'family', None, None, 'Five generations, one house'),
    (3, 'splithaus-vs-google-calendar', 'tools', None, None, 'SplitHaus vs a shared Google Calendar'),
]
TOPICS = {
    'calendar': ('Splitting the calendar', 'How families divide weeks, holidays, and the nights nobody uses.', 'how-to-share-a-vacation-home-with-family'),
    'rules': ('Rules and agreements', 'House rules, written plans, and the yearly meeting that keeps them current.', 'family-cabin-rules-template'),
    'family': ('Family and friends', 'Siblings, friends who bought a place together, growing families, and keeping everyone involved.', 'inheriting-a-vacation-home-with-siblings'),
    'tools': ('Choosing a tool', 'When a shared calendar is enough, and when a family wants more.', None),
}
START_HERE = 'how-to-share-a-vacation-home-with-family'
import csv
SLOT = {r['slug']: r['slot'] for r in csv.DictReader(open('/home/general/splithaus_run/content/splithaus-content-tracker.csv'))} if os.path.exists('/home/general/splithaus_run/content/splithaus-content-tracker.csv') else {}
AUTHOR_BIO = 'Dan co-founded SplitHaus and has shared a family beach house across five generations.'


def when(slug):
    s = SLOT.get(slug, '')
    return 'Publishes on launch day' if s == 'Launch' else f'Publishes {s.lower()} after launch' if s else 'Not yet scheduled'


def byline(slug, fm):
    return f'By {e(fm["author"]["name"])}<span style="margin:0 8px">&middot;</span>{when(slug)}'
HUB_FAQ = [
    ('What is the simplest way to share a vacation home?',
     'For two or three groups, a rotation of equal blocks with a release date for unused time is the easiest to explain and keep track of.',
     'how-to-share-a-vacation-home-with-family', 'Five ways to split the calendar'),
    ('What should family cabin rules cover?',
     'How many people can stay, guests and pets, what anyone can spend without asking, the checkout list, and how the rules change.',
     'family-cabin-rules-template', 'The family cabin rules template'),
    ('How do siblings share an inherited vacation home?',
     'Agree who shares it, how much time each household gets, how holidays work, and who looks after the house. Take ownership and tax questions to a professional.',
     'inheriting-a-vacation-home-with-siblings', 'Inheriting a vacation home with siblings'),
    ('Where do we start?',
     'Answer a few questions together and write the answers down. The free Shared House Playbook walks you through them one at a time.',
     None, None),
]

CSS = '''
/* Tokens from apps/splithaus/app/globals.css (BRAND_GUIDELINES.md section 3). */
:root{--cream:#faf6ef;--cream-dark:#f0e9dc;--paper:#fdfbf7;--ink-band:#10242b;--navy:#10242b;--terra:#c05c3e;--terra-deep:#a84e32;
--cta:#a84e32;--cta-hover:#8f4229;--sand:#d8cab0;--text-muted:#5b6b6b;--muted-fg:hsl(188 9% 39%);--border:hsl(36 36% 77%);--card:#fff;
--elev-card:0 1px 2px rgb(16 36 43 / .04);--elev-ledger-sm:0 6px 18px -8px rgb(16 36 43 / .18)}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--navy);font:1rem/1.65 "Hanken Grotesk",ui-sans-serif,system-ui,sans-serif}
.banner{background:var(--ink-band);color:var(--paper);font-size:.8125rem;text-align:center;padding:8px 12px}
.wrap{max-width:48rem;margin:0 auto;padding:3.5rem 1.5rem}.wide{max-width:72rem}
a{color:var(--terra-deep);text-underline-offset:4px}a:hover{color:var(--navy)}
nav.crumb{font-size:.875rem;margin-bottom:1.75rem}nav.crumb span{margin:0 8px;color:var(--text-muted)}
.serif,h1{font-family:"Newsreader","Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;text-wrap:balance}
h1{font-weight:500;letter-spacing:-.02em;line-height:1.06;font-size:clamp(2.25rem,6vw,3.3rem);margin:0}
article h1{font-size:clamp(2rem,5vw,2.85rem);line-height:1.1}
.lead{font-size:1.15rem;line-height:1.65;color:var(--text-muted);max-width:34rem;margin:1rem 0 0}
.meta{margin-top:1rem;font-size:.875rem;color:var(--muted-fg)}
figure{margin:1.75rem 0}figure img{width:100%;height:auto;border-radius:1rem;display:block}
.surface{border:1px solid var(--border);background:var(--card);border-radius:1rem;box-shadow:var(--elev-card)}
.short{margin:0 0 2rem;padding:1.25rem}
.label{margin:0;font-size:.6875rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--terra-deep)}
.label.rule{display:flex;align-items:center;gap:.75rem}.label.rule:before{content:"";height:1px;width:1.75rem;background:rgb(168 78 50 / .6)}
.short p.a{margin:.5rem 0 0}
.toc{margin:0 0 2.5rem;border-left:3px solid var(--sand);padding:4px 0 4px 1.25rem}.toc ol{margin:.5rem 0 0;padding-left:1.25rem;font-size:.875rem;line-height:1.5rem}
.body{color:var(--text-muted)}.body h2{font-family:"Newsreader",Georgia,serif;font-weight:400;letter-spacing:-.02em;line-height:1.2;color:var(--navy);font-size:1.5rem;margin:2.5rem 0 .75rem;scroll-margin-top:16px;text-wrap:balance}
.body h3{color:var(--navy);font-size:1.25rem;font-weight:600;margin:2rem 0 .5rem}.body strong{color:var(--navy)}
table{border-collapse:collapse;width:100%;font-size:.875rem;margin:1.5rem 0;font-variant-numeric:tabular-nums}th,td{border-bottom:1px solid var(--border);padding:.5rem .75rem;text-align:left;vertical-align:top}th{color:var(--navy)}
.grid{display:grid;align-items:stretch;grid-template-columns:repeat(auto-fill,minmax(16.25rem,1fr));gap:1.25rem;margin:1.25rem 0 0}
.card{display:flex;flex-direction:column;overflow:hidden;text-decoration:none;color:var(--navy);border:1px solid var(--border);background:var(--card);border-radius:1rem;box-shadow:var(--elev-card);transition:transform .2s,box-shadow .2s,border-color .2s}
@media (hover:hover) and (pointer:fine){a.card:hover{transform:translateY(-4px);box-shadow:var(--elev-ledger-sm);border-color:#d9a895;color:var(--navy)}}
@media (prefers-reduced-motion:reduce){.card{transition:none}a.card:hover{transform:none}}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.card div.t{padding:1.25rem}.card h3{font-family:"Newsreader",Georgia,serif;font-weight:400;letter-spacing:-.02em;font-size:1.25rem;line-height:1.25;margin:.5rem 0 .5rem;text-wrap:balance}
.card p{margin:0;font-size:.875rem;color:var(--muted-fg);line-height:1.5rem}
.card.soon{background:transparent;border:1px dashed var(--border);box-shadow:none}.card.soon h3{color:var(--text-muted);font-size:1.1rem}
.pill{font-size:.6875rem;font-weight:600;letter-spacing:.18em;text-transform:uppercase;color:var(--terra-deep)}
.card.feature{display:grid;grid-template-columns:1.3fr 1fr;margin-top:.75rem}
.card.feature img{height:100%;aspect-ratio:auto;min-height:17.5rem}.card.feature div.t{padding:2rem;align-self:center}.card.feature h3{font-size:1.75rem}
@media(max-width:760px){.card.feature{grid-template-columns:1fr}.card.feature img{min-height:0;aspect-ratio:16/9}.card.feature div.t{padding:1.25rem}}
section.topic{margin-top:3.5rem}section.topic h2,.faq h2{font-family:"Newsreader",Georgia,serif;font-weight:500;letter-spacing:-.03em;line-height:1.08;font-size:2rem;margin:0;text-wrap:balance}
@media(min-width:640px){section.topic h2,.faq h2{font-size:2.25rem}}
section.topic p.d{margin:.5rem 0 0;color:var(--text-muted);max-width:65ch}
.faq{margin-top:4rem}.faq .surface{margin-top:1.25rem;padding:0 1.25rem}
.faq details{border-top:1px solid var(--border)}.faq details:first-child{border-top:0}
.faq summary{cursor:pointer;font-weight:600;min-height:3rem;display:flex;align-items:center;padding:.75rem 0}.faq p{margin:0;padding-bottom:1rem;color:var(--text-muted);max-width:65ch}
.cta{margin-top:4rem;background:var(--ink-band);color:var(--paper);border-radius:24px;padding:2rem;box-shadow:0 10px 15px -3px rgb(0 0 0 / .1)}
.cta h2{font-family:"Newsreader",Georgia,serif;font-weight:400;letter-spacing:-.02em;margin:0 0 .5rem;font-size:1.875rem}
.cta p{margin:0 0 1.5rem;opacity:.85;max-width:65ch}
.btn{display:inline-flex;align-items:center;min-height:3rem;background:var(--cta);color:#fff;text-decoration:none;padding:.75rem 1.25rem;border-radius:.75rem;font-weight:600}.btn:hover{color:#fff;background:var(--cta-hover)}
.related{margin-top:3.5rem;border-top:1px solid var(--border);padding-top:2rem}.related h2{font-family:"Newsreader",Georgia,serif;font-weight:400;letter-spacing:-.02em;font-size:1.5rem;margin:0}
.part{font-size:.875rem;color:var(--muted-fg);margin:0 0 1.25rem}
.author{margin-top:3rem;padding:1.25rem;border:1px solid var(--border);background:rgb(250 246 239 / .5);border-radius:1rem}.author p{margin:.5rem 0 0;color:var(--navy)}.author p.label{margin:0;color:var(--terra-deep)}
.card p.by{margin-top:.75rem;font-size:.75rem}
.checks li{margin:8px 0}
footer.f{margin-top:2.5rem;font-size:.875rem}
'''
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,200..800;1,6..72,200..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">'
BANNER = '<div class="banner">Draft preview for Matt and Dan to review. Not published. Not indexed.</div>'
e = html.escape


def page(title, desc, body, depth):
    css = '../' * depth + 'style.css'
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="noindex,nofollow">{FONTS}'
            f'<link rel="stylesheet" href="{css}"></head><body>{BANNER}{body}</body></html>')


def parse(path):
    s = open(path).read()
    m = re.match(r'export const frontmatter = (\{[\s\S]*?\n\})\n', s)
    js = m.group(1)
    js = re.sub(r'(\n\s*)(\w+):', r'\1"\2":', js)
    js = re.sub(r'\{ name:', r'{ "name":', js)
    js = re.sub(r'\{ src:', r'{ "src":', js)
    js = re.sub(r', alt:', r', "alt":', js)
    js = re.sub(r',(\s*[}\]])', r'\1', js)
    return json.loads(js), s[m.end():]


drafts = {}
for n, slug, topic, img, alt, short in POSTS:
    p = f'{SRC}/{slug}.mdx'
    if os.path.exists(p):
        fm, body = parse(p)
        assert fm['slug'] == slug
        drafts[slug] = (fm, body)
meta = {slug: (n, topic, img, alt, short) for n, slug, topic, img, alt, short in POSTS}


def card(slug, prefix, feature=False):
    n, topic, img, alt, short = meta[slug]
    if slug in drafts:
        fm = drafts[slug][0]
        pic = f'<img src="{prefix}images/{img}" alt="{e(alt)}" loading="lazy">' if img else '<span class="ph"></span>'
        cls = 'card feature' if feature else 'card'
        return (f'<a class="{cls}" href="{prefix}{slug}/">{pic}<div class="t"><span class="pill">{e(TOPICS[topic][0])}</span>'
                f'<h3>{e(fm["title"])}</h3><p>{e(fm["description"])}</p><p class="by">{byline(slug, fm)}</p></div></a>')
    return (f'<div class="card soon"><div class="t"><span class="pill">Coming soon</span>'
            f'<h3>{e(short)}</h3></div></div>')


def fix_links(h, prefix):
    def fix(m):
        u = m.group(1)
        if u.startswith('/blog/') and u[6:] in drafts:
            return f'href="{prefix}{u[6:]}/"'
        if u == '/blog':
            return f'href="{prefix}"'
        if u.startswith('/'):
            return f'href="{LIVE}{u}"'
        return m.group(0)
    return re.sub(r'href="([^"]+)"', fix, h)


os.makedirs(OUT, exist_ok=True)
open(f'{OUT}/style.css', 'w').write(CSS)
open(f'{OUT}/.nojekyll', 'w').write('')

# ---- articles
for slug, (fm, body) in drafts.items():
    n, topic, img, alt, _ = meta[slug]
    tname, _, pillar = TOPICS[topic]
    md = markdown.Markdown(extensions=['tables', 'toc'])
    h = fix_links(md.convert(body), '../')
    toc = ''.join(f'<li><a href="#{t["id"]}">{e(t["name"])}</a></li>' for t in md.toc_tokens)
    part = ''
    if pillar and pillar != slug and pillar in drafts:
        part = (f'<p class="part">Part of <a href="../#{topic}">{e(tname)}</a>. '
                f'Start with <a href="../{pillar}/">{e(drafts[pillar][0]["title"])}</a>.</p>')
    same = [s for s in drafts if s != slug and meta[s][1] == topic]
    other = [s for s in drafts if s != slug and s not in same]
    rel = (same + other)[:3]
    related = f'<section class="related"><h2>Related guides</h2><div class="grid">{"".join(card(s, "../") for s in rel)}</div></section>' if rel else ''
    art = (f'<article class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="{LIVE}/">SplitHaus</a><span>/</span>'
           f'<a href="../">Guides</a><span>/</span><a href="../#{topic}">{e(tname)}</a></nav>'
           f'<header><h1>{e(fm["title"])}</h1><p class="meta">{byline(slug, fm)}</p></header>'
           f'<figure><img src="../images/{img}" alt="{e(alt)}" width="1024" height="576"></figure>'
           f'{part}'
           f'<section class="short surface" aria-label="Short answer"><p class="label">Short answer</p><p class="a">{e(fm["summary"])}</p></section>'
           f'<nav class="toc" aria-label="On this page"><p class="label">On this page</p><ol>{toc}</ol></nav>'
           f'<div class="body">{h}</div>'
           f'<aside class="author"><p class="label">About the author</p><p>{e(AUTHOR_BIO)}</p></aside>{related}'
           f'<footer class="f"><a href="../">All guides</a></footer></article>')
    os.makedirs(f'{OUT}/{slug}', exist_ok=True)
    open(f'{OUT}/{slug}/index.html', 'w').write(page(fm['title'] + ' | SplitHaus', fm['description'], art, 1))

# ---- hub
sections = ''
for key, (name, desc, _) in TOPICS.items():
    slugs = [s for n, s, t, *_ in POSTS if t == key and s != START_HERE]
    if not slugs:
        continue
    sections += (f'<section class="topic" id="{key}"><h2>{e(name)}</h2><p class="d">{e(desc)}</p>'
                 f'<div class="grid">{"".join(card(s, "") for s in slugs)}</div></section>')
faq = ''
for q, a, link, label in HUB_FAQ:
    more = f' <a href="{link}/">{e(label)}</a>' if link and link in drafts else f' <a href="{LIVE}/playbook">Open the Shared House Playbook</a>'
    faq += f'<details><summary>{e(q)}</summary><p>{e(a)}{more}</p></details>'
hub = (f'<main class="wrap wide"><nav class="crumb" aria-label="Breadcrumb"><a href="{LIVE}/">SplitHaus</a><span>/</span>Guides</nav>'
       f'<h1>Guides to sharing a vacation home</h1>'
       f'<p class="lead">Practical guides for everyone who shares a vacation home, whether family or friends: how to split the calendar, '
       f'write house rules everyone agrees on, and handle the situations that come up over the years.</p>'
       f'<section class="topic" style="margin-top:36px"><p class="label rule">Start here</p>{card(START_HERE, "", feature=True)}</section>'
       f'{sections}'
       f'<section class="faq"><h2>Common questions</h2><div class="surface">{faq}</div></section>'
       f'<section class="cta"><h2>Make your own house plan</h2><p>The free Shared House Playbook walks everyone who shares the house through these decisions, '
       f'one question at a time, and turns the answers into a one-page plan.</p><a class="btn" href="{LIVE}/playbook">Open the Playbook</a></section>'
       f'<p class="meta" style="margin-top:32px"><a href="review/">Review page for Matt and Dan</a>. Preview note: grey "Coming soon" cards show the planned structure. The live site lists only published guides.</p>'
       f'</main>')
open(f'{OUT}/index.html', 'w').write(page('Guides to sharing a vacation home | SplitHaus',
                                          'Practical guides for families and friends who share a vacation home: splitting the calendar, house rules, and the situations that come up over the years.', hub, 0))
# ---- review page for Matt and Dan
launch = [s for s in drafts if SLOT.get(s) == 'Launch']
rows = ''.join(
    f'<tr><td>{meta[s][0]}</td><td><a href="../{s}/">{e(drafts[s][0]["title"])}</a></td><td>{e(TOPICS[meta[s][1]][0])}</td>'
    f'<td>{len(re.findall(r"[A-Za-z0-9]+", drafts[s][1]))}</td><td>&#9744;</td><td>&#9744;</td></tr>' for s in launch)
review = f'''<main class="wrap wide"><nav class="crumb"><a href="../">Guides hub</a><span>/</span>Review</nav>
<h1>Launch batch: review</h1>
<p class="lead">Five guides publish together on launch day. Each one needs approval from both Matt and Dan before it goes live.
Dan's approval matters because every guide carries his byline.</p>
<section class="topic" style="margin-top:32px"><h2>The five launch guides</h2>
<table><thead><tr><th>#</th><th>Guide</th><th>Topic</th><th>Words</th><th>Matt</th><th>Dan</th></tr></thead><tbody>{rows}</tbody></table>
<p class="meta">Reply in chat with "approved" or your changes for each number. Approvals are recorded in the content tracker.</p></section>
<section class="topic"><h2>What to check in each guide</h2><ol class="checks">
<li><strong>Sounds like Dan.</strong> Would Dan say this? Change anything that does not sound like him. His name is on it.</li>
<li><strong>True to how families share a house.</strong> Flag anything that does not match real life, including Dan's family's house.</li>
<li><strong>No promises.</strong> Nothing should promise fairness, fewer arguments, a fuller house, savings, or speed.</li>
<li><strong>No legal, tax, or money advice.</strong> Ownership, estates, and taxes are pointed to a lawyer or tax advisor.</li>
<li><strong>No product claims or pricing.</strong> SplitHaus is not described or priced in these guides yet, on purpose.</li>
<li><strong>The examples are clearly made up.</strong> Worked examples say they are hypothetical. No real family names, addresses, or dates.</li>
<li><strong>The pictures.</strong> Each guide has an illustration. Say if any should change.</li>
<li><strong>On brand.</strong> Plain words a translation app would get right, no idioms, sentence case, and not family-only (friends co-own too). See BRAND_GUIDELINES.md section 2.</li>
<li><strong>Anything missing.</strong> A question a real family would ask that the guide does not answer.</li>
</ol></section>
<section class="topic"><h2>Already checked</h2><p class="d">Every guide passes the blog's own format and content checks, uses only approved claims,
has a short answer and FAQ, links to at least two other guides and to the Playbook, and carries the approved author line:
"Dan co-founded SplitHaus and has shared a family beach house across five generations."</p></section>
<section class="topic"><h2>After launch</h2><p class="d">One guide a week, reviewed the same way in monthly batches. Next up: SplitHaus vs a shared Google Calendar,
which needs Matt's example details and product screenshots first.</p></section>
</main>'''
os.makedirs(f'{OUT}/review', exist_ok=True)
open(f'{OUT}/review/index.html', 'w').write(page('Launch review | SplitHaus guides', 'Review page for the launch batch.', review, 1))
print('built', len(drafts), 'articles + hub + review page')
