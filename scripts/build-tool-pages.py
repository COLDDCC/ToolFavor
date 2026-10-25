"""Generate tool detail pages from data/tools/*.json for every locale.

    python3 scripts/build-tool-pages.py           # validate, then write pages + sitemap
    python3 scripts/build-tool-pages.py --check   # validate only

See docs/detail-page-standard.md for the content standard, tiers and writing style.
"""
from pathlib import Path
from html import escape
from urllib.parse import urlparse, quote
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'tools'
SITE = 'https://toolfavor.com'
LOCALES = {  # key: (folder prefix, html lang, hreflang, og locale)
    'en': ('', 'en', 'en', 'en_US'),
    'ja': ('/ja', 'ja', 'ja', 'ja_JP'),
    'zh-cn': ('/zh-cn', 'zh-CN', 'zh-CN', 'zh_CN'),
}
LANG_LABEL = {'en': 'EN', 'ja': '日本語', 'zh-cn': '中文'}

UI = {
 'en': {
  'explore': 'Explore tools', 'developers': 'For developers',
  'visit': 'Get {name}', 'visit_web': 'Open {name}', 'fit_jump': 'Is it for me?', 'more_tools': 'Browse more tools',
  'titles': {'features': 'What it does.', 'steps': 'How it works.', 'fit': 'Is it for you?', 'compare': 'How it compares.',
             'alternatives': 'Other ways to do it.', 'faq': 'Questions, answered.', 'details': 'The fine print.', 'related': 'Keep exploring.'},
  'subs': {'compare': 'By approach and typical use. Not a hands-on ranking.', 'details': 'Every fact links to where it came from.'},
  'good': 'Made for you if', 'consider': 'Look elsewhere if',
  'source': 'Source', 'verified': 'Last checked', 'sources': 'Sources',
  'alt_on_site': 'See on ToolFavor', 'alt_visit': 'Learn more',
  'kind': {'official': 'Official', 'third_party': 'Third party', 'tested': 'Tested by ToolFavor'},
  'policy': 'Independent summary. Not sponsored, not certified, no invented ratings or prices. The official site always has the final word.',
  'founder': 'Disclosure: built by ToolFavor\'s founder, described under the same sourcing rules as every listing.',
  'founder_link': 'Creator portfolio', 'report': 'Something out of date? Tell us',
  'related_more': 'Browse the full directory',
  'pricing': {'free': 'Free', 'freemium': 'Free plan', 'paid': 'Paid'},
  'type': {'web': 'Web app', 'mobile': 'Mobile app', 'desktop': 'Desktop app', 'extension': 'Browser extension'},
  'cat': {'Design': 'Design', 'Productivity': 'Productivity'},
  'category': 'Category', 'type_label': 'Type', 'website': 'Website',
  'footer': 'ToolFavor · Discover, understand and compare useful tools.',
 },
 'ja': {
  'explore': 'ツールを探す', 'developers': '開発者の方へ',
  'visit': '{name}を入手', 'visit_web': '{name}を開く', 'fit_jump': '自分に合う？', 'more_tools': 'ほかのツールを探す',
  'titles': {'features': 'できること。', 'steps': '使い方。', 'fit': 'あなたに合う？', 'compare': 'ほかの方法と比べる。',
             'alternatives': 'ほかの選択肢も。', 'faq': 'よくある質問。', 'details': '詳しい情報と出典。', 'related': 'ほかのツールも。'},
  'subs': {'compare': '使い方と位置づけで比較。実機テストのランキングではありません。', 'details': 'すべての情報に出典があります。'},
  'good': 'こんな人に', 'consider': 'こんな場合はほかの方法を',
  'source': '出典', 'verified': '最終確認', 'sources': '出典',
  'alt_on_site': 'ToolFavorで見る', 'alt_visit': '詳しく見る',
  'kind': {'official': '公式', 'third_party': '第三者', 'tested': 'ToolFavor検証'},
  'policy': '独立した情報整理です。広告・提携・認証ではなく、架空の評価や価格は載せていません。最新情報は公式サイトが基準です。',
  'founder': '開示：ToolFavor創設者が制作したツールです。ほかの掲載と同じ出典ルールで紹介しています。',
  'founder_link': '制作者のポートフォリオ', 'report': '情報が古い場合はお知らせください',
  'related_more': 'ツール一覧を見る',
  'pricing': {'free': '無料', 'freemium': '無料プランあり', 'paid': '有料'},
  'type': {'web': 'Webアプリ', 'mobile': 'モバイルアプリ', 'desktop': 'デスクトップアプリ', 'extension': 'ブラウザー拡張'},
  'cat': {'Design': 'デザイン', 'Productivity': '仕事効率化'},
  'category': 'カテゴリ', 'type_label': '種類', 'website': '公式サイト',
  'footer': 'ToolFavor · 便利なツールを見つけて、比べて、選ぶ。',
 },
 'zh-cn': {
  'explore': '探索工具', 'developers': '开发者',
  'visit': '获取 {name}', 'visit_web': '打开 {name}', 'fit_jump': '适合我吗？', 'more_tools': '浏览更多工具',
  'titles': {'features': '它能做什么。', 'steps': '怎么用。', 'fit': '适合你吗？', 'compare': '和其他方式比一比。',
             'alternatives': '也可以试试这些。', 'faq': '常见问题。', 'details': '详细信息与来源。', 'related': '继续探索。'},
  'subs': {'compare': '按使用方式和定位比较，非实测排名。', 'details': '每条信息都能追溯到出处。'},
  'good': '适合你，如果', 'consider': '不妨换个方式，如果',
  'source': '来源', 'verified': '最后核对', 'sources': '来源',
  'alt_on_site': '在 ToolFavor 查看', 'alt_visit': '了解更多',
  'kind': {'official': '官方', 'third_party': '第三方', 'tested': 'ToolFavor 实测'},
  'policy': '独立资料整理。无赞助、无认证、无虚构评分或价格。一切以官方页面为准。',
  'founder': '利益披露：本工具由 ToolFavor 创始人开发，介绍时遵循与其他收录相同的来源规则。',
  'founder_link': '创作者作品集', 'report': '发现信息过时？告诉我们',
  'related_more': '浏览完整目录',
  'pricing': {'free': '免费', 'freemium': '有免费方案', 'paid': '付费'},
  'type': {'web': '网页应用', 'mobile': '手机应用', 'desktop': '桌面软件', 'extension': '浏览器扩展'},
  'cat': {'Design': '设计工具', 'Productivity': '效率工具'},
  'category': '分类', 'type_label': '类型', 'website': '官网',
  'footer': 'ToolFavor · 发现、了解并比较值得使用的工具。',
 },
}

