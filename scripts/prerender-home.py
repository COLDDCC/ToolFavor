"""Prerender the homepage directory into static HTML for every locale.

    python3 scripts/prerender-home.py

The catalog lives in each page's inline `const data=[...]` and is drawn by
render() in the browser. Crawlers and no-JS visitors used to see an empty
"Explore the collection" section, so this script writes the same initial
state render() produces (category "All", featured order, first page of cards,
the category chips, the result count) straight into the HTML. render() still
runs on load and replaces it with identical markup, so filters keep working.

It also writes the copyright year into the footer.

build-ja.py and build-zh.py call this automatically at the end; run it by hand
after editing index.html without rebuilding the localized pages.
Output is deterministic (apart from the year), so re-running it is a no-op.
"""
from pathlib import Path
from html import escape
from urllib.parse import quote
import datetime, json, re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'ja/index.html', 'zh-cn/index.html']

# Mirrors the strings render() uses on each locale page (see build-ja.py / build-zh.py).
STRINGS = {
    'en': {'pricing': {'freemium': 'Freemium', 'free': 'Free', 'paid': 'Paid'},
           'details': 'Details →', 'visit': 'Visit ↗',
           'aria_details': lambda n: 'View details for ' + n,
           'aria_visit': lambda n: 'Visit ' + n + ' (opens in new tab)',
           'count': lambda total, shown: f'{total} curated results · Showing {shown}'},
    'ja': {'pricing': {'freemium': '無料プランあり', 'free': '無料', 'paid': '有料'},
           'details': '詳細 →', 'visit': 'サイトへ ↗',
           'aria_details': lambda n: n + 'の詳細',
           'aria_visit': lambda n: n + 'を開く（新しいタブ）',
           'count': lambda total, shown: f'{total}件中 {shown}件を表示'},
    'zh-CN': {'pricing': {'freemium': '有免费方案', 'free': '免费', 'paid': '付费'},
              'details': '查看详情 →', 'visit': '访问网站 ↗',
              'aria_details': lambda n: '查看' + n + '详情',
              'aria_visit': lambda n: '访问' + n + '（新标签页）',
              'count': lambda total, shown: f'共 {total} 个结果 · 已显示 {shown} 个'},
}


def js_value(h, name):
    start = h.index('const ' + name + '=') + len('const ' + name + '=')
    return json.JSONDecoder().raw_decode(h[start:])[0]


def js_single_quoted(h, start_marker, end_char):
    start = h.index(start_marker) + len(start_marker)
    return h[start:h.index(end_char, start)]


def page_strings(h, lang):
    """Read the locale's JS strings from the page itself when they are present."""
    s = dict(STRINGS[lang])
    m = re.search(r"detail\?'([^']*)':'([^']*)';foot\.append", h)
    if m:
        s['details'], s['visit'] = m[1], m[2]
    return s


def card(x, s, labels, detail_pages, tools_prefix):
    name, domain, desc, cat, pricing = x[0], x[1], x[2], x[3], x[5]
    detail = detail_pages.get(domain)
    if detail:
        href = detail if detail.startswith('/') else tools_prefix + detail
        extra = ''
        aria = s['aria_details'](name)
    else:
        href = 'https://' + domain.rstrip('/') + '/'
        extra = ' target="_blank" rel="noopener noreferrer"'
        aria = s['aria_visit'](name)
    host = domain.split('/')[0]
    favicon = 'https://www.google.com/s2/favicons?domain=' + quote(host, safe='') + '&sz=128'
    tags = [labels.get(cat, cat), s['pricing'].get(pricing, s['pricing']['paid'])]
    return (f'<a class="card" href="{escape(href)}"{extra} aria-label="{escape(aria)}">'
            f'<div class="cardtop"><span class="logo"><img class="site-favicon" src="{escape(favicon)}" alt="" '
            f'loading="lazy" decoding="async" referrerpolicy="no-referrer"></span>'
            f'<div><div class="name">{escape(name, quote=False)}</div><div class="domain">{escape(domain, quote=False)}</div></div></div>'
            f'<p class="desc">{escape(desc, quote=False)}</p>'
            f'<div class="foot"><div>' + ''.join(f'<span class="tag">{escape(t, quote=False)}</span>' for t in tags) +
            f'</div><span class="visit">{escape(s["details"] if detail else s["visit"], quote=False)}</span></div></a>')


def between(h, marker, inner):
    pattern = re.compile(r'<!-- prerender:' + marker + r' -->.*?<!-- /prerender:' + marker + r' -->', re.S)
    block = '<!-- prerender:' + marker + ' -->' + inner + '<!-- /prerender:' + marker + ' -->'
    if not pattern.search(h):
        raise SystemExit(f'missing <!-- prerender:{marker} --> markers')
    return pattern.sub(lambda m: block, h, count=1)


def prerender(path, year):
    p = ROOT / path
    h = p.read_text()
    lang = re.search(r'<html lang="([^"]+)"', h)[1]
    s = page_strings(h, lang)
    data = js_value(h, 'data')
    labels = js_value(h, 'labels') if 'const labels=' in h else {}
    cats = re.findall(r"'([^']*)'", js_single_quoted(h, 'const cats=[', ']'))
    detail_pages = dict(re.findall(r"'([^']*)':'([^']*)'", js_single_quoted(h, 'const detailPages={', '}')))
    tools_prefix = re.search(r"'(/(?:[a-z-]+/)?tools/)'\+detail", h)[1]
    page_size = int(re.search(r'const pageSize=(\d+)', h)[1])

    shown = data[:page_size]
    h = between(h, 'chips', ''.join(
        f'<button class="chip{" active" if c == "All" else ""}" type="button" aria-pressed="{"true" if c == "All" else "false"}">'
        f'{escape(labels.get(c, c), quote=False)}</button>' for c in cats))
    h = between(h, 'cards', ''.join(card(x, s, labels, detail_pages, tools_prefix) for x in shown))
    h = re.sub(r'(<p class="sub" id="count" aria-live="polite">)[^<]*(</p>)',
               lambda m: m[1] + escape(s['count'](len(data), len(shown)), quote=False) + m[2], h, count=1)
    h = re.sub(r'(<button class="secondary" id="loadMore" type="button" aria-controls="cards")( hidden)?>',
               lambda m: m[1] + ('' if len(data) > page_size else ' hidden') + '>', h, count=1)
    h = re.sub(r'(<span id="year">)[^<]*(</span>)', lambda m: m[1] + str(year) + m[2], h)
    p.write_text(h)
    return len(shown), len(data)


def main():
    year = datetime.date.today().year
    for path in PAGES:
        if not (ROOT / path).exists():
            continue
        if '<!-- prerender:cards -->' not in (ROOT / path).read_text():
            print(f'Skipped {path}: no prerender markers yet (rebuild it from index.html first).')
            continue
        if True:
            shown, total = prerender(path, year)
            print(f'Prerendered {path}: {shown} of {total} cards, footer year {year}.')


if __name__ == '__main__':
    main()
