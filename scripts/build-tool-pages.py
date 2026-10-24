"""Generate tool detail pages from data/tools/*.json for every locale.

    python3 scripts/build-tool-pages.py           # validate, then write pages + sitemap
    python3 scripts/build-tool-pages.py --check   # validate only

See docs/detail-page-standard.md for the content standard and tiers.
"""
from pathlib import Path
from html import escape
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'tools'
SITE = 'https://toolfavor.com'
LOCALES = {  # key: (folder prefix, html lang, hreflang, og locale)
    'en': ('', 'en', 'en', 'en_US'),
    'ja': ('/ja', 'ja', 'ja', 'ja_JP'),
    'zh-cn': ('/zh-cn', 'zh-CN', 'zh-CN', 'zh_CN'),
}
LANG_LABEL = {'en': 'English', 'ja': '日本語', 'zh-cn': '简体中文'}

UI = {
 'en': {
  'explore': 'Explore tools', 'developers': 'For developers', 'home': 'ToolFavor',
  'visit': 'Visit {name} ↗', 'fit_jump': 'Is it right for me? ↓', 'more_tools': 'Browse more tools',
  'cap_eyebrow': 'AT A GLANCE', 'cap_title': 'What can it do for you?', 'cap_note': 'Each point links to the official source',
  'check': 'Check source ↗',
  'facts_eyebrow': 'KEY FACTS', 'facts_title': 'The details that matter', 'verified': 'Last checked',
  'fit_eyebrow': 'MAKE A DECISION', 'fit_title': 'Is {name} right for you?', 'good': 'Good fit if…', 'consider': 'Compare first if…',
  'steps_eyebrow': 'START IN MINUTES', 'steps_title': 'Your first edit in three steps',
  'compare_eyebrow': 'CHOOSE THE RIGHT TOOL', 'compare_title': 'How does it compare?', 'compare_sub': 'By positioning and typical use — not a hands-on ranking',
  'alt_eyebrow': 'ALTERNATIVES', 'alt_title': 'When another tool fits better', 'alt_on_site': 'Details on ToolFavor →', 'alt_visit': 'Visit site ↗',
  'faq_eyebrow': 'QUICK ANSWERS', 'faq_title': 'Frequently asked questions',
  'src_eyebrow': 'TRANSPARENCY', 'src_title': 'Where this information comes from',
  'kind': {'official': 'Official', 'third_party': 'Third party', 'tested': 'Tested by ToolFavor'},
  'policy': 'Editorial policy: this page is an independent summary. It is not sponsored, certified or a hands-on compatibility test. We publish no invented ratings, reviews or prices. Details change — the official site is always authoritative.',
  'founder': 'Disclosure: this tool was built by ToolFavor\'s founder. It is described with the same sourcing rules as every other listing.',
  'founder_link': 'See the creator\'s portfolio →',
  'report': 'Spotted something out of date? Tell us →',
  'related_eyebrow': 'KEEP EXPLORING', 'related_title': 'More tools on ToolFavor', 'related_more': 'Browse the full directory →',
  'pricing': {'free': 'Free', 'freemium': 'Free plan', 'paid': 'Paid'},
  'type': {'web': 'Web app', 'mobile': 'Mobile app', 'desktop': 'Desktop app', 'extension': 'Browser extension'},
  'cat': {'Design': 'Design', 'Productivity': 'Productivity'},
  'category': 'Category', 'type_label': 'Type', 'website': 'Website',
  'footer': '© ToolFavor · Discover, understand and compare useful tools.',
 },
 'ja': {
  'explore': 'ツールを探す', 'developers': '開発者の方へ', 'home': 'ToolFavor',
  'visit': '{name}を開く ↗', 'fit_jump': '自分に合う？ ↓', 'more_tools': 'ほかのツールを探す',
  'cap_eyebrow': 'AT A GLANCE', 'cap_title': '何ができる？', 'cap_note': '各項目から公式の説明を確認できます',
  'check': '公式の説明 ↗',
  'facts_eyebrow': 'KEY FACTS', 'facts_title': '基本情報', 'verified': '最終確認日',
  'fit_eyebrow': 'MAKE A DECISION', 'fit_title': '{name}はあなたに合う？', 'good': 'こんな人におすすめ', 'consider': 'ほかのツールと比べたい人',
  'steps_eyebrow': 'START IN MINUTES', 'steps_title': '3ステップで使い始める',
  'compare_eyebrow': 'CHOOSE THE RIGHT TOOL', 'compare_title': 'ほかのツールとの違い', 'compare_sub': '位置づけと一般的な使い方で比較 · 実機テストのランキングではありません',
  'alt_eyebrow': 'ALTERNATIVES', 'alt_title': '目的によってはこちらも', 'alt_on_site': 'ToolFavorで詳しく →', 'alt_visit': 'サイトを開く ↗',
  'faq_eyebrow': 'QUICK ANSWERS', 'faq_title': 'よくある質問',
  'src_eyebrow': 'TRANSPARENCY', 'src_title': '情報の出典',
  'kind': {'official': '公式', 'third_party': '第三者', 'tested': 'ToolFavor検証'},
  'policy': '編集方針：このページは独立した情報整理です。広告・提携・認証ではなく、実機での互換性テストでもありません。架空の評価・レビュー・価格は掲載しません。情報は変わる場合があるため、最新情報は公式サイトをご確認ください。',
  'founder': '開示：このツールはToolFavorの創設者が制作したものです。ほかの掲載と同じ出典ルールで紹介しています。',
  'founder_link': '制作者のポートフォリオ →',
  'report': '情報が古い場合はお知らせください →',
  'related_eyebrow': 'KEEP EXPLORING', 'related_title': 'ToolFavorのほかのツール', 'related_more': 'ツール一覧を見る →',
  'pricing': {'free': '無料', 'freemium': '無料プランあり', 'paid': '有料'},
  'type': {'web': 'Webアプリ', 'mobile': 'モバイルアプリ', 'desktop': 'デスクトップアプリ', 'extension': 'ブラウザー拡張'},
  'cat': {'Design': 'デザイン', 'Productivity': '仕事効率化'},
  'category': 'カテゴリ', 'type_label': '種類', 'website': '公式サイト',
  'footer': '© ToolFavor · 便利なツールを見つけて、比べて、選ぶ。',
 },
 'zh-cn': {
  'explore': '探索工具', 'developers': '开发者', 'home': 'ToolFavor',
  'visit': '打开 {name} ↗', 'fit_jump': '适合我吗？ ↓', 'more_tools': '浏览更多工具',
  'cap_eyebrow': 'AT A GLANCE', 'cap_title': '它能帮你做什么？', 'cap_note': '每一项都可点击核对官方说明',
  'check': '查看官方说明 ↗',
  'facts_eyebrow': 'KEY FACTS', 'facts_title': '关键信息', 'verified': '最后核对',
  'fit_eyebrow': 'MAKE A DECISION', 'fit_title': '{name} 适合你吗？', 'good': '推荐这些场景', 'consider': '这些情况建议再比较',
  'steps_eyebrow': 'START IN MINUTES', 'steps_title': '第一次用，只要三步',
  'compare_eyebrow': 'CHOOSE THE RIGHT TOOL', 'compare_title': '它和其他工具有什么不同？', 'compare_sub': '按产品定位和典型用法整理，非实测排名',
  'alt_eyebrow': 'ALTERNATIVES', 'alt_title': '这些情况，换个工具更合适', 'alt_on_site': '在 ToolFavor 查看 →', 'alt_visit': '访问官网 ↗',
  'faq_eyebrow': 'QUICK ANSWERS', 'faq_title': '常见问题',
  'src_eyebrow': 'TRANSPARENCY', 'src_title': '信息从哪里来？',
  'kind': {'official': '官方', 'third_party': '第三方', 'tested': 'ToolFavor 实测'},
  'policy': '编辑原则：本页为独立资料整理，不代表官方合作、认证或亲自完成的兼容性测试。无虚构评分、评论或价格；信息可能变化，请以官方页面为准。',
  'founder': '利益披露：本工具由 ToolFavor 创始人开发，介绍时遵循与其他收录相同的来源规则。',
  'founder_link': '查看创作者作品集 →',
  'report': '发现信息过时？告诉我们 →',
  'related_eyebrow': 'KEEP EXPLORING', 'related_title': 'ToolFavor 上的更多工具', 'related_more': '浏览完整目录 →',
  'pricing': {'free': '免费', 'freemium': '有免费方案', 'paid': '付费'},
  'type': {'web': '网页应用', 'mobile': '手机应用', 'desktop': '桌面软件', 'extension': '浏览器扩展'},
  'cat': {'Design': '设计工具', 'Productivity': '效率工具'},
  'category': '分类', 'type_label': '类型', 'website': '官网',
  'footer': '© ToolFavor · 发现、了解并比较值得使用的工具。',
 },
}