TIER_RULES = {
    'basic': {'capabilities': 3, 'facts': 2, 'sources': 1},
    'complete': {'capabilities': 3, 'facts': 3, 'sources': 2, 'fit': 1, 'steps': 3, 'faq': 3, 'highlights': 3},
    'flagship': {'capabilities': 3, 'facts': 4, 'sources': 3, 'fit': 1, 'steps': 3, 'faq': 4, 'highlights': 3,
                 'compare': 3, 'alternatives': 3, 'media': 1},
}

# Simple line icons (24px, stroke = currentColor). Referenced by `icon` in capabilities.
ICONS = {
    'swipe': '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M12 15V8m-3 3 3-3 3 3"/>',
    'album': '<rect x="3" y="7" width="14" height="13" rx="2.5"/><path d="M7 4h11.5A2.5 2.5 0 0 1 21 6.5V16"/><path d="m6 17 3.5-4 3 3 1.5-1.5 2 2.5"/>',
    'compare': '<rect x="2.5" y="5" width="8" height="14" rx="2"/><rect x="13.5" y="5" width="8" height="14" rx="2"/><path d="m15.5 12 1.5 1.5 3-3"/>',
    'file': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/>',
    'layers': '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5"/><path d="m3 16 9 5 9-5"/>',
    'export': '<path d="M12 3v12m-4-4 4 4 4-4"/><path d="M4 15v3a3 3 0 0 0 3 3h10a3 3 0 0 0 3-3v-3"/>',
    'grid': '<rect x="3" y="3" width="18" height="18" rx="2.5"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
    'sliders': '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    'print': '<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',
    'swap': '<path d="M7 4 3 8l4 4"/><path d="M3 8h14"/><path d="m17 20 4-4-4-4"/><path d="M21 16H7"/>',
    'coins': '<circle cx="12" cy="12" r="9"/><path d="M14.5 9a2.5 2 0 0 0-2.5-1.5c-1.4 0-2.5.8-2.5 2s1.1 1.7 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2a2.5 2 0 0 1-2.5-1.5M12 6v1.5m0 9V18"/>',
    'repeat': '<path d="M17 2l4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/>',
    'check': '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    'ext': '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>',
    'star': '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
}


def icon(name, cls='ico'):
    body = ICONS.get(name)
    if not body:
        return f'<span class="{cls} glyph" aria-hidden="true">{escape(name)}</span>'
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def domain_of(url):
    return urlparse(url if '://' in url else 'https://' + url).netloc


# Images are self-hosted: scripts/fetch-logos.py (run by GitHub Actions) downloads every
# remote logo/media file into /assets and records it in data/assets.json. Until a file has
# been fetched, the page falls back to the remote URL so nothing is ever broken.
ASSET_MANIFEST_PATH = ROOT / 'data' / 'assets.json'
ASSETS = json.loads(ASSET_MANIFEST_PATH.read_text()) if ASSET_MANIFEST_PATH.exists() else {}
REQUESTED = {}  # key -> {"url": remote URL, "kind": "logo" | "favicon" | "media", "name": file name hint}


def asset(key, url, kind, name):
    """Return the local copy of a remote image if we have one, else the remote URL."""
    if url.startswith('/'):
        return url  # already a local file in the repo
    REQUESTED.setdefault(key, {'url': url, 'kind': kind, 'name': name})
    return ASSETS.get(key, {}).get('path') or url


def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'logo'


def logo(domain, name, cls='logo', src=None, eager=False):
    """Brand logo: explicit image if given, otherwise the site's icon; falls back to an initial."""
    if not src and domain.startswith('https://'):
        src = domain  # an explicit image URL was given instead of a domain
    if src:
        url = asset(src, src, 'logo', slugify(name))
    else:
        url = asset('favicon:' + domain, f'https://www.google.com/s2/favicons?domain={quote(domain)}&sz=256', 'favicon', slugify(domain))
    initial = escape((name.strip() or '?')[0].upper())
    return (f'<span class="{cls}" data-l="{initial}"><img src="{escape(url)}" alt="" loading="{'eager' if eager else 'lazy'}" decoding="async" '
            f'referrerpolicy="no-referrer" onerror="this.parentNode.classList.add(\'nl\');this.remove()"></span>')


def media_src(t, m):
    return asset(m['src'], m['src'], 'media', t['slug'])


def absolute(url):
    return SITE + url if url.startswith('/') else url


def tool_logo(t, cls='logo', eager=False):
    return logo(t.get('logo_domain') or t['domain'], t['name'], cls, t.get('logo'), eager)


def load_tools():
    tools = []
    for p in sorted(DATA.glob('*.json')):
        t = json.loads(p.read_text())
        assert t['slug'] == p.stem, f'{p.name}: slug must match file name'
        tools.append(t)
    return tools


def validate(t):
    errs = []
    rules = TIER_RULES.get(t.get('tier'))
    if not rules:
        return [f"{t['slug']}: unknown tier {t.get('tier')!r}"]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', t.get('last_verified', '')):
        errs.append('last_verified must be YYYY-MM-DD')
    if len(t.get('sources', {})) < rules['sources']:
        errs.append(f"needs {rules['sources']}+ sources")
    for s in t.get('sources', {}).values():
        if s.get('kind') not in ('official', 'third_party', 'tested'):
            errs.append(f"source kind invalid: {s}")
        if s.get('kind') == 'tested' and not s.get('tested_on'):
            errs.append('tested sources need tested_on')
    if len(t.get('media', [])) < rules.get('media', 0):
        errs.append('flagship needs product media')
    if len(t.get('alternatives', [])) < rules.get('alternatives', 0):
        errs.append(f"needs {rules['alternatives']}+ alternatives")
    for code in LOCALES:
        c = t['i18n'].get(code)
        if not c:
            errs.append(f'missing locale {code}')
            continue
        where = f'[{code}]'
        for key in ('title', 'description', 'lead', 'sublead', 'kicker', 'pricing_label', 'snapshot', 'cta', 'source_labels'):
            if not c.get(key):
                errs.append(f'{where} missing {key}')
        if len(c.get('title', '')) > 95:
            errs.append(f'{where} title is long ({len(c["title"])} chars)')
        if not 50 <= len(c.get('description', '')) <= 170:
            errs.append(f'{where} description length {len(c.get("description", ""))} (want 50–170)')
        for key in ('capabilities', 'facts', 'steps', 'faq', 'highlights'):
            if len(c.get(key, [])) < rules.get(key, 0):
                errs.append(f'{where} needs {rules[key]}+ {key}')
        if rules.get('fit') and not (c.get('fit', {}).get('good') and c.get('fit', {}).get('consider')):
            errs.append(f'{where} needs fit.good and fit.consider')
        if rules.get('compare') and len(c.get('compare', {}).get('rows', [])) < rules['compare']:
            errs.append(f'{where} needs {rules["compare"]}+ compare rows')
        for item in c.get('capabilities', []) + c.get('facts', []) + c.get('faq', []) + c.get('highlights', []):
            if item.get('source') not in t['sources']:
                errs.append(f'{where} unknown source {item.get("source")!r} in {item}')
        for k in t['sources']:
            if k not in c.get('source_labels', {}):
                errs.append(f'{where} source_labels missing {k}')
        for a in t.get('alternatives', []):
            if a['key'] not in c.get('alternatives', {}):
                errs.append(f'{where} alternative reason missing for {a["key"]}')
        if t.get('media') and not c.get('media_alt'):
            errs.append(f'{where} media_alt required')
    return [f"{t['slug']}: {e}" for e in errs]


