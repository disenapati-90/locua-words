#!/usr/bin/env python3
"""Generate the Locua static SEO site from the app's own JSON data.
usage: build.py DATA_DIR OUT_DIR SITE_URL   (SITE_URL without trailing slash, may include a path)"""
import json, sys, os, re, shutil, unicodedata, datetime
from html import escape as e
from urllib.parse import quote

DATA, OUT, SITE = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/')
PLAY = 'https://play.google.com/store/apps/details?id=com.locua.app'
TODAY = datetime.date.today().isoformat()

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')

def play(campaign):
    ref = quote(f'utm_source=website&utm_medium=seo&utm_campaign={campaign}', safe='')
    return f'{PLAY}&referrer={ref}'

origins = json.load(open(f'{DATA}/origin_words.json', encoding='utf-8'))
bank = json.load(open(f'{DATA}/word_bank.json', encoding='utf-8'))

for o in origins:
    o['lang'] = o['originLanguage'].split(' (')[0]
    o['sub'] = o['originLanguage'][len(o['lang']):].strip(' ()')
    o['lslug'] = slug(o['lang'])
    o['slug'] = slug(o['word'])
by_lang = {}
for o in origins: by_lang.setdefault(o['lang'], []).append(o)
for v in by_lang.values(): v.sort(key=lambda x: x['word'].lower())
origin_by_word = {o['word'].lower(): o for o in origins}

themes = {}
for w in bank: themes.setdefault(w['theme'], []).append(w)
theme_slugs = {t: slug(t) for t in themes}

pages = []  # (path, priority)

def write(path, html, prio='0.6'):
    full = os.path.join(OUT, path.strip('/'), 'index.html') if not path.endswith('.html') else os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(html)
    if not path.endswith('.html'): pages.append((path if path.endswith('/') else path + '/', prio))
    elif path == 'index.html': pages.append(('/', prio))

CSS = """:root{--bg:#0b2b22;--card:#10382d;--text:#f3efe2;--muted:#b9c7bd;--gold:#e3b85a;--line:#1f5242}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:17px/1.65 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--gold)}.wrap{max-width:820px;margin:0 auto;padding:20px 16px 60px}
header.site{border-bottom:1px solid var(--line)}header.site .wrap{padding:14px 16px;display:flex;justify-content:space-between;gap:12px;align-items:center}
header.site a{text-decoration:none;font-weight:700;color:var(--text)}header.site a.cta{color:#0b2b22;background:var(--gold);padding:8px 14px;border-radius:999px;font-size:15px}
h1{font-size:2rem;line-height:1.2;margin:.3em 0}h2{font-size:1.25rem;margin:1.6em 0 .4em;color:var(--gold)}
.crumbs{font-size:14px;color:var(--muted)}.crumbs a{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:16px 0}
.big{font-size:1.1rem}.spell{color:var(--gold);font-size:1.3rem}.pill{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:999px;padding:2px 10px;color:var(--muted);margin-right:6px}
ul.grid{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
ul.grid li a{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;text-decoration:none;color:var(--text)}
ul.grid small{display:block;color:var(--muted)}
.btn{display:inline-block;background:var(--gold);color:#0b2b22;font-weight:700;text-decoration:none;padding:12px 20px;border-radius:999px}
button.say{background:none;border:1px solid var(--gold);color:var(--gold);border-radius:999px;padding:4px 12px;cursor:pointer;font-size:14px;margin-left:8px}
.promo{text-align:center}footer{color:var(--muted);font-size:14px;border-top:1px solid var(--line);margin-top:40px;padding-top:16px}"""

