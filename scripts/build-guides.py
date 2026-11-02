"""Generate comparison guide pages (hubs) from data/guides/*.json for every locale.

    python3 scripts/build-guides.py           # validate, then write pages + sitemap
    python3 scripts/build-guides.py --check   # validate only

A guide compares tools that already have detail pages in data/tools/. Tool names,
logos, links and review URLs come from the tool JSON; the guide JSON holds only the
comparison text. Each tool listed in a guide should carry a matching "guide" field
so its detail page links back to the hub. Output: /<slug>/, /ja/<slug>/, /zh-cn/<slug>/.
"""
from pathlib import Path
from html import escape
import importlib.util, json, re, sys

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('tool_pages', ROOT / 'scripts' / 'build-tool-pages.py')
tp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tp)

SITE, LOCALES, LANG_LABEL, UI = tp.SITE, tp.LOCALES, tp.LANG_LABEL, tp.UI
icon, ext, tool_logo, block = tp.icon, tp.ext, tp.tool_logo, tp.block
page_url, home_url, guide_url = tp.page_url, tp.home_url, tp.guide_url

GUIDES = ROOT / 'data' / 'guides'

EXTRA_CSS = """
.picks{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.pick{display:flex;flex-direction:column;gap:10px;padding:24px}
.pick .top-row{display:flex;align-items:center;gap:12px}.pick .top-row .logo{width:44px;height:44px;border-radius:12px}
.pick .for{font-size:13px;font-weight:600;color:var(--accent-ink);text-transform:none;margin:0}
.pick h3{margin:0;font-size:19px;letter-spacing:-.01em}.pick p{margin:0;color:var(--muted);font-size:15px}
.pick .go{margin-top:auto;font-size:14px;font-weight:600;color:var(--accent-ink);display:inline-flex;align-items:center;gap:6px}
.pick .go .ico{width:16px;height:16px}
.callout{padding:28px}.callout h3{margin:0 0 8px;font-size:20px}.callout p{margin:0;color:var(--muted)}
.guide-hero{padding:72px 0 24px}
#choose .steps{grid-template-columns:repeat(2,1fr)}
@media(max-width:620px){#choose .steps{grid-template-columns:1fr}}.guide-hero .lead{max-width:760px}.guide-hero .sublead{max-width:760px}
"""


def load(path):
    g = json.loads(path.read_text())
    assert g['slug'] == path.stem, f'{path.name}: slug must match file name'
    return g


def validate(g, tools_by_slug):
    errs = []
    for slug in g['tools']:
        t = tools_by_slug.get(slug)
        if not t:
            errs.append(f'unknown tool {slug!r}')
        elif t.get('guide', {}).get('slug') != g['slug']:
            errs.append(f'{slug}.json has no "guide" field pointing back to {g["slug"]}')
    for code in LOCALES:
        c = g['i18n'].get(code)
        if not c:
            errs.append(f'missing locale {code}')
            continue
        if len(c['title']) > 95:
            errs.append(f'[{code}] title is long ({len(c["title"])} chars)')
        if not 50 <= len(c['description']) <= 170:
            errs.append(f'[{code}] description length {len(c["description"])} (want 50–170)')
        for slug in g['tools']:
            if slug not in c['rows']:
                errs.append(f'[{code}] table row missing for {slug}')
            elif len(c['rows'][slug]) != len(c['columns']) - 1:
                errs.append(f'[{code}] row {slug} has {len(c["rows"][slug])} cells, want {len(c["columns"]) - 1}')
        for p in c['picks']:
            if p['tool'] not in g['tools']:
                errs.append(f'[{code}] pick for unlisted tool {p["tool"]!r}')
    return [f"{g['slug']}: {e}" for e in errs]