TIER_RULES = {
    'basic': {'capabilities': 3, 'facts': 2, 'sources': 1},
    'complete': {'capabilities': 3, 'facts': 3, 'sources': 2, 'fit': 1, 'steps': 3, 'faq': 3},
    'flagship': {'capabilities': 3, 'facts': 4, 'sources': 3, 'fit': 1, 'steps': 3, 'faq': 4,
                 'compare': 3, 'alternatives': 3, 'media': 1},
}


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
        for key in ('capabilities', 'facts', 'steps', 'faq'):
            if len(c.get(key, [])) < rules.get(key, 0):
                errs.append(f'{where} needs {rules[key]}+ {key}')
        if rules.get('fit') and not (c.get('fit', {}).get('good') and c.get('fit', {}).get('consider')):
            errs.append(f'{where} needs fit.good and fit.consider')
        if rules.get('compare') and len(c.get('compare', {}).get('rows', [])) < rules['compare']:
            errs.append(f'{where} needs {rules["compare"]}+ compare rows')
        for item in c.get('capabilities', []) + c.get('facts', []) + c.get('faq', []):
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
    return f"{LOCALES[code][0]}/tools/{slug}.html"


def home_url(code):
    return LOCALES[code][0] + '/'


def ext(url, text, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<a{c} href="{escape(url)}" target="_blank" rel="noopener">{text}</a>'


CSS = """:root{--ink:#25263c;--muted:#6d7185;--line:#e8e7ef;--purple:#7958ed;--lime:#b8f36b;--bg:#fafafc}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--bg);font:15px/1.65 Inter,system-ui,-apple-system,"Hiragino Kaku Gothic ProN","Yu Gothic","Microsoft YaHei",sans-serif}a{color:inherit;text-decoration:none}a:hover{color:#6340dc}a:focus-visible,summary:focus-visible{outline:3px solid #7958ed;outline-offset:3px}.wrap{max-width:1150px;padding:0 24px;margin:auto}.locale-switch{display:flex;justify-content:center;gap:20px;padding:8px;background:#f5f3fc;font-size:12px;color:#6d647e}.locale-switch [aria-current]{font-weight:800;color:#6440dc}header{background:#fff;border-bottom:1px solid var(--line)}.nav{display:flex;align-items:center;justify-content:space-between;min-height:66px;gap:16px}.brand{font-weight:850;font-size:21px;letter-spacing:-.04em;display:flex;align-items:center;gap:8px}.brand img{width:28px;height:28px}.brand span{color:var(--purple)}.navlinks{display:flex;gap:22px;color:var(--muted);font-size:13px}.crumb{font-size:12px;color:var(--muted);padding-top:25px}.crumb span{margin:0 7px}.hero{background:radial-gradient(ellipse at 76% 0%,#e9f5db 0%,transparent 42%),radial-gradient(ellipse at 13% 10%,#eee8ff 0%,transparent 44%);padding-bottom:50px}.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:48px;align-items:center;padding-top:34px}.kicker{color:#704edc;font-size:12px;font-weight:850;letter-spacing:.11em;text-transform:uppercase}.identity{display:flex;align-items:center;gap:17px;margin:16px 0}.appmark{flex:none;width:64px;height:64px;border-radius:18px;background:#181825;color:#fff;font-size:33px;font-weight:750;display:grid;place-items:center;box-shadow:0 14px 30px #25253a21}.identity h1{font-size:clamp(40px,6vw,68px);line-height:1.05;letter-spacing:-.06em;margin:0;overflow-wrap:anywhere}.lead{font-size:clamp(19px,2.2vw,25px);font-weight:700;line-height:1.4;letter-spacing:-.03em;margin:18px 0}.sublead{font-size:14px;max-width:500px;margin:0;color:var(--muted)}.tags{display:flex;gap:7px;flex-wrap:wrap;margin:22px 0}.tag{font-size:12px;border:1px solid #e6e1f8;background:#fff;border-radius:100px;padding:6px 11px;color:#6049a3}.tag.price{background:#eaf8df;border-color:#d4efbf;color:#3f7d27;font-weight:700}.buttons{display:flex;gap:10px;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:1px solid transparent;background:var(--purple);padding:12px 20px;border-radius:12px;color:#fff;font-weight:750;font-size:14px;transition:transform .18s,box-shadow .18s}.btn:hover{color:#fff;transform:translateY(-2px);box-shadow:0 12px 22px #7958ed33}.btn.secondary{background:#fff;border-color:#e1ddec;color:#5f43ba}.btn.secondary:hover{color:#5f43ba}.snapshot{margin-top:16px;font-size:12px;color:var(--muted)}.media{margin:0}.shot{position:relative;background:#20202b;border-radius:19px;padding:9px;box-shadow:0 30px 60px #25243c24;overflow:hidden}.shot img{display:block;width:100%;aspect-ratio:16/10;object-fit:cover;object-position:top left;border-radius:12px;background:#2b2b38}.shot.portrait{background:linear-gradient(145deg,#f5eaff,#ebf5ff);border:1px solid #e4def0;box-shadow:none;display:flex;justify-content:center;padding:16px}.shot.portrait img{width:min(100%,300px);aspect-ratio:auto;max-height:560px;object-fit:contain;background:none}.media figcaption{font-size:11px;color:#7e7c90;margin-top:9px}.media .mock,.media .mock-cap{display:none}.media.failed .shot,.media.failed .real-cap{display:none}.media.failed .mock{display:block}.media.failed .mock-cap{display:block}.mock{background:#20202b;border-radius:19px;padding:9px;box-shadow:0 30px 60px #25243c24;overflow:hidden}.browser-top{display:flex;align-items:center;gap:7px;background:#292936;padding:10px;border-radius:12px 12px 0 0}.dot{height:8px;width:8px;border-radius:50%;background:#77738a}.address{margin:auto;border-radius:5px;background:#3b3b48;color:#c4c1d0;min-width:54%;text-align:center;font-size:10px;padding:3px}.workspace{display:grid;grid-template-columns:39px 1fr 114px;min-height:260px;background:#393946;color:#c8c7d1;font-size:10px}.tools{background:#292934;padding:13px 10px;display:grid;gap:13px}.canvas{padding:17px;display:grid;place-items:center;background:repeating-conic-gradient(#464651 0 25%,#3d3d49 0 50%) 50%/22px 22px}.artwork{width:81%;aspect-ratio:1.25;background:linear-gradient(145deg,#dad9f0 0 38%,#9895c5 39% 45%,#8c9fc8 46% 62%,#d7d3ec 63%);box-shadow:0 12px 28px #0004}.layer{background:#2d2d38;padding:10px 7px}.layer div{padding:10px 4px;border-bottom:1px solid #42424d}.layer .active{background:#555271}.mock.plain{background:none;box-shadow:none;padding:0;border-radius:0}.glance{background:#fff;border:1px solid var(--line);border-radius:19px;padding:26px;box-shadow:0 24px 50px #25243c12}.glance dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:12px 20px;font-size:14px}.glance dt{color:var(--muted)}.glance dd{margin:0;font-weight:700;overflow-wrap:anywhere}.section{padding-top:52px}.section-head{display:flex;justify-content:space-between;align-items:end;gap:15px;margin-bottom:20px}.eyebrow{color:var(--purple);font-size:12px;font-weight:800;letter-spacing:.07em}h2{font-size:clamp(24px,3vw,32px);line-height:1.2;letter-spacing:-.04em;margin:6px 0}h3{font-size:17px;margin:0 0 6px}.small{font-size:12px;color:var(--muted)}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{background:#fff;border:1px solid var(--line);border-radius:17px;padding:23px}.card p{margin:7px 0 0;color:var(--muted);font-size:13px}.card .src{display:inline-block;margin-top:12px;font-size:12px;color:#5f43ba;font-weight:650}.iconbox{display:grid;place-items:center;background:#f0ecff;color:#704ddd;width:42px;height:42px;border-radius:12px;font-size:20px;margin-bottom:18px}.facts{background:#fff;border:1px solid var(--line);border-radius:17px;overflow:hidden}.fact{display:grid;grid-template-columns:180px 1fr auto;gap:16px;padding:15px 22px;border-bottom:1px solid var(--line);font-size:14px;align-items:baseline}.fact:last-child{border-bottom:0}.fact dt{color:var(--muted)}.fact dd{margin:0;font-weight:650}.fact a{font-size:12px;color:#5f43ba;white-space:nowrap}.decision{display:grid;grid-template-columns:1fr 1fr;gap:14px}.decision ul{padding-left:0;list-style:none;margin:12px 0 0;color:#5b6174;font-size:14px}.decision li{margin:10px 0;padding-left:26px;position:relative}.decision li:before{position:absolute;left:0;top:1px;width:18px;height:18px;border-radius:6px;display:grid;place-items:center;font-size:11px;font-weight:900}.decision .yes li:before{content:"✓";background:#eaf8df;color:#43872a}.decision .maybe li:before{content:"↗";background:#fff3e2;color:#b26a12}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.stepno{font-size:12px;color:#7454e1;font-weight:900;margin-bottom:12px}.compare-wrap{background:#fff;border:1px solid var(--line);border-radius:17px;overflow-x:auto}.compare-table{width:100%;border-collapse:collapse;text-align:left;font-size:13px;min-width:640px}.compare-table th,.compare-table td{padding:14px 15px;border-bottom:1px solid var(--line);vertical-align:top}.compare-table thead th{color:#4c456e;background:#f7f5fd;font-size:12px}.compare-table tbody tr:last-child td,.compare-table tbody tr:last-child th{border-bottom:0}.compare-table .self{background:#fbfaff}.compare-table .self th{color:#5b40b7}.alts{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}.alt{display:flex;flex-direction:column}.alt-top{display:flex;justify-content:space-between;align-items:center;gap:10px}.chip{font-size:11px;font-weight:750;color:#5b40b7;background:#f0ecff;border-radius:100px;padding:3px 9px;white-space:nowrap}.alt p{flex:1}.alt .go{margin-top:14px;font-size:13px;font-weight:700;color:#5f43ba}.accordion{background:#fff;border:1px solid var(--line);border-radius:13px;margin-bottom:9px}.accordion summary{list-style:none;cursor:pointer;padding:17px 20px;font-weight:650;display:flex;justify-content:space-between;gap:12px}.accordion summary::-webkit-details-marker{display:none}.accordion summary:after{content:"+";font-size:20px;color:#7958ed;line-height:1}.accordion[open] summary:after{content:"−"}.accordion .answer{padding:0 20px 18px;color:var(--muted);font-size:14px}.accordion .answer p{margin:0 0 8px}.accordion .answer a{font-size:12px;color:#5f43ba;font-weight:650}.references{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.ref{display:block;background:#fff;padding:16px;border:1px solid var(--line);border-radius:13px;font-size:13px}.ref:hover{border-color:#b6a5f9}.ref .meta{display:flex;gap:8px;align-items:center;color:var(--muted);font-size:11px;margin-top:7px;overflow-wrap:anywhere}.ref .kind{flex:none;white-space:nowrap;color:#3f7d27;background:#eaf8df;border-radius:5px;padding:1px 6px;font-weight:700}.policy{margin-top:16px;font-size:12px;color:var(--muted);max-width:820px}.policy p{margin:6px 0}.policy a{color:#5f43ba;font-weight:650}.related{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.related .card{display:block}.related .card:hover{border-color:#b6a5f9}.bottom{margin:54px 0;background:#25243b;border-radius:20px;color:#fff;padding:35px;display:flex;justify-content:space-between;gap:20px;align-items:center}.bottom h2{font-size:24px;margin:0}.bottom p{margin:6px 0 0;color:#c7c5d5;font-size:13px}.bottom .btn{background:var(--lime);color:#242c20;flex:none}.bottom .btn:hover{color:#242c20}footer{border-top:1px solid var(--line);padding:27px 0;color:var(--muted);font-size:12px}footer .wrap{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}@media(max-width:850px){.hero-grid{grid-template-columns:1fr;gap:30px}.grid3,.steps,.references,.related{grid-template-columns:1fr 1fr}.fact{grid-template-columns:140px 1fr}.fact a{grid-column:2}}@media(max-width:620px){.wrap{padding:0 16px}.navlinks{gap:12px}.hero{padding-bottom:34px}.hero-grid{padding-top:22px}.identity h1{font-size:40px}.appmark{width:52px;height:52px;font-size:27px}.workspace{min-height:200px;grid-template-columns:30px 1fr 75px}.layer{font-size:8px}.grid3,.steps,.references,.decision,.related{grid-template-columns:1fr}.fact{grid-template-columns:1fr;gap:2px;padding:13px 18px}.fact a{grid-column:1}.section{padding-top:40px}.card{padding:19px}.bottom{display:block;padding:25px}.bottom .btn{margin-top:18px}.section-head{align-items:start;flex-direction:column}.glance dl{grid-template-columns:1fr;gap:2px}.glance dd{margin-bottom:10px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.btn{transition:none}}"""

EDITOR_MOCK = ('<div class="browser-top"><i class="dot"></i><i class="dot"></i><i class="dot"></i><span class="address">{domain}</span></div>'
               '<div class="workspace" aria-hidden="true"><div class="tools"><span>✥</span><span>▧</span><span>◯</span><span>⌗</span><span>✎</span></div>'
               '<div class="canvas"><div class="artwork"></div></div><div class="layer"><div class="active">▣ Layer 3</div><div>▣ Layer 2</div><div>▧ Background</div></div></div>')


def render_media(t, c, u):
    media = t.get('media') or []
    if not media:
        return None
    m = media[0]
    fallback = m.get('fallback')
    cls = 'media'
    portrait = ' portrait' if m.get('portrait') else ''
    img = (f'<img src="{escape(m["src"])}" alt="{escape(c["media_alt"])}" loading="eager" decoding="async" '
           f'fetchpriority="high" referrerpolicy="no-referrer" onerror="this.closest(\'figure\').classList.add(\'failed\')">')
    out = f'<figure class="{cls}"><div class="shot{portrait}">{img}</div>'
    out += f'<figcaption class="real-cap">{escape(c.get("media_caption", ""))}</figcaption>'
    if fallback == 'editor-mock':
        out += f'<div class="mock" aria-hidden="true">{EDITOR_MOCK.format(domain=escape(t["domain"]))}</div>'
        out += f'<figcaption class="mock-cap">{escape(c.get("mock_caption", ""))}</figcaption>'
    else:  # if the image cannot load, show the key-facts card instead
        out += f'<div class="mock plain">{render_glance(t, c, u)}</div>'
    return out + '</figure>'


def render_glance(t, c, u):
    rows = [(u['category'], u['cat'].get(t['category'], t['category'])),
            (u['type_label'], u['type'][t['type']]),
            (c['facts'][0]['label'], c['facts'][0]['value']) if c.get('facts') else None,
            (u['website'], ext(t['url'], escape(t['domain']) + ' ↗')),
            (u['verified'], t['last_verified'])]
    body = ''.join(f'<dt>{escape(k)}</dt><dd>{v if k == u["website"] else escape(v)}</dd>' for k, v in filter(None, rows))
    return f'<div class="glance"><dl>{body}</dl></div>'


def section(id_, eyebrow, title, inner, sub=''):
    s = f'<p class="small">{escape(sub)}</p>' if sub else ''
    return (f'<section class="section" id="{id_}" aria-labelledby="{id_}-h"><div class="section-head"><div>'
            f'<div class="eyebrow">{escape(eyebrow)}</div><h2 id="{id_}-h">{escape(title)}</h2></div>{s}</div>{inner}</section>')


def json_ld(t, c, code, tools_by_slug):
    url = SITE + page_url(t['slug'], code)
    app = {'@type': 'SoftwareApplication', 'name': t['name'], 'url': t['url'],
           'description': c['description'], 'applicationCategory': t['schema']['applicationCategory'],
           'operatingSystem': t['schema']['operatingSystem']}
    if t['pricing'] in ('free', 'freemium'):
        app['offers'] = {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'}
    if t.get('media') and not t['media'][0].get('portrait'):
        app['screenshot'] = t['media'][0]['src']
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
    slug, name = t['slug'], t['name']
    src = t['sources']
    canonical = SITE + page_url(slug, code)

    alternates = ''.join(f'<link rel="alternate" hreflang="{LOCALES[k][2]}" href="{SITE + page_url(slug, k)}">' for k in LOCALES)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{SITE + page_url(slug, "en")}">'
    og_image = ''
    if t.get('media'):
        og_image = f'<meta property="og:image" content="{escape(t["media"][0]["src"])}"><meta name="twitter:card" content="summary_large_image">'
    head = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="theme-color" content="#fafafc"><title>{escape(c["title"])}</title>'
            f'<meta name="description" content="{escape(c["description"])}"><link rel="canonical" href="{canonical}">{alternates}'
            f'<meta property="og:type" content="website"><meta property="og:site_name" content="ToolFavor"><meta property="og:locale" content="{og_locale}">'
            f'<meta property="og:title" content="{escape(c["title"])}"><meta property="og:description" content="{escape(c["description"])}">'
            f'<meta property="og:url" content="{canonical}">{og_image}'
            f'<link rel="icon" href="/favicon-96x96.png" sizes="96x96"><link rel="icon" href="/assets/toolfavor-mark.svg" type="image/svg+xml">'
            f'<style>{CSS}</style><script type="application/ld+json">{json_ld(t, c, code, tools_by_slug)}</script></head>')

    langs = ''.join(f'<a href="{page_url(slug, k)}" lang="{LOCALES[k][1]}"' + (' aria-current="page"' if k == code else '') + f'>{LANG_LABEL[k]}</a>' for k in LOCALES)
    header = (f'<nav aria-label="Language" class="locale-switch">{langs}</nav>'
              f'<header><div class="wrap nav"><a class="brand" href="{home_url(code)}"><img src="/assets/toolfavor-mark.svg" alt="" width="28" height="28">ToolFavor<span>.</span></a>'
              f'<nav class="navlinks" aria-label="Main"><a href="{home_url(code)}">{escape(u["explore"])}</a><a href="{prefix}/developers.html">{escape(u["developers"])}</a></nav></div></header>')

    cat = u['cat'].get(t['category'], t['category'])
    crumb = (f'<nav class="crumb" aria-label="Breadcrumb"><a href="{home_url(code)}">{escape(u["explore"])}</a><span>/</span>'
             f'{escape(cat)}<span>/</span><span aria-current="page" style="margin:0">{escape(name)}</span></nav>')
    tags = ''.join(f'<span class="tag">{escape(x)}</span>' for x in c.get('tags', []))
    tags += f'<span class="tag price">{escape(c["pricing_label"])}</span>'
    fit_btn = f'<a class="btn secondary" href="#fit">{escape(u["fit_jump"])}</a>' if c.get('fit') else f'<a class="btn secondary" href="{home_url(code)}">{escape(u["more_tools"])}</a>'
    visual = render_media(t, c, u) or render_glance(t, c, u)
    hero = (f'<section class="hero"><div class="wrap">{crumb}<div class="hero-grid"><div>'
            f'<div class="kicker">{escape(c["kicker"])}</div>'
            f'<div class="identity"><div class="appmark" aria-hidden="true">{escape(t["mark"])}</div><h1>{escape(name)}</h1></div>'
            f'<p class="lead">{escape(c["lead"])}</p><p class="sublead">{escape(c["sublead"])}</p>'
            f'<div class="tags">{tags}</div>'
            f'<div class="buttons">{ext(t["url"], escape(u["visit"].format(name=name)), "btn")}{fit_btn}</div>'
            f'<p class="snapshot">{escape(c["snapshot"])} · {escape(u["verified"])} {t["last_verified"]}</p>'
            f'</div>{visual}</div></div></section>')

    body = []
    cards = ''.join(f'<article class="card"><div class="iconbox" aria-hidden="true">{escape(x["icon"])}</div><h3>{escape(x["title"])}</h3>'
                    f'<p>{escape(x["text"])}</p>{ext(src[x["source"]]["url"], escape(u["check"]), "src")}</article>' for x in c['capabilities'])
    body.append(section('features', u['cap_eyebrow'], u['cap_title'], f'<div class="grid3">{cards}</div>', u['cap_note']))

    facts = [(u['category'], escape(cat), None), (u['type_label'], escape(u['type'][t['type']]), None)]
    facts += [(f['label'], escape(f['value']), f['source']) for f in c['facts']]
    facts += [(u['website'], ext(t['url'], escape(t['domain']) + ' ↗'), None), (u['verified'], t['last_verified'], None)]
    rows = ''.join(f'<div class="fact"><dt>{escape(k)}</dt><dd>{v}</dd>' + (ext(src[s]['url'], escape(u['check'])) if s else '<span></span>') + '</div>' for k, v, s in facts)
    body.append(section('facts', u['facts_eyebrow'], u['facts_title'], f'<dl class="facts">{rows}</dl>'))

    if c.get('fit'):
        good = ''.join(f'<li>{escape(x)}</li>' for x in c['fit']['good'])
        maybe = ''.join(f'<li>{escape(x)}</li>' for x in c['fit']['consider'])
        body.append(section('fit', u['fit_eyebrow'], u['fit_title'].format(name=name),
                            f'<div class="decision"><div class="card yes"><h3>{escape(u["good"])}</h3><ul>{good}</ul></div>'
                            f'<div class="card maybe"><h3>{escape(u["consider"])}</h3><ul>{maybe}</ul></div></div>'))

    if c.get('steps'):
        steps = ''.join(f'<article class="card"><div class="stepno">{escape(s["label"])}</div><h3>{escape(s["title"])}</h3><p>{escape(s["text"])}</p></article>' for s in c['steps'])
        body.append(section('start', u['steps_eyebrow'], u['steps_title'], f'<div class="steps">{steps}</div>'))

    if c.get('compare'):
        cmp = c['compare']
        links = t.get('compare_links', {})
        head_row = ''.join(f'<th scope="col">{escape(h)}</th>' for h in cmp['columns'])
        trs = ''
        for r in cmp['rows']:
            is_self = r[0] == name
            first = escape(r[0]) if is_self or r[0] not in links else ext(links[r[0]], escape(r[0]) + ' ↗')
            trs += f'<tr{" class=self" if is_self else ""}><th scope="row">{first}</th>' + ''.join(f'<td>{escape(x)}</td>' for x in r[1:]) + '</tr>'
        note_links = ' · '.join(ext(url, escape(n) + ' ↗') for n, url in links.items())
        inner = (f'<div class="compare-wrap"><table class="compare-table"><thead><tr>{head_row}</tr></thead><tbody>{trs}</tbody></table></div>'
                 f'<p class="small">{escape(cmp["note"])} {note_links}</p>')
        body.append(section('compare', u['compare_eyebrow'], u['compare_title'], inner, u['compare_sub']))

    if t.get('alternatives'):
        cards = ''
        for a in t['alternatives']:
            on_site = a['key'] in tools_by_slug
            link = (f'<a class="go" href="{page_url(a["key"], code)}">{escape(u["alt_on_site"])}</a>' if on_site
                    else ext(a['url'], escape(u['alt_visit']), 'go'))
            cards += (f'<article class="card alt"><div class="alt-top"><h3>{escape(a["name"])}</h3>'
                      f'<span class="chip">{escape(u["pricing"][a["pricing"]])}</span></div>'
                      f'<p>{escape(c["alternatives"][a["key"]])}</p>{link}</article>')
        body.append(section('alternatives', u['alt_eyebrow'], u['alt_title'], f'<div class="alts">{cards}</div>'))

    if c.get('faq'):
        items = ''.join(f'<details class="accordion"{" open" if i == 0 else ""}><summary>{escape(f["q"])}</summary>'
                        f'<div class="answer"><p>{escape(f["a"])}</p>{ext(src[f["source"]]["url"], escape(u["check"]))}</div></details>'
                        for i, f in enumerate(c['faq']))
        body.append(section('faq', u['faq_eyebrow'], u['faq_title'], items))

    refs = ''.join(f'<a class="ref" href="{escape(s["url"])}" target="_blank" rel="noopener">{escape(c["source_labels"][k])} ↗'
                   f'<span class="meta"><span class="kind">{escape(u["kind"][s["kind"]])}</span>{escape(re.sub(r"^https?://", "", s["url"]).rstrip("/"))}</span></a>'
                   for k, s in src.items())
    policy = f'<p>{escape(u["policy"])}</p>'
    if t.get('related_by_founder'):
        policy += f'<p>{escape(u["founder"])} <a href="{prefix}/creators/1/">{escape(u["founder_link"])}</a></p>'
    policy += f'<p><a href="{prefix}/contact.html">{escape(u["report"])}</a></p>'
    body.append(section('sources', u['src_eyebrow'], u['src_title'], f'<div class="references">{refs}</div><div class="policy">{policy}</div>'))

    others = [o for o in tools_by_slug.values() if o['slug'] != slug and o['slug'] not in {a['key'] for a in t.get('alternatives', [])}]
    others.sort(key=lambda o: (o['category'] != t['category'], o['name']))
    if others:
        cards = ''.join(f'<a class="card" href="{page_url(o["slug"], code)}"><div class="alt-top"><h3>{escape(o["name"])}</h3>'
                        f'<span class="chip">{escape(UI[code]["pricing"][o["pricing"]])}</span></div><p>{escape(o["i18n"][code]["lead"])}</p></a>'
                        for o in others[:3])
        body.append(section('related', u['related_eyebrow'], u['related_title'],
                            f'<div class="related">{cards}</div><p class="small"><a href="{home_url(code)}">{escape(u["related_more"])}</a></p>'))

    cta = c['cta']
    bottom = (f'<div class="bottom"><div><h2>{escape(cta["title"])}</h2><p>{escape(cta["text"])}</p></div>'
              f'{ext(t["url"], escape(u["visit"].format(name=name)), "btn")}</div>')
    footer = f'<footer><div class="wrap"><span>{escape(u["footer"])}</span><a href="{home_url(code)}">{escape(u["more_tools"])} →</a></div></footer>'
    return head + '<body>' + header + '<main>' + hero + '<div class="wrap">' + ''.join(body) + bottom + '</div></main>' + footer + '</body></html>\n'


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
            dest = ROOT / page_url(t['slug'], code).lstrip('/')
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(render(t, code, by_slug))
    update_sitemap(tools)
    print(f'Generated {len(tools) * len(LOCALES)} detail pages for {len(tools)} tools.')


if __name__ == '__main__':
    main()