def page_url(slug, code):
    # Public URL is extensionless: Cloudflare Pages redirects /x.html -> /x.
    return f"{LOCALES[code][0]}/tools/{slug}"


def page_file(slug, code):
    return f"{LOCALES[code][0]}/tools/{slug}.html".lstrip('/')


def home_url(code):
    return LOCALES[code][0] + '/'


def ext(url, text, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<a{c} href="{escape(url)}" target="_blank" rel="noopener">{text}</a>'


CSS = """
:root{--bg:#fbfbfd;--ink:#1d1d1f;--muted:#6e6e73;--soft:#86868b;--line:rgba(0,0,0,.08);--card:rgba(255,255,255,.72);--accent:#7958ed;--accent-ink:#5b3fd0;--lime:#b8f36b;--lilac:#d9ceff;--mint:#c9f2dc;--sky:#cfe2ff;--peach:#ffe0cc;--r:28px}
*{box-sizing:border-box}html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 -apple-system,BlinkMacSystemFont,"SF Pro Text","Inter","Helvetica Neue","Hiragino Sans","Hiragino Kaku Gothic ProN","PingFang SC","Microsoft YaHei",sans-serif;-webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:3px;border-radius:8px}
img{max-width:100%}h1,h2,h3,.lead,.sublead{text-wrap:balance;word-break:auto-phrase}
.wrap{max-width:1080px;margin:auto;padding:0 24px}
.ico{width:24px;height:24px;flex:none}
/* nav */
.top{position:sticky;top:0;z-index:20;background:rgba(251,251,253,.72);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:56px}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;font-size:18px;letter-spacing:-.02em}.brand img{width:24px;height:24px}.brand span{color:var(--accent)}
.navr{display:flex;align-items:center;gap:22px;font-size:13px;color:var(--muted)}.navr a{white-space:nowrap}.navr a:hover{color:var(--ink)}
.langs{display:flex;gap:2px;background:rgba(0,0,0,.04);border-radius:99px;padding:3px}.langs a{padding:3px 10px;border-radius:99px;font-size:12px}.langs [aria-current]{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 3px rgba(0,0,0,.08)}
/* ambient light */
.sky{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:-1}
.orb{position:absolute;border-radius:50%;filter:blur(70px);opacity:.75;animation:drift 18s ease-in-out infinite alternate}
.orb.a{width:520px;height:520px;background:var(--lilac);left:-120px;top:-80px}.orb.b{width:440px;height:440px;background:var(--mint);right:-100px;top:60px;animation-delay:-6s}.orb.c{width:380px;height:380px;background:var(--sky);left:35%;top:420px;animation-delay:-12s}.orb.d{width:300px;height:300px;background:var(--peach);right:12%;top:640px;opacity:.55;animation-delay:-3s}
@keyframes drift{0%{transform:translate(0,0) scale(1)}50%{transform:translate(40px,-30px) scale(1.08)}100%{transform:translate(-30px,25px) scale(.96)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
/* hero */
.hero{position:relative;isolation:isolate;padding:28px 0 40px}.hero-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:56px;align-items:center;min-height:min(720px,calc(100vh - 80px))}.intro{text-align:left}
.crumb{font-size:12px;color:var(--soft);margin-bottom:30px}.crumb a:hover{color:var(--ink)}.crumb i{font-style:normal;margin:0 6px;opacity:.6}
.appicon{width:104px;height:104px;margin:0 0 22px;border-radius:24px;box-shadow:0 22px 50px rgba(60,40,140,.18),0 2px 6px rgba(0,0,0,.06);animation:float 6s ease-in-out infinite}
.eyebrow{font-size:14px;font-weight:600;color:var(--accent-ink);letter-spacing:.01em;margin:0}
h1.long{font-size:clamp(40px,5.6vw,68px)!important}h1{font-size:clamp(48px,8vw,88px);line-height:1.02;letter-spacing:-.045em;font-weight:700;margin:6px 0 0}
.lead{font-size:clamp(24px,3.2vw,38px);line-height:1.15;letter-spacing:-.03em;font-weight:600;margin:14px 0 0;max-width:560px;background:linear-gradient(92deg,#1d1d1f 10%,#5b3fd0 55%,#3c9a5f 95%);-webkit-background-clip:text;background-clip:text;color:transparent}
.sublead{font-size:clamp(17px,1.7vw,20px);color:var(--muted);max-width:520px;margin:16px 0 0;line-height:1.5}
.cta-row{display:flex;justify-content:flex-start;align-items:center;gap:22px;flex-wrap:wrap;margin-top:30px}
.pill{display:inline-flex;align-items:center;gap:6px;background:var(--accent);color:#fff;border-radius:99px;padding:13px 26px;font-size:17px;font-weight:500;transition:transform .25s,box-shadow .25s,background .25s}
.pill:hover{background:#6a45ea;transform:translateY(-2px);box-shadow:0 14px 30px rgba(121,88,237,.32)}
.link{display:inline-flex;align-items:center;gap:4px;color:var(--accent-ink);font-size:17px}.link:hover{text-decoration:underline}.link .ico{width:16px;height:16px}
.meta{display:flex;justify-content:flex-start;flex-wrap:wrap;gap:8px;margin-top:26px}
.badge{display:inline-flex;align-items:center;gap:7px;background:var(--card);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:99px;padding:6px 13px 6px 7px;font-size:13px;color:#424245}
.badge.price{padding-left:13px;background:#effbe6;border-color:#d8f2c4;color:#2f6b1c;font-weight:600}
.logo{position:relative;display:inline-grid;place-items:center;flex:none;width:22px;height:22px;border-radius:6px;overflow:hidden;background:#fff}
.logo img{width:100%;height:100%;object-fit:contain;display:block}
.logo.nl,.appicon.logo.nl{background:linear-gradient(140deg,#8b6cf3,#5b3fd0)}.logo.nl:after{content:attr(data-l);color:#fff;font-weight:700;font-size:.55em;line-height:1}
.appicon.logo{width:104px;height:104px;border-radius:24px;font-size:96px;background:#fff}.appicon.logo img{width:100%;height:100%}
.snap{font-size:12px;color:var(--soft);margin-top:18px}
/* hero stage */
.stage{position:relative;display:flex;justify-content:center;align-items:center}.phone-wrap{position:relative}.paper{position:relative;width:min(400px,100%);border-radius:14px;background:#fff;padding:14px;box-shadow:0 50px 100px -30px rgba(50,30,120,.35),0 0 0 1px var(--line);transform:rotate(2deg);animation:float 8s ease-in-out infinite}.paper img{display:block;width:100%;border-radius:6px}.paper .fallback{display:none;place-items:center;aspect-ratio:3/4}.paper.failed img{display:none}.paper.failed .fallback{display:grid}.paper .fallback .logo{width:96px;height:96px;border-radius:22px;font-size:80px}
.phone{position:relative;width:min(300px,74vw);aspect-ratio:9/19.3;border-radius:46px;background:#111;padding:11px;box-shadow:0 50px 100px -20px rgba(50,30,120,.35),0 0 0 1px rgba(0,0,0,.2),inset 0 0 0 2px #2b2b2b;animation:float 7s ease-in-out infinite}
.phone:before{content:"";position:absolute;top:20px;left:50%;transform:translateX(-50%);width:84px;height:24px;border-radius:20px;background:#000;z-index:2}
.screen{position:relative;width:100%;height:100%;border-radius:36px;overflow:hidden;background:linear-gradient(160deg,#f3eeff,#e7f6ee)}
.screen img{width:100%;height:100%;object-fit:contain;display:block;background:#000}
.screen .fallback{position:absolute;inset:0;display:none;place-items:center}.screen.failed .fallback{display:grid}.screen.failed img{display:none}
.screen .fallback .logo{width:96px;height:96px;border-radius:22px;font-size:80px;box-shadow:0 16px 40px rgba(60,40,140,.2)}
.browser{width:min(920px,100%);border-radius:18px;background:rgba(255,255,255,.8);border:1px solid var(--line);box-shadow:0 50px 100px -30px rgba(50,30,120,.3);overflow:hidden;animation:float 8s ease-in-out infinite}
.browser .bar{display:flex;align-items:center;gap:7px;padding:12px 14px;border-bottom:1px solid var(--line)}.browser .bar i{width:11px;height:11px;border-radius:50%;background:#e2e2e7}.browser .bar i:nth-child(1){background:#ff5f57}.browser .bar i:nth-child(2){background:#febc2e}.browser .bar i:nth-child(3){background:#28c840}
.browser .addr{margin:0 auto;font-size:12px;color:var(--muted);background:rgba(0,0,0,.04);border-radius:8px;padding:4px 40px}
.browser .view img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;object-position:top left}
.browser .view .mock{display:none}.browser.failed .view img{display:none}.browser.failed .view .mock{display:grid}
.mock{grid-template-columns:44px 1fr 150px;aspect-ratio:16/10;background:#2c2c35;color:#bdbdc7;font-size:11px;text-align:left}
.mock .tl{background:#23232b;display:grid;align-content:start;gap:16px;padding:16px 0;justify-items:center}.mock .tl b{width:16px;height:16px;border-radius:4px;background:#45454f}
.mock .cv{display:grid;place-items:center;background:repeating-conic-gradient(#3a3a44 0 25%,#33333c 0 50%) 50%/24px 24px}.mock .cv div{width:70%;aspect-ratio:1.3;border-radius:6px;background:linear-gradient(135deg,var(--lilac),var(--sky) 55%,var(--mint));box-shadow:0 20px 40px rgba(0,0,0,.35)}
.mock .ly{background:#23232b;padding:12px}.mock .ly p{margin:0 0 8px;padding:8px;border-radius:6px;background:#2e2e37}.mock .ly p:first-child{background:#4b4370;color:#fff}
.chipfloat{position:absolute;display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.82);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.9);box-shadow:0 18px 40px rgba(40,30,90,.14);border-radius:18px;padding:11px 16px;font-size:15px;font-weight:600;white-space:nowrap;animation:float 6s ease-in-out infinite}
.chipfloat .ico{width:20px;height:20px;color:var(--accent)}
.chipfloat{z-index:3}.chipfloat.c0{right:calc(100% - 40px);top:18%}.chipfloat.c1{left:calc(100% - 70px);top:44%;animation-delay:-2s}.chipfloat.c2{right:calc(100% - 50px);top:72%;animation-delay:-4s}
.glass-card{background:var(--card);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,.9);box-shadow:0 30px 70px -30px rgba(50,30,120,.25);border-radius:var(--r)}
.stage .glass-card{padding:30px 34px;min-width:min(420px,100%);text-align:left;animation:float 8s ease-in-out infinite}
.stage dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:12px 26px;font-size:15px}.stage dt{color:var(--muted)}.stage dd{margin:0;font-weight:600}
/* sections */
section.block{padding:96px 0 0}
.head{text-align:center;max-width:760px;margin:0 auto 44px}
h2{font-size:clamp(34px,5vw,56px);line-height:1.06;letter-spacing:-.035em;font-weight:700;margin:0}
.head p{color:var(--muted);font-size:19px;margin:12px 0 0}
/* highlights */
.hl{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-top:56px}
.hl .tile{padding:24px 22px;text-align:left;display:flex;flex-direction:column;gap:6px;min-height:150px;transition:transform .3s}
.hl .tile:hover{transform:translateY(-4px)}
.hl .logos{display:flex;gap:6px;min-height:26px}.hl .logos .logo{width:26px;height:26px;border-radius:7px;font-size:24px;box-shadow:0 2px 6px rgba(0,0,0,.08)}
.hl .v{font-size:30px;font-weight:700;letter-spacing:-.03em;line-height:1.1;margin-top:auto}.hl .v.long{font-size:22px}
.hl .l{font-size:13px;color:var(--muted);line-height:1.4}
/* features */
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.feature{padding:34px 30px;position:relative;overflow:hidden}
.feature .badge-ico{display:grid;place-items:center;width:56px;height:56px;border-radius:18px;color:var(--accent-ink);background:linear-gradient(140deg,#efe9ff,#e3f6ea);margin-bottom:26px}
.feature .badge-ico .ico{width:28px;height:28px}
.feature h3{font-size:24px;letter-spacing:-.02em;line-height:1.2;margin:0 0 10px}
.feature p{margin:0;color:var(--muted);font-size:16px}
.src{display:inline-flex;align-items:center;gap:4px;margin-top:16px;font-size:13px;color:var(--soft)}.src:hover{color:var(--accent-ink)}.src .ico{width:13px;height:13px}
/* steps */
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;counter-reset:s;position:relative}
.step{padding:30px}
.step .n{font-size:64px;font-weight:700;letter-spacing:-.05em;line-height:1;background:linear-gradient(140deg,var(--accent),#57c77f);-webkit-background-clip:text;background-clip:text;color:transparent}
.step h3{font-size:21px;margin:18px 0 8px;letter-spacing:-.02em}.step p{margin:0;color:var(--muted);font-size:15px}
/* fit */
.fit{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.fit .glass-card{padding:34px}
.fit h3{font-size:22px;margin:0 0 18px;letter-spacing:-.02em}
.fit ul{list-style:none;margin:0;padding:0;display:grid;gap:14px}
.fit li{display:flex;gap:12px;font-size:16px;line-height:1.45}
.fit li .ico{width:22px;height:22px;padding:3px;border-radius:50%;color:#2f8a4b;background:#e3f6ea}
.fit .no li .ico{color:#b36a14;background:#fff1e0}
/* compare */
.table{overflow-x:auto;padding:6px}
.table table{width:100%;border-collapse:collapse;font-size:15px;min-width:720px}
.table th,.table td{text-align:left;padding:18px 16px;border-bottom:1px solid var(--line);vertical-align:middle}
.table thead th{font-size:12px;font-weight:600;color:var(--soft);text-transform:uppercase;letter-spacing:.04em}
.table tbody tr:last-child th,.table tbody tr:last-child td{border-bottom:0}
.table .name{display:flex;align-items:center;gap:12px;font-weight:600;white-space:nowrap}
.table .name .logo{width:34px;height:34px;border-radius:9px;font-size:30px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.table .self{background:linear-gradient(90deg,rgba(121,88,237,.07),rgba(121,88,237,0))}
.table td{color:#424245}
.note{text-align:center;font-size:13px;color:var(--soft);margin-top:16px}
/* alternatives & related */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}
.alt{padding:28px;display:flex;flex-direction:column;transition:transform .3s,box-shadow .3s}
.alt:hover{transform:translateY(-4px);box-shadow:0 40px 80px -30px rgba(50,30,120,.3)}
.alt .top-row{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:18px}
.alt .logo{width:52px;height:52px;border-radius:14px;font-size:44px;box-shadow:0 6px 16px rgba(0,0,0,.08)}
.tag{font-size:12px;font-weight:600;color:var(--accent-ink);background:#f1edff;border-radius:99px;padding:4px 10px;white-space:nowrap}
.alt h3{font-size:19px;margin:0 0 8px;letter-spacing:-.015em}
.alt p{margin:0;color:var(--muted);font-size:15px;flex:1}
.alt .go{margin-top:18px;font-size:15px;color:var(--accent-ink);display:inline-flex;align-items:center;gap:4px}.alt .go .ico{width:15px;height:15px}
/* faq */
.faq{max-width:820px;margin:0 auto}
.faq details{border-bottom:1px solid var(--line)}
.faq summary{list-style:none;cursor:pointer;padding:24px 0;font-size:19px;font-weight:600;display:flex;justify-content:space-between;gap:20px;letter-spacing:-.01em}
.faq summary::-webkit-details-marker{display:none}
.faq summary:after{content:"";flex:none;width:12px;height:12px;margin-top:8px;border-right:2px solid var(--soft);border-bottom:2px solid var(--soft);transform:rotate(45deg);transition:transform .3s}
.faq details[open] summary:after{transform:rotate(225deg)}
.faq .a{padding:0 0 24px;color:var(--muted);font-size:16px}.faq .a p{margin:0}
/* fine print */
.fine{display:grid;grid-template-columns:1.2fr 1fr;gap:18px}
.fine .glass-card{padding:30px}
.specs{margin:0;display:grid;gap:0}
.specs div{display:grid;grid-template-columns:130px 1fr;gap:14px;padding:12px 0;border-bottom:1px solid var(--line);font-size:14px}
.specs div:last-child{border-bottom:0}.specs dt{color:var(--soft)}.specs dd{margin:0}
.specs dd a{color:var(--accent-ink)}
.srcs{display:grid;gap:10px}
.srcs a{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:14px;font-size:14px;transition:background .2s}
.srcs a:hover{background:rgba(121,88,237,.06)}
.srcs .logo{width:28px;height:28px;border-radius:8px;font-size:24px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
.srcs .t{flex:1;min-width:0}.srcs .k{font-size:11px;color:var(--soft)}
.fine h3{font-size:15px;color:var(--soft);font-weight:600;margin:0 0 10px;text-transform:uppercase;letter-spacing:.05em}
.policy{font-size:13px;color:var(--soft);margin-top:22px;line-height:1.6}.policy p{margin:4px 0}.policy a{color:var(--accent-ink)}
/* related */
.rel{padding:24px;display:flex;align-items:center;gap:16px;transition:transform .3s}
.rel:hover{transform:translateY(-3px)}
.rel .logo{width:48px;height:48px;border-radius:13px;font-size:40px;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.rel h3{margin:0;font-size:17px}.rel p{margin:2px 0 0;font-size:14px;color:var(--muted)}
.more{text-align:center;margin-top:22px}
/* closing */
.closing{position:relative;isolation:isolate;overflow:hidden;text-align:center;margin:110px 0 0;padding:90px 24px;border-radius:40px;background:linear-gradient(135deg,#f1ecff,#e9f8ef 55%,#e8f1ff)}
.closing .logo{width:72px;height:72px;border-radius:18px;font-size:64px;margin:0 auto 22px;box-shadow:0 16px 40px rgba(60,40,140,.18);animation:float 6s ease-in-out infinite}
.closing h2{font-size:clamp(32px,5vw,52px)}.closing p{color:var(--muted);font-size:19px;margin:12px 0 28px}
footer{margin-top:80px;padding:28px 0 40px;border-top:1px solid var(--line);font-size:12px;color:var(--soft)}
footer .wrap{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px}footer a:hover{color:var(--ink)}
/* motion */
.js .reveal{opacity:0;transform:translateY(28px);transition:opacity .9s cubic-bezier(.2,.7,.2,1),transform .9s cubic-bezier(.2,.7,.2,1)}
.js .reveal.in{opacity:1;transform:none}
@media(max-width:1100px){.chipfloat.c0,.chipfloat.c2{right:calc(100% - 70px)}.chipfloat.c1{left:calc(100% - 70px)}}@media(max-width:900px){.hero-grid{grid-template-columns:1fr;gap:44px;min-height:0}.intro{text-align:center}.appicon{margin:0 auto 22px}.lead,.sublead{margin-left:auto;margin-right:auto}.cta-row,.meta{justify-content:center}.chipfloat{display:none}.features,.steps{grid-template-columns:1fr}.fit,.fine{grid-template-columns:1fr}section.block{padding-top:76px}}
@media(max-width:620px){body{font-size:16px}.wrap{padding:0 16px}.navr .dev{display:none}.navr{gap:10px}.brand{font-size:16px}.appicon,.appicon.logo{width:84px;height:84px;border-radius:20px}.hero{padding-top:20px}.crumb{margin-bottom:24px}.cta-row{gap:16px}.pill{padding:12px 22px;font-size:16px}.hl{grid-template-columns:1fr 1fr;margin-top:50px}.hl .tile{min-height:130px;padding:20px 18px}.hl .v{font-size:24px}.hl .v.long{font-size:18px}.feature,.step,.fit .glass-card,.fine .glass-card,.alt{padding:24px}.head{margin-bottom:30px}.head p{font-size:17px}.faq summary{font-size:17px}.specs div{grid-template-columns:1fr;gap:2px}.closing{padding:60px 20px;border-radius:28px;margin-top:80px}.orb.a{width:340px;height:340px}.phone{width:62vw}.orb.b{width:300px;height:300px}.orb.c,.orb.d{display:none}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}.js .reveal{opacity:1;transform:none}html{scroll-behavior:auto}}
"""

REVEAL_JS = ("(function(){var els=document.querySelectorAll('.reveal');if(!('IntersectionObserver' in window)){els.forEach(function(e){e.classList.add('in')});return}"
             "var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px'});"
             "els.forEach(function(e){io.observe(e)})})();")


def onfail(cls='failed'):
    return f'onerror="this.closest(\'.js-media\').classList.add(\'{cls}\')"'


def render_stage(t, c, u):
    media = (t.get('media') or [None])[0]
    if media and media.get('portrait'):
        img = (f'<img src="{escape(media_src(t, media))}" alt="{escape(c["media_alt"])}" decoding="async" fetchpriority="high" '
               f'referrerpolicy="no-referrer" {onfail()}>')
        chips = ''.join(f'<span class="chipfloat c{i}">{icon(ch.get("icon", "check"))}{escape(ch["text"])}</span>'
                        for i, ch in enumerate(c.get('hero_chips', [])[:3]))
        return (f'<div class="stage reveal"><div class="phone-wrap">{chips}<div class="phone"><div class="screen js-media">{img}'
                f'<div class="fallback">{tool_logo(t, eager=True)}</div></div></div></div></div>')
    if media and media.get('frame') == 'paper':
        img = (f'<img src="{escape(media_src(t, media))}" alt="{escape(c["media_alt"])}" decoding="async" fetchpriority="high" '
               f'referrerpolicy="no-referrer" {onfail()}>')
        return (f'<div class="stage reveal"><div class="paper js-media">{img}'
                f'<div class="fallback">{tool_logo(t, eager=True)}</div></div></div>')
    if media:
        img = (f'<img src="{escape(media_src(t, media))}" alt="{escape(c["media_alt"])}" decoding="async" fetchpriority="high" '
               f'referrerpolicy="no-referrer" {onfail()}>')
        mock = ('<div class="mock" aria-hidden="true"><div class="tl"><b></b><b></b><b></b><b></b><b></b></div>'
                '<div class="cv"><div></div></div><div class="ly"><p>▣ Layer 3</p><p>▣ Layer 2</p><p>▧ Background</p></div></div>')
        return (f'<div class="stage reveal"><div class="browser js-media"><div class="bar"><i></i><i></i><i></i>'
                f'<span class="addr">{escape(t["domain"])}</span></div><div class="view">{img}{mock}</div></div></div>')
    rows = [(u['category'], u['cat'].get(t['category'], t['category'])), (u['type_label'], u['type'][t['type']])]
    rows += [(f['label'], f['value']) for f in c.get('facts', [])[:2]]
    dl = ''.join(f'<dt>{escape(k)}</dt><dd>{escape(v)}</dd>' for k, v in rows)
    return f'<div class="stage reveal"><div class="glass-card"><dl>{dl}</dl></div></div>'


def head_block(title, sub=''):
    s = f'<p>{escape(sub)}</p>' if sub else ''
    return f'<div class="head reveal"><h2>{escape(title)}</h2>{s}</div>'


def block(id_, title, inner, sub=''):
    return f'<section class="block" id="{id_}"><div class="wrap">{head_block(title, sub)}{inner}</div></section>'


def src_link(url, u):
    return ext(url, f'{escape(u["source"])} {icon("ext")}', 'src')


def json_ld(t, c, code):
    url = SITE + page_url(t['slug'], code)
    app = {'@type': 'SoftwareApplication', 'name': t['name'], 'url': t['url'],
           'description': c['description'], 'applicationCategory': t['schema']['applicationCategory'],
           'operatingSystem': t['schema']['operatingSystem']}
    if t['pricing'] in ('free', 'freemium'):
        app['offers'] = {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}
    if t.get('media') and not t['media'][0].get('portrait'):
        app['screenshot'] = absolute(media_src(t, t['media'][0]))
    graph = [
        {'@type': 'WebPage', '@id': url, 'url': url, 'name': c['title'], 'inLanguage': LOCALES[code][1],
         'dateModified': t['last_verified'], 'about': {'@id': url + '#app'},
         'isPartOf': {'@type': 'WebSite', 'name': 'ToolFavor', 'url': SITE + '/'}},
        dict(app, **{'@id': url + '#app'}),
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': UI[code]['explore'], 'item': SITE + home_url(code)},
            {'@type': 'ListItem', 'position': 2, 'name': t['name'], 'item': url}]},
    ]
    if c.get('faq'):
        graph.append({'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in c['faq']]})
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def render(t, code, tools_by_slug):
    c, u = t['i18n'][code], UI[code]
    prefix, lang, _, og_locale = LOCALES[code]
    slug, name, src = t['slug'], t['name'], t['sources']
    titles = dict(u['titles'], **c.get('titles', {}))
    canonical = SITE + page_url(slug, code)
    visit_label = (u['visit_web'] if t['type'] == 'web' else u['visit']).format(name=name)

    alternates = ''.join(f'<link rel="alternate" hreflang="{LOCALES[k][2]}" href="{SITE + page_url(slug, k)}">' for k in LOCALES)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE + page_url(slug, "en")}">'
    og_image = ''
    if t.get('media'):
        og_image = f'<meta property="og:image" content="{escape(absolute(media_src(t, t["media"][0])))}"><meta name="twitter:card" content="summary_large_image">'
    head = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="theme-color" content="#fbfbfd"><title>{escape(c["title"])}</title>'
            f'<meta name="description" content="{escape(c["description"])}"><link rel="canonical" href="{canonical}">{alternates}'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="ToolFavor"><meta property="og:locale" content="{og_locale}">'
            f'<meta property="og:title" content="{escape(c["title"])}"><meta property="og:description" content="{escape(c["description"])}">'
            f'<meta property="og:url" content="{canonical}">{og_image}'
            f'<link rel="icon" href="/favicon-96x96.png" sizes="96x96"><link rel="icon" href="/assets/toolfavor-mark.svg" type="image/svg+xml">'
            f'<script>document.documentElement.classList.add("js")</script>'
            f'<style>{CSS.strip()}</style><script type="application/ld+json">{json_ld(t, c, code)}</script></head>')

    langs = ''.join(f'<a href="{page_url(slug, k)}" lang="{LOCALES[k][1]}" hreflang="{LOCALES[k][2]}"'
                    + (' aria-current="page"' if k == code else '') + f'>{LANG_LABEL[k]}</a>' for k in LOCALES)
    nav = (f'<header class="top"><div class="wrap"><a class="brand" href="{home_url(code)}"><img src="/assets/toolfavor-mark.svg" alt="" width="24" height="24">ToolFavor<span>.</span></a>'
           f'<nav class="navr" aria-label="Main"><a href="{home_url(code)}">{escape(u["explore"])}</a><a class="dev" href="{prefix}/developers">{escape(u["developers"])}</a>'
           f'<span class="langs" role="group" aria-label="Language">{langs}</span></nav></div></header>')

    cat = u['cat'].get(t['category'], t['category'])
    crumb = (f'<nav class="crumb" aria-label="Breadcrumb"><a href="{home_url(code)}">{escape(u["explore"])}</a><i>/</i>'
             f'{escape(cat)}<i>/</i><span aria-current="page">{escape(name)}</span></nav>')
    badges = ''.join(f'<span class="badge">{logo(p["domain"], p["label"])}{escape(p["label"])}</span>' for p in t.get('platforms', []))
    badges += f'<span class="badge price">{escape(c["pricing_label"])}</span>'
    second = (f'<a class="link" href="#fit">{escape(u["fit_jump"])} {icon("arrow")}</a>' if c.get('fit')
              else f'<a class="link" href="{home_url(code)}">{escape(u["more_tools"])} {icon("arrow")}</a>')
    hero = (f'<section class="hero"><div class="sky" aria-hidden="true"><i class="orb a"></i><i class="orb b"></i><i class="orb c"></i><i class="orb d"></i></div>'
            f'<div class="wrap"><div class="hero-grid"><div class="intro">{crumb}{tool_logo(t, "appicon logo", eager=True)}'
            f'<p class="eyebrow">{escape(c["kicker"])}</p><h1{" class=long" if len(name) > 10 else ""}>{escape(name)}</h1>'
            f'<p class="lead">{escape(c["lead"])}</p><p class="sublead">{escape(c["sublead"])}</p>'
            f'<div class="cta-row">{ext(t["url"], escape(visit_label) + " " + icon("ext"), "pill")}{second}</div>'
            f'<div class="meta">{badges}</div>'
            f'<p class="snap">{escape(c["snapshot"])} · {escape(u["verified"])} {t["last_verified"]}</p></div>'
            f'{render_stage(t, c, u)}</div>')
    if c.get('highlights'):
        tiles = ''
        for h in c['highlights']:
            logos = ''.join(logo(d, d) for d in h.get('domains', []))
            if not logos and h.get('icon'):
                logos = f'<span style="color:var(--accent-ink)">{icon(h["icon"])}</span>'
            tiles += (f'<a class="tile glass-card" href="{escape(src[h["source"]]["url"])}" target="_blank" rel="noopener">'
                      f'<span class="logos">{logos}</span><span class="v{" long" if sum(2 if ord(ch) > 0x2e80 else 1 for ch in h["value"]) > 7 else ""}">{escape(h["value"])}</span><span class="l">{escape(h["label"])}</span></a>')
        hero += f'<div class="hl reveal">{tiles}</div>'
    hero += '</div></section>'

    body = []
    cards = ''.join(f'<article class="feature glass-card reveal"><div class="badge-ico">{icon(x["icon"])}</div>'
                    f'<h3>{escape(x["title"])}</h3><p>{escape(x["text"])}</p>{src_link(src[x["source"]]["url"], u)}</article>'
                    for x in c['capabilities'])
    body.append(block('features', titles['features'], f'<div class="features">{cards}</div>', c.get('features_sub', '')))

    if c.get('steps'):
        steps = ''.join(f'<article class="step glass-card reveal"><div class="n">{i:02d}</div><h3>{escape(s["title"])}</h3><p>{escape(s["text"])}</p></article>'
                        for i, s in enumerate(c['steps'], 1))
        body.append(block('start', c.get('steps_title') or titles['steps'], f'<div class="steps">{steps}</div>'))

    if c.get('fit'):
        good = ''.join(f'<li>{icon("check")}<span>{escape(x)}</span></li>' for x in c['fit']['good'])
        maybe = ''.join(f'<li>{icon("arrow")}<span>{escape(x)}</span></li>' for x in c['fit']['consider'])
        body.append(block('fit', titles['fit'].format(name=name),
                          f'<div class="fit"><div class="glass-card reveal"><h3>{escape(u["good"])}</h3><ul>{good}</ul></div>'
                          f'<div class="glass-card no reveal"><h3>{escape(u["consider"])}</h3><ul>{maybe}</ul></div></div>'))

    if c.get('compare'):
        cmp, links = c['compare'], t.get('compare_links', {})
        thead = ''.join(f'<th scope="col">{escape(h)}</th>' for h in cmp['columns'])
        trs = ''
        for r in cmp['rows']:
            is_self = r[0] == name
            mark = tool_logo(t) if is_self else logo(t.get('compare_logos', {}).get(r[0]) or domain_of(links.get(r[0], '')) or r[0], r[0])
            label = escape(r[0]) if is_self or r[0] not in links else ext(links[r[0]], escape(r[0]))
            trs += (f'<tr{" class=self" if is_self else ""}><th scope="row"><span class="name">{mark}{label}</span></th>'
                    + ''.join(f'<td>{escape(x)}</td>' for x in r[1:]) + '</tr>')
        inner = (f'<div class="table glass-card reveal"><table><thead><tr>{thead}</tr></thead><tbody>{trs}</tbody></table></div>'
                 f'<p class="note">{escape(cmp["note"])}</p>')
        body.append(block('compare', titles['compare'], inner, u['subs']['compare']))

    if t.get('alternatives'):
        cards = ''
        for a in t['alternatives']:
            on_site = a['key'] in tools_by_slug
            if on_site:
                go = f'<a class="go" href="{page_url(a["key"], code)}">{escape(u["alt_on_site"])} {icon("arrow")}</a>'
            else:
                go = ext(a['url'], f'{escape(u["alt_visit"])} {icon("ext")}', 'go')
            mark = logo(a.get('domain') or domain_of(a['url']), a['name'], src=a.get('logo'))
            cards += (f'<article class="alt glass-card reveal"><div class="top-row">{mark}<span class="tag">{escape(u["pricing"][a["pricing"]])}</span></div>'
                      f'<h3>{escape(a["name"])}</h3><p>{escape(c["alternatives"][a["key"]])}</p>{go}</article>')
        body.append(block('alternatives', titles['alternatives'], f'<div class="cards">{cards}</div>'))

    if c.get('faq'):
        items = ''.join(f'<details{" open" if i == 0 else ""}><summary>{escape(f["q"])}</summary>'
                        f'<div class="a"><p>{escape(f["a"])}</p>{src_link(src[f["source"]]["url"], u)}</div></details>'
                        for i, f in enumerate(c['faq']))
        body.append(block('faq', titles['faq'], f'<div class="faq reveal">{items}</div>'))

    facts = [(u['category'], escape(cat)), (u['type_label'], escape(u['type'][t['type']]))]
    facts += [(f['label'], escape(f['value']) + ' ' + ext(src[f['source']]['url'], icon('ext'), 'src')) for f in c['facts']]
    facts += [(u['website'], ext(t['url'], escape(t['domain']))), (u['verified'], t['last_verified'])]
    specs = ''.join(f'<div><dt>{escape(k)}</dt><dd>{v}</dd></div>' for k, v in facts)
    srcs = ''.join(f'<a href="{escape(s["url"])}" target="_blank" rel="noopener">{logo(domain_of(s["url"]), c["source_labels"][k])}'
                   f'<span class="t">{escape(c["source_labels"][k])}<br><span class="k">{escape(u["kind"][s["kind"]])} · {escape(domain_of(s["url"]))}</span></span></a>'
                   for k, s in src.items())
    policy = f'<p>{escape(u["policy"])}</p>'
    if t.get('related_by_founder'):
        policy += f'<p>{escape(u["founder"])} <a href="{prefix}/creators/1/">{escape(u["founder_link"])} →</a></p>'
    policy += f'<p><a href="{prefix}/contact">{escape(u["report"])} →</a></p>'
    fine = (f'<div class="fine"><div class="glass-card reveal"><dl class="specs">{specs}</dl></div>'
            f'<div class="glass-card reveal"><h3>{escape(u["sources"])}</h3><div class="srcs">{srcs}</div><div class="policy">{policy}</div></div></div>')
    body.append(block('details', titles['details'], fine, u['subs']['details']))

    skip = {a['key'] for a in t.get('alternatives', [])} | {slug}
    others = sorted((o for o in tools_by_slug.values() if o['slug'] not in skip), key=lambda o: (o['category'] != t['category'], o['name']))
    if others:
        cards = ''.join(f'<a class="rel glass-card reveal" href="{page_url(o["slug"], code)}">{tool_logo(o)}'
                        f'<span><h3>{escape(o["name"])}</h3><p>{escape(o["i18n"][code]["lead"])}</p></span></a>' for o in others[:3])
        body.append(block('related', titles['related'],
                          f'<div class="cards">{cards}</div><p class="more"><a class="link" href="{home_url(code)}">{escape(u["related_more"])} {icon("arrow")}</a></p>'))

    cta = c['cta']
    closing = (f'<div class="wrap"><section class="closing reveal"><div class="sky" aria-hidden="true"><i class="orb a"></i><i class="orb b"></i></div>'
               f'{tool_logo(t)}<h2>{escape(cta["title"])}</h2><p>{escape(cta["text"])}</p>'
               f'{ext(t["url"], escape(visit_label) + " " + icon("ext"), "pill")}</section></div>')
    footer = (f'<footer><div class="wrap"><span>© {escape(u["footer"])}</span>'
              f'<a href="{home_url(code)}">{escape(u["more_tools"])} →</a></div></footer>')
    return (head + '<body>' + nav + '<main>' + hero + ''.join(body) + closing + '</main>' + footer
            + f'<script>{REVEAL_JS}</script></body></html>\n')