def json_ld(g, c, code, tools):
    url = SITE + guide_url(g['slug'], code)
    graph = [
        {'@type': 'CollectionPage', '@id': url, 'url': url, 'name': c['title'], 'description': c['description'],
         'inLanguage': LOCALES[code][1], 'dateModified': g['last_verified'],
         'isPartOf': {'@type': 'WebSite', 'name': 'ToolFavor', 'url': SITE + '/'},
         'mainEntity': {'@type': 'ItemList', 'itemListElement': [
             {'@type': 'ListItem', 'position': i, 'name': t['name'], 'url': SITE + page_url(t['slug'], code)}
             for i, t in enumerate(tools, 1)]}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': UI[code]['explore'], 'item': SITE + home_url(code)},
            {'@type': 'ListItem', 'position': 2, 'name': tools[0]['guide']['label'][code], 'item': url}]},
        {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in c['faq']]},
    ]
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def render(g, code, tools_by_slug):
    c, u = g['i18n'][code], UI[code]
    prefix, lang, _, og_locale = LOCALES[code]
    tools = [tools_by_slug[s] for s in g['tools']]
    canonical = SITE + guide_url(g['slug'], code)
    label = tools[0]['guide']['label'][code]

    alternates = ''.join(f'<link rel="alternate" hreflang="{LOCALES[k][2]}" href="{SITE + guide_url(g["slug"], k)}">' for k in LOCALES)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE + guide_url(g["slug"], "en")}">'
    head = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="theme-color" content="#fbfbfd"><title>{escape(c["title"])}</title>'
            f'<meta name="description" content="{escape(c["description"])}"><link rel="canonical" href="{canonical}">{alternates}'
            f'<meta property="og:type" content="article"><meta property="og:site_name" content="ToolFavor"><meta property="og:locale" content="{og_locale}">'
            f'<meta property="og:title" content="{escape(c["title"])}"><meta property="og:description" content="{escape(c["description"])}">'
            f'<meta property="og:url" content="{canonical}">'
            f'<link rel="icon" href="/favicon-96x96.png" sizes="96x96"><link rel="icon" href="/assets/toolfavor-mark.svg" type="image/svg+xml">'
            f'<script>document.documentElement.classList.add("js")</script>'
            f'<style>{tp.CSS.strip()}{EXTRA_CSS.strip()}</style><script type="application/ld+json">{json_ld(g, c, code, tools)}</script></head>')

    langs = ''.join(f'<a href="{guide_url(g["slug"], k)}" lang="{LOCALES[k][1]}" hreflang="{LOCALES[k][2]}"'
                    + (' aria-current="page"' if k == code else '') + f'>{LANG_LABEL[k]}</a>' for k in LOCALES)
    nav = (f'<header class="top"><div class="wrap"><a class="brand" href="{home_url(code)}"><img src="/assets/toolfavor-mark.svg" alt="" width="24" height="24">ToolFavor<span>.</span></a>'
           f'<nav class="navr" aria-label="Main"><a href="{home_url(code)}">{escape(u["explore"])}</a><a class="dev" href="{prefix}/developers">{escape(u["developers"])}</a>'
           f'<span class="langs" role="group" aria-label="Language">{langs}</span></nav></div></header>')

    crumb = (f'<nav class="crumb" aria-label="Breadcrumb"><a href="{home_url(code)}">{escape(u["explore"])}</a><i>/</i>'
             f'<span aria-current="page">{escape(label)}</span></nav>')
    hero = (f'<section class="hero guide-hero"><div class="sky" aria-hidden="true"><i class="orb a"></i><i class="orb b"></i><i class="orb c"></i><i class="orb d"></i></div>'
            f'<div class="wrap"><div class="intro">{crumb}<p class="eyebrow">{escape(c["kicker"])}</p>'
            f'<h1 class=long>{escape(c["h1"])}</h1><p class="lead">{escape(c["lead"])}</p><p class="sublead">{escape(c["sublead"])}</p>'
            f'<div class="cta-row"><a class="pill" href="#compare">{escape(c["table_title"].rstrip("。."))} {icon("arrow")}</a></div>'
            f'<p class="snap">{escape(c["snapshot"])} · {escape(u["verified"])} {g["last_verified"]}</p></div></div></section>')

    body = []
    cards = ''
    for p in c['picks']:
        t = tools_by_slug[p['tool']]
        cards += (f'<article class="pick glass-card reveal"><div class="top-row">{tool_logo(t)}<span><p class="for">{escape(p["for"])}</p>'
                  f'<h3>{escape(t["name"])}</h3></span></div><p>{escape(p["why"])}</p>'
                  f'<a class="go" href="{page_url(t["slug"], code)}">{escape(c["review_cta"])} {icon("arrow")}</a></article>')
    body.append(block('picks', c['picks_title'], f'<div class="picks">{cards}</div>', c['picks_sub']))

    thead = ''.join(f'<th scope="col">{escape(h)}</th>' for h in c['columns'])
    trs = ''
    for t in tools:
        name = f'<a href="{page_url(t["slug"], code)}">{escape(t["name"])}</a>'
        trs += (f'<tr><th scope="row"><span class="name">{tool_logo(t)}{name}</span></th>'
                + ''.join(f'<td>{escape(x)}</td>' for x in c['rows'][t['slug']]) + '</tr>')
    table = (f'<div class="table glass-card reveal"><table><thead><tr>{thead}</tr></thead><tbody>{trs}</tbody></table></div>'
             f'<p class="note">{escape(c["table_note"])}</p>')
    body.append(block('compare', c['table_title'], table, c['table_sub']))

    steps = ''.join(f'<article class="step glass-card reveal"><div class="n">{i:02d}</div><h3>{escape(s["title"])}</h3><p>{escape(s["text"])}</p></article>'
                    for i, s in enumerate(c['choose'], 1))
    callout = f'<div class="callout glass-card reveal" style="margin-top:16px"><h3>{escape(c["names_title"])}</h3><p>{escape(c["names_text"])}</p></div>'
    body.append(block('choose', c['choose_title'], f'<div class="steps">{steps}</div>{callout}'))

    items = ''.join(f'<details{" open" if i == 0 else ""}><summary>{escape(f["q"])}</summary><div class="a"><p>{escape(f["a"])}</p></div></details>'
                    for i, f in enumerate(c['faq']))
    body.append(block('faq', c['faq_title'], f'<div class="faq reveal">{items}</div>'))

    rel = ''.join(f'<a class="rel glass-card reveal" href="{page_url(t["slug"], code)}">{tool_logo(t)}'
                  f'<span><h3>{escape(t["name"])}</h3><p>{escape(t["i18n"][code]["lead"])}</p></span></a>' for t in tools)
    official = ' · '.join(ext(t['url'], escape(t['domain'])) for t in tools)
    body.append(block('reviews', c['reviews_title'],
                      f'<div class="cards">{rel}</div><p class="note">{escape(c["visit"])}: {official}</p>'
                      f'<p class="note">{escape(c["policy"])} <a href="{prefix}/contact">{escape(u["report"])} →</a></p>'))

    footer = (f'<footer><div class="wrap"><span>© {escape(u["footer"])}</span>'
              f'<a href="{home_url(code)}">{escape(u["more_tools"])} →</a></div></footer>')
    return (head + '<body>' + nav + '<main>' + hero + ''.join(body) + '</main>' + footer
            + f'<script>{tp.REVEAL_JS}</script></body></html>\n')