def layout(title, desc, path, body, campaign, jsonld=None, crumbs=None):
    url = f'{SITE}{path}'
    cr = ''
    if crumbs:
        cr = '<nav class="crumbs">' + ' › '.join(f'<a href="{SITE}{p}">{e(n)}</a>' for n, p in crumbs) + '</nav>'
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ''
    promo = f'''<div class="card promo"><p class="big"><b>Learn words like this every day</b><br>Locua is a free vocabulary app with word origins, story themes, quizzes and streaks.</p>
<a class="btn" href="{play(campaign)}" rel="noopener">Get Locua on Google Play</a></div>'''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:type" content="article"><meta property="og:url" content="{url}">
<meta name="theme-color" content="#0b2b22"><link rel="stylesheet" href="{SITE}/style.css">{ld}</head><body>
<header class="site"><div class="wrap"><a href="{SITE}/">Locua Words</a><a class="cta" href="{play(campaign)}" rel="noopener">Get the app</a></div></header>
<main class="wrap">{cr}{body}{promo}
<footer>Word data from the <a href="{play('footer')}" rel="noopener">Locua</a> app. Etymologies are simplified for learners.</footer></main>
<script>function say(t,l){{if(!('speechSynthesis' in window))return;var u=new SpeechSynthesisUtterance(t);u.lang=l;speechSynthesis.cancel();speechSynthesis.speak(u)}}</script>
</body></html>'''

# ---- word pages
for o in origins:
    siblings = [x for x in by_lang[o['lang']] if x is not o]
    same_level = [x for x in siblings if x['level'] == o['level']][:4]
    related = (same_level + [x for x in siblings if x not in same_level])[:6]
    lang_label = o['originLanguage']
    title = f"{o['word'].title()} – word origin ({o['lang']}) | Locua"
    desc = f"Where does the English word “{o['word']}” come from? Origin: {lang_label} ({o['originSpelling']}). Meaning: {o['meaning']}."[:300]
    body = f'''<h1>{e(o['word'])}</h1>
<p><span class="pill">{e(lang_label)}</span><span class="pill">{e(o['level'])}</span></p>
<div class="card"><p class="big"><b>Meaning:</b> {e(o['meaning'])}.</p>
<p><b>Origin:</b> {e(lang_label)} — <span class="spell">{e(o['originSpelling'])}</span>
<button class="say" onclick="say({e(json.dumps(o['originSpelling'], ensure_ascii=False))},'{e(o.get('pronunciationLocale') or 'en-US')}')" aria-label="Hear the original pronunciation">▶ Listen</button></p>
<p><b>Did you know?</b> {e(o['funFact'])}</p></div>
<h2>More English words from {e(o['lang'])}</h2><ul class="grid">''' + ''.join(
        f'<li><a href="{SITE}/origins/{x["lslug"]}/{x["slug"]}/">{e(x["word"])}<small>{e(x["meaning"][:60])}</small></a></li>' for x in related) + \
        f'</ul><p><a href="{SITE}/origins/{o["lslug"]}/">All English words from {e(o["lang"])} →</a></p>'
    ld = {"@context": "https://schema.org", "@type": "DefinedTerm", "name": o['word'], "description": o['meaning'],
          "inDefinedTermSet": f"{SITE}/origins/{o['lslug']}/"}
    write(f"/origins/{o['lslug']}/{o['slug']}", layout(title, desc, f"/origins/{o['lslug']}/{o['slug']}/", body,
          f"origin_{o['lslug']}", ld, [('Home', '/'), ('Word origins', '/origins/'), (o['lang'], f"/origins/{o['lslug']}/")]), '0.6')

# ---- language hubs
for lang, ws in by_lang.items():
    ls = slug(lang)
    title = f"{len(ws)} English words from {lang} – meanings & origins | Locua"
    desc = f"Explore {len(ws)} English words borrowed from {lang}, with meanings, original spellings and fun facts: {', '.join(w['word'] for w in ws[:5])} and more."
    body = f'<h1>English words from {e(lang)}</h1><p>English has borrowed many everyday and surprising words from {e(lang)}. Tap a word to see its meaning, original spelling and story.</p><ul class="grid">' + ''.join(
        f'<li><a href="{SITE}/origins/{ls}/{w["slug"]}/">{e(w["word"])}<small>{e(w["meaning"][:60])}</small></a></li>' for w in ws) + '</ul>'
    write(f'/origins/{ls}', layout(title, desc, f'/origins/{ls}/', body, f'hub_{ls}', None, [('Home', '/'), ('Word origins', '/origins/')]), '0.8')

write('/origins', layout('English word origins by language | Locua',
      f'Browse {len(origins)} English words by the language they came from: ' + ', '.join(by_lang)[:150],
      '/origins/', '<h1>English word origins by language</h1><ul class="grid">' + ''.join(
          f'<li><a href="{SITE}/origins/{slug(l)}/">{e(l)}<small>{len(ws)} words</small></a></li>' for l, ws in by_lang.items()) + '</ul>',
      'origins_index', None, [('Home', '/')]), '0.8')

# ---- theme pages
for t, ws in themes.items():
    ts = theme_slugs[t]
    title = f"{t} vocabulary: {len(ws)} words with meanings & examples | Locua"
    desc = f"Learn vocabulary through the story of “{t}”: " + ', '.join(w['word'] for w in ws[:5]) + ", with definitions, examples, synonyms and antonyms."
    items = ''
    for w in ws:
        ol = origin_by_word.get(w['word'].lower())
        extra = f' <a href="{SITE}/origins/{ol["lslug"]}/{ol["slug"]}/">Word origin →</a>' if ol else ''
        items += f'''<div class="card"><h2 style="margin-top:0">{e(w['word'])} <span class="pill">{e(w['level'])}</span></h2>