def update_sitemap(tools):
    path = ROOT / 'sitemap.xml'
    xml = path.read_text()
    entries = re.findall(r'<url>(.*?)</url>', xml, flags=re.S)
    urls = []
    for e in entries:
        loc = re.search(r'<loc>(.*?)</loc>', e).group(1).strip()
        lastmod = re.search(r'<lastmod>(.*?)</lastmod>', e)
        urls.append([loc, lastmod.group(1) if lastmod else None])
    known = {u[0]: u for u in urls}
    for t in tools:
        for code in LOCALES:
            loc = SITE + page_url(t['slug'], code)
            if loc in known:
                known[loc][1] = t['last_verified']
            else:
                item = [loc, t['last_verified']]
                urls.append(item)
                known[loc] = item
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in urls:
        lines.append(f'<url><loc>{loc}</loc>' + (f'<lastmod>{lastmod}</lastmod>' if lastmod else '') + '</url>')
    lines.append('</urlset>')
    path.write_text('\n'.join(lines) + '\n')


def main():
    tools = load_tools()
    errors = [e for t in tools for e in validate(t)]
    if errors:
        print('Validation failed:\n  ' + '\n  '.join(errors))
        sys.exit(1)
    if '--check' in sys.argv:
        print(f'OK: {len(tools)} tools pass their tier rules.')
        return
    by_slug = {t['slug']: t for t in tools}
    for t in tools:
        for code in LOCALES:
            dest = ROOT / page_file(t['slug'], code)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(t, code, by_slug))
    update_sitemap(tools)
    print(f'Generated {len(tools) * len(LOCALES)} detail pages for {len(tools)} tools.')


if __name__ == '__main__':
    main()