def update_sitemap(guides):
    path = ROOT / 'sitemap.xml'
    xml = path.read_text()
    for g in guides:
        for code in LOCALES:
            loc = SITE + guide_url(g['slug'], code)
            entry = f'<url><loc>{loc}</loc><lastmod>{g["last_verified"]}</lastmod></url>'
            pattern = re.compile(rf'<url><loc>{re.escape(loc)}</loc>.*?</url>')
            xml = pattern.sub(entry, xml) if pattern.search(xml) else xml.replace('</urlset>', entry + '\n</urlset>')
    path.write_text(xml)


def main():
    tools_by_slug = {t['slug']: t for t in tp.load_tools()}
    guides = [load(p) for p in sorted(GUIDES.glob('*.json'))]
    errors = [e for g in guides for e in validate(g, tools_by_slug)]
    if errors:
        print('Validation failed:\n  ' + '\n  '.join(errors))
        sys.exit(1)
    if '--check' in sys.argv:
        print(f'OK: {len(guides)} guides pass validation.')
        return
    for g in guides:
        for code in LOCALES:
            dest = ROOT / guide_url(g['slug'], code).lstrip('/') / 'index.html'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(g, code, tools_by_slug))
    update_sitemap(guides)
    print(f'Generated {len(guides) * len(LOCALES)} guide pages for {len(guides)} guides.')


if __name__ == '__main__':
    main()
