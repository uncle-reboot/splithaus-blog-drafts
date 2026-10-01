"""Render SplitHaus blog drafts into a static preview site mirroring app/blog/[slug]/page.tsx."""
import re, json, html, os, shutil, markdown
SRC='/home/general/splithaus_run/content/drafts'
OUT='/home/general/splithaus_run/content/site'
IMG={'how-to-share-a-vacation-home-with-family':('share.png','A lake house with a dock and canoes on calm water'),
     'family-cabin-rules-template':('rules.png','A cabin door with a checklist, a key, and a pet bed'),
     'inheriting-a-vacation-home-with-siblings':('siblings.png','A beach house with three doors and a row of chairs facing the sea')}
ORDER=list(IMG)
LIVE='https://www.splithaus.com'
CSS='''
:root{--cream:#faf6ef;--navy:#10242b;--teal:#1c3b44;--terra:#c05c3e;--sand:#d8cab0;--muted:#5b6b6b}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--navy);font:17px/1.7 "Hanken Grotesk",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.banner{background:var(--teal);color:#fff;font-size:13px;text-align:center;padding:8px 12px}
.wrap{max-width:48rem;margin:0 auto;padding:64px 24px}
a{color:var(--terra);text-underline-offset:4px}a:hover{color:#d4775b}
nav.crumb{font-size:14px;margin-bottom:32px}nav.crumb span{margin:0 8px;color:var(--muted)}
h1{font-family:"Fraunces",Georgia,serif;font-weight:400;font-size:2.25rem;line-height:1.2;margin:0}
.meta{margin-top:16px;font-size:14px;color:var(--muted)}
figure{margin:32px 0}figure img{width:100%;height:auto;border-radius:8px;display:block}
.short{margin:0 0 40px;border:1px solid rgba(16,36,43,.1);background:rgba(255,255,255,.6);border-radius:8px;padding:20px}
.short p.l{margin:0;font-size:13px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}.short p.a{margin:8px 0 0}
.body{color:var(--muted)}.body h2{font-family:"Fraunces",Georgia,serif;font-weight:400;color:var(--navy);font-size:1.6rem;margin:48px 0 12px}
.body h3{color:var(--navy);font-size:1.15rem;margin:32px 0 8px}.body strong{color:var(--navy)}
table{border-collapse:collapse;width:100%;font-size:15px;margin:24px 0}th,td{border-bottom:1px solid rgba(16,36,43,.12);padding:10px 8px;text-align:left;vertical-align:top}th{color:var(--navy)}
footer{margin-top:64px;border-top:1px solid rgba(16,36,43,.1);padding-top:24px;font-size:14px}
.card{display:block;border:1px solid rgba(16,36,43,.1);background:rgba(255,255,255,.6);border-radius:8px;padding:0;margin:24px 0;text-decoration:none;color:var(--navy);overflow:hidden}
.card img{width:100%;display:block}.card div{padding:20px}.card h2{font-family:"Fraunces",Georgia,serif;font-weight:400;margin:0 0 8px;font-size:1.4rem}.card p{margin:0;color:var(--muted)}
'''
FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz@9..144&family=Hanken+Grotesk:wght@400;600&display=swap" rel="stylesheet">'
BANNER='<div class="banner">Draft preview for review. Not published. Not indexed.</div>'
def page(title,desc,body):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><meta name="robots" content="noindex,nofollow">{FONTS}<link rel="stylesheet" href="{'' if 'index' in title else '../'}style.css"></head>
<body>{BANNER}{body}</body></html>'''
def parse(path):
    s=open(path).read()
    m=re.match(r'export const frontmatter = (\{[\s\S]*?\n\})\n',s)
    js=m.group(1)
    js=re.sub(r'(\n\s*)(\w+):',r'\1"\2":',js); js=re.sub(r'\{ name:',r'{ "name":',js); js=re.sub(r',(\s*[}\]])',r'\1',js)
    return json.loads(js), s[m.end():]
def links(h,slugs):
    def fix(m):
        u=m.group(1)
        if u.startswith('/blog/') and u[6:] in slugs: return f'href="../{u[6:]}/"'
        if u=='/blog': return 'href="../"'
        if u.startswith('/'): return f'href="{LIVE}{u}"'
        return m.group(0)
    return re.sub(r'href="([^"]+)"',fix,h)
os.makedirs(OUT,exist_ok=True); open(f'{OUT}/style.css','w').write(CSS); open(f'{OUT}/.nojekyll','w').write('')
posts=[]
for slug in ORDER:
    fm,body=parse(f'{SRC}/{slug}.mdx'); assert fm['slug']==slug
    img,alt=IMG[slug]
    h=markdown.markdown(body,extensions=['tables'])
    h=links(h,ORDER)
    art=f'''<article class="wrap"><nav class="crumb" aria-label="Breadcrumb"><a href="{LIVE}/">SplitHaus</a><span>/</span><a href="../">Guides</a></nav>
<header><h1>{html.escape(fm['title'])}</h1><p class="meta">By {html.escape(fm['author']['name'])}<span style="margin:0 8px">&middot;</span>Draft, not yet published</p></header>
<figure><img src="../images/{img}" alt="{html.escape(alt)}" width="1024" height="576"></figure>
<section class="short" aria-label="Short answer"><p class="l">Short answer</p><p class="a">{html.escape(fm['summary'])}</p></section>
<div class="body">{h}</div><footer><a href="../">More guides</a></footer></article>'''
    os.makedirs(f'{OUT}/{slug}',exist_ok=True)
    open(f'{OUT}/{slug}/index.html','w').write(page(fm['title']+' | SplitHaus',fm['description'],art))
    posts.append((slug,fm,img,alt))
cards=''.join(f'<a class="card" href="{s}/"><img src="images/{i}" alt="{html.escape(a)}"><div><h2>{html.escape(f["title"])}</h2><p>{html.escape(f["description"])}</p></div></a>' for s,f,i,a in posts)
idx=f'<main class="wrap"><nav class="crumb"><a href="{LIVE}/">SplitHaus</a></nav><h1>Guides</h1><p class="meta">Batch A drafts for review. Post 3 (SplitHaus vs a shared Google Calendar) is waiting on founder details.</p>{cards}</main>'
open(f'{OUT}/index.html','w').write(page('SplitHaus Guides (index) | draft preview','Draft preview of SplitHaus guides.',idx))
print('built',len(posts))
