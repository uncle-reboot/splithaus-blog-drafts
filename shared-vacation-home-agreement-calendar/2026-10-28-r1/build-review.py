"""Build one immutable review revision using the established preview CSS."""
import ast
import html
import json
import re
import sys
from pathlib import Path
import markdown

p = Path(sys.argv[1]).resolve()
meta = json.loads((p / 'frontmatter.json').read_text())
source = (p / 'article.md').read_text()
assert source.startswith('# ' + meta['title'] + '\n')
body = source.split('\n', 1)[1].lstrip()
short = re.search(r'\*\*Short answer:\*\* (.+)\n', body)
assert short and short.group(1) == meta['summary']
body = body[:short.start()] + body[short.end():]
(p / 'article.mdx').write_text('export const frontmatter = ' + json.dumps(meta, indent=2, ensure_ascii=False) + '\n\n' + body)
# Read literal layout tokens without executing the multi-article builder.
tree = ast.parse(Path('/home/general/splithaus_run/content/repo/source/build_preview.py').read_text())
constants = {}
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ('CSS', 'FONTS'):
                constants[target.id] = ast.literal_eval(node.value)
css = constants['CSS'] + '\nbody{overflow-wrap:anywhere}blockquote{margin:1.5rem 0;border-left:3px solid var(--sand);padding-left:1rem} .review-note{padding:1rem;border:1px solid var(--border);border-radius:1rem;margin:1rem 0} @media(max-width:600px){.wrap{padding:1.5rem 1.125rem}}'
(p / 'style.css').write_text(css)
md = markdown.Markdown(extensions=['tables', 'toc'])
rendered = md.convert(body)
toc = ''.join('<li><a href="#' + t['id'] + '">' + html.escape(t['name']) + '</a></li>' for t in md.toc_tokens)
e = html.escape
page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow"><title>' + e(meta['title']) + ' | SplitHaus — Review draft</title>'
        '<meta name="description" content="' + e(meta['description']) + '">' + constants['FONTS'] + '<link rel="stylesheet" href="style.css"></head><body>'
        '<div class="banner">APPROVAL REQUEST — REVIEW DRAFT — NOT PUBLISHED</div><main><article class="wrap">'
        '<nav class="crumb"><a href="https://www.splithaus.com/blog">SplitHaus guides</a> / Rules and agreements</nav>'
        '<header><h1>' + e(meta['title']) + '</h1><p class="meta">Proposed byline: Dan, subject to his approval. Proposed Friday: October 30, 2026; release hour pending.</p></header>'
        '<figure><img src="shared-vacation-home-agreement-calendar.webp" width="1024" height="576" alt="' + e(meta['image']['alt']) + '"></figure>'
        '<section class="short surface"><p class="label">Short answer</p><p class="a">' + e(meta['summary']) + '</p></section>'
        '<nav class="toc" aria-label="On this page"><p class="label">On this page</p><ol>' + toc + '</ol></nav><div class="body">' + rendered + '</div>'
        '<aside class="author"><p class="label">About the proposed author</p><p>Dan co-founded SplitHaus and has shared a family beach house across five generations.</p></aside>'
        '<aside class="review-note"><strong>Review decisions</strong><p>Matt: approve this revision or leave edits in the Slack thread. Dan: copy and byline approval required before publication.</p>'
        '<p>What Friday release hour, Pacific time, should we use? No production PR or deployment before explicit approval of the latest revision.</p>'
        '<p>Hero is a generated editorial illustration, not a product screenshot. <a href="article.md">Download draft Markdown</a> · <a href="article.mdx">Review MDX source</a></p></aside>'
        '</article></main></body></html>')
(p / 'preview.html').write_text(page)
print(json.dumps({'revision_dir': str(p), 'word_count': len(source.split()), 'h2_count': len(md.toc_tokens), 'draft': meta['draft'], 'reviewState': meta['reviewState']}))
