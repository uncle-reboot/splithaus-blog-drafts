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
    (1, 'how-to-share-a-vacation-home-with-family', 'calendar', 'share.png', 'A lake house with a dock and canoes on calm water', None),
    (5, 'who-gets-the-fourth-of-july', 'calendar', None, None, 'Who gets the Fourth of July? A holiday rotation example'),
    (8, 'when-one-family-never-uses-the-vacation-home', 'calendar', None, None, 'When one family never uses the house'),
    (10, 'vacation-home-calendar-template', 'calendar', None, None, 'Replacing the family spreadsheet: a vacation home calendar template'),
    (2, 'family-cabin-rules-template', 'rules', 'rules.png', 'A cabin door with a checklist, a key, and a pet bed', None),
    (6, 'shared-vacation-home-agreement-calendar', 'rules', None, None, 'The calendar clauses of a shared vacation home agreement'),
    (9, 'annual-vacation-home-meeting-agenda', 'rules', None, None, 'Running the annual vacation home meeting'),
    (4, 'inheriting-a-vacation-home-with-siblings', 'family', 'siblings.png', 'A beach house with three doors and a row of chairs facing the sea', None),
    (7, 'how-to-share-a-vacation-house-with-friends', 'family', None, None, 'How to share a vacation house with friends'),
    (11, 'get-every-household-involved-shared-house', 'family', None, None, 'Getting every household to take part'),
    (12, 'five-generations-one-house', 'family', None, None, 'Five generations, one house'),
    (3, 'splithaus-vs-google-calendar', 'tools', None, None, 'SplitHaus vs a shared Google Calendar'),
]
TOPICS = {
    'calendar': ('Splitting the calendar', 'How families divide weeks, holidays, and the nights nobody uses.', 'how-to-share-a-vacation-home-with-family'),
    'rules': ('Rules and agreements', 'House rules, written plans, and the yearly meeting that keeps them current.', 'family-cabin-rules-template'),
    'family': ('Family situations', 'Siblings, friends, growing families, and keeping everyone involved.', 'inheriting-a-vacation-home-with-siblings'),
    'tools': ('Choosing a tool', 'When a shared calendar is enough, and when a family wants more.', None),
}
START_HERE = 'how-to-share-a-vacation-home-with-family'
import csv
SLOT = {r['slug']: r['slot'] for r in csv.DictReader(open('/home/general/splithaus_run/content/splithaus-content-tracker.csv'))}
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
:root{--cream:#faf6ef;--navy:#10242b;--teal:#1c3b44;--terra:#c05c3e;--sand:#d8cab0;--muted:#5b6b6b;--line:rgba(16,36,43,.12)}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--navy);font:17px/1.7 "Hanken Grotesk",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.banner{background:var(--teal);color:#fff;font-size:13px;text-align:center;padding:8px 12px}
.wrap{max-width:48rem;margin:0 auto;padding:56px 24px}.wide{max-width:72rem}
a{color:var(--terra);text-underline-offset:4px}a:hover{color:#d4775b}
nav.crumb{font-size:14px;margin-bottom:28px}nav.crumb span{margin:0 8px;color:var(--muted)}
h1{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:2.25rem;line-height:1.2;margin:0}
.lead{font-size:1.15rem;color:var(--muted);max-width:44rem;margin:16px 0 0}
.meta{margin-top:14px;font-size:14px;color:var(--muted)}
figure{margin:28px 0}figure img{width:100%;height:auto;border-radius:8px;display:block}
.short{margin:0 0 28px;border:1px solid var(--line);background:rgba(255,255,255,.6);border-radius:8px;padding:20px}
.label{margin:0;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.short p.a{margin:8px 0 0}
.toc{margin:0 0 36px;border-left:3px solid var(--sand);padding:4px 0 4px 18px}.toc ol{margin:8px 0 0;padding-left:20px;font-size:15px}.toc li{margin:2px 0}
.body{color:var(--muted)}.body h2{font-family:"Fraunces",Georgia,serif;font-weight:400;color:var(--navy);font-size:1.6rem;margin:44px 0 12px;scroll-margin-top:16px}
.body h3{color:var(--navy);font-size:1.15rem;margin:28px 0 8px}.body strong{color:var(--navy)}
table{border-collapse:collapse;width:100%;font-size:15px;margin:24px 0}th,td{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left;vertical-align:top}th{color:var(--navy)}
.grid{display:grid;align-items:stretch;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;margin:16px 0 0}
.card{display:flex;flex-direction:column;border:1px solid var(--line);background:rgba(255,255,255,.65);border-radius:10px;overflow:hidden;text-decoration:none;color:var(--navy)}
a.card:hover{border-color:var(--terra)}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block}
.card .ph{display:block;aspect-ratio:16/9;background:repeating-linear-gradient(135deg,#efe8db 0 12px,#f4eee4 12px 24px)}
.card div.t{padding:16px 18px 18px}.card h3{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:1.2rem;line-height:1.3;margin:0 0 6px}
.card p{margin:0;font-size:15px;color:var(--muted);line-height:1.5}
.card.soon{background:transparent;border:1px dashed rgba(16,36,43,.25);box-shadow:none}.card.soon div.t{padding:18px}.card.soon h3{color:var(--muted);font-size:1.1rem}.pill{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.card.feature{display:grid;grid-template-columns:1.3fr 1fr;margin-top:12px}
.card.feature img{height:100%;aspect-ratio:auto;min-height:280px}.card.feature div.t{padding:28px;align-self:center}.card.feature h3{font-size:1.6rem}
@media(max-width:760px){.card.feature{grid-template-columns:1fr}.card.feature img{min-height:0;aspect-ratio:16/9}}
section.topic{margin-top:56px}section.topic h2{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:1.7rem;margin:0}
section.topic p.d{margin:4px 0 0;color:var(--muted)}
.faq{margin-top:64px}.faq h2{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:1.7rem;margin:0 0 8px}
.faq details{border-bottom:1px solid var(--line);padding:14px 0}.faq summary{cursor:pointer;font-weight:600}.faq p{margin:8px 0 0;color:var(--muted)}
.cta{margin-top:64px;background:var(--teal);color:#fff;border-radius:12px;padding:32px}.cta h2{font-family:"Fraunces",Georgia,serif;font-weight:400;margin:0 0 8px;font-size:1.6rem}
.cta p{margin:0 0 18px;color:#dfe7e7}.btn{display:inline-block;background:var(--terra);color:#fff;text-decoration:none;padding:10px 18px;border-radius:8px;font-weight:600}.btn:hover{color:#fff;background:#d4775b}
.related{margin-top:56px;border-top:1px solid var(--line);padding-top:28px}.related h2{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:1.5rem;margin:0}
.part{font-size:14px;color:var(--muted);margin:0 0 18px}
\n.card p.by{margin-top:10px;font-size:13px;color:var(--muted)}\n.author{margin-top:48px;border-top:1px solid var(--line);padding-top:20px}.author p{margin:4px 0 0}\nfooter.f{margin-top:40px;font-size:14px}
'''
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz@9..144&family=Hanken+Grotesk:wght@400;600&display=swap" rel="stylesheet">'
BANNER = '<div class="banner">Draft preview for review. Not published. Not indexed.</div>'
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
           f'<section class="short" aria-label="Short answer"><p class="label">Short answer</p><p class="a">{e(fm["summary"])}</p></section>'
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
       f'<p class="lead">Practical guides for families and friends who share a vacation home: how to split the calendar, '
       f'write house rules everyone agrees on, and handle the situations that come up as a family grows.</p>'
       f'<section class="topic" style="margin-top:36px"><p class="label">Start here</p>{card(START_HERE, "", feature=True)}</section>'
       f'{sections}'
       f'<section class="faq"><h2>Common questions</h2>{faq}</section>'
       f'<section class="cta"><h2>Make your own house plan</h2><p>The free Shared House Playbook walks your family through these decisions '
       f'one question at a time and turns the answers into a one-page plan.</p><a class="btn" href="{LIVE}/playbook">Open the Playbook</a></section>'
       f'<p class="meta" style="margin-top:32px">Preview note: grey "Coming soon" cards show the planned structure. The live site lists only published guides.</p>'
       f'</main>')
open(f'{OUT}/index.html', 'w').write(page('Guides to sharing a vacation home | SplitHaus',
                                          'Practical guides for families who share a vacation home: splitting the calendar, house rules, and family situations.', hub, 0))
print('built', len(drafts), 'articles + hub')