<p>{e(w['definition'])}.</p><p><i>“{e(w['sentence'])}”</i></p>
<p><b>Synonyms:</b> {e(', '.join(w['synonyms']))} &nbsp; <b>Opposites:</b> {e(', '.join(w['antonyms']))}{extra}</p></div>'''
    body = f'<h1>{e(t)} vocabulary</h1><p>Words you meet in a “{e(t)}” story, each with a clear meaning and an example sentence. In the Locua app these are read in story order so the context helps you remember them.</p>{items}'
    write(f'/themes/{ts}', layout(title, desc, f'/themes/{ts}/', body, f'theme_{ts}', None, [('Home', '/'), ('Vocabulary themes', '/themes/')]), '0.7')

write('/themes', layout('Vocabulary by story theme | Locua', f'{len(themes)} story themes to learn English vocabulary in context.', '/themes/',
      '<h1>Vocabulary by story theme</h1><ul class="grid">' + ''.join(
          f'<li><a href="{SITE}/themes/{theme_slugs[t]}/">{e(t)}<small>{len(ws)} words</small></a></li>' for t, ws in themes.items()) + '</ul>',
      'themes_index', None, [('Home', '/')]), '0.7')

# ---- home
write('index.html', layout('Locua Words – English word origins & vocabulary by theme',
      f'Discover where {len(origins)}+ English words come from and learn {len(bank)}+ vocabulary words through story themes.', '/',
      f'''<h1>Where do English words come from?</h1><p class="big">Explore {len(origins)} words borrowed from {len(by_lang)} language families, and learn vocabulary through {len(themes)} story themes.</p>
<h2>Word origins by language</h2><ul class="grid">''' + ''.join(
          f'<li><a href="{SITE}/origins/{slug(l)}/">{e(l)}<small>{len(ws)} words</small></a></li>' for l, ws in by_lang.items()) +
      '</ul><h2>Vocabulary by story theme</h2><ul class="grid">' + ''.join(
          f'<li><a href="{SITE}/themes/{theme_slugs[t]}/">{e(t)}<small>{len(ws)} words</small></a></li>' for t, ws in themes.items()) + '</ul>',
      'home'), '1.0')

# ---- static files
open(os.path.join(OUT, 'style.css'), 'w').write(CSS)
open(os.path.join(OUT, '404.html'), 'w').write(layout('Page not found | Locua Words', 'Page not found', '/404.html', '<h1>Page not found</h1><p><a href="' + SITE + '/">Back to Locua Words</a></p>', 'notfound'))
open(os.path.join(OUT, '.nojekyll'), 'w').write('')
open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
    f'<url><loc>{SITE}{p}</loc><lastmod>{TODAY}</lastmod><priority>{pr}</priority></url>\n' for p, pr in pages) + '</urlset>\n'
open(os.path.join(OUT, 'sitemap.xml'), 'w').write(sm)
print(f'{len(pages)} pages: {len(origins)} words, {len(by_lang)} hubs, {len(themes)} themes')
