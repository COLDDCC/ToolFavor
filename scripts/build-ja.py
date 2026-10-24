"""Generate Japanese pages from the English source; run after editing the catalog."""
from pathlib import Path
import html, json, re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['index.html', 'developers.html', 'contact.html', 'creators/1/index.html']
# Tool detail pages are generated per locale by build-tool-pages.py from data/tools/*.json.
# They are listed here only so links to them get localized.
TOOL_PAGES = sorted('tools/'+p.stem+'.html' for p in (ROOT/'data'/'tools').glob('*.json'))
LINK_TARGETS = PAGES + TOOL_PAGES
UI = {
 'Explore':'ツールを探す','For Developers':'開発者の方へ','For developers':'開発者の方へ',
 'Contact / Feedback':'お問い合わせ','Creator portfolio · EN / 中文 / 日本語':'制作者のポートフォリオ',
 'About':'掲載について','+ Submit a site':'＋ サイトを掲載する',
 'A curated corner of the internet':'使ってみたいWebサイトを、ここから', 'Independent picks':'独自のセレクト',
 'Discover The Best':'仕事と創作に役立つ','Websites & Tools':'Webサイト・ツールを探す',
 'Useful tools, remarkable websites, and creative inspiration. Find what you need without the endless scrolling.':'AI、デザイン、開発、日々の作業に。用途や料金から、自分に合うツールを見つけましょう。',
 'Search →':'検索 →','Explore the collection':'用途から探す','All pricing':'すべての料金',
 'Free':'無料','Freemium':'無料プランあり','Paid':'有料','Websites & tools':'サイト・ツールすべて',
 'Tools only':'ツールのみ','Websites only':'サイトのみ','Featured':'おすすめ順','Name A–Z':'名前順 A–Z',
 'Show more websites':'もっと見る','No matching results. Try clearing a filter or searching again.':'該当するサイトが見つかりません。条件や検索語を変えてみてください。',
 'Curated starter collection. Pricing and availability may change; verify details with each website.':'料金や提供状況は変更される場合があります。利用前に各公式サイトをご確認ください。',
 'Built something useful?':'あなたのサイトも紹介しませんか？',
 'Share your tool, creative website, or developer project. Submissions are free.':'便利なツール、個性的なサイト、開発プロジェクトを募集中。掲載申請は無料です。',
 'Submit your website →':'サイトを掲載申請 →','Independent discovery directory · No sponsored rankings':'独自に選ぶツール案内 · 広告による順位付けなし',
 'Submit a website':'サイトの掲載申請',
 'Submit your site for review through GitHub. This opens a public GitHub issue form for review. A GitHub account is required.':'GitHubの公開フォームから掲載を申請できます。GitHubアカウントが必要です。申請内容は公開されます。',
 'Website name':'サイト名','Website URL':'サイトのURL','Type':'種類','Tool':'ツール','Website':'Webサイト',
 'Short description':'簡単な紹介','Cancel':'キャンセル','Submit via GitHub →':'GitHubで申請 →',
 'Free AI Video Generators — 2026 Comparison':'無料AI動画生成ツール比較【英語】',
 'Compare 9 tools, free credits, watermarks and official links.':'9サービスの無料枠・透かし・公式リンクを比較。',
 'Explore guide →':'英語のガイドを見る →','DeepSwapper vs DeepSwapFace — Which Is Free?':'DeepSwapperとDeepSwapFace、無料で使えるのは？【英語】',
 'Compare photo swaps, video subscriptions, daily limits and privacy claims.':'画像・動画の顔交換、利用上限、料金、プライバシーの説明を比較。',
 'Read comparison →':'英語の比較を見る →','Free AI Logo Generators — PNG, SVG & No-Signup Filters':'無料AIロゴ作成：PNG・SVG・登録不要で比較【英語】',
 'Find out what you can actually download for free.':'無料で保存できる形式や利用条件を確認できます。','Compare tools →':'英語の比較を見る →',
 'Explore tools':'ツール一覧','Design · Web tool':'デザイン · Webツール','Productivity · Web tool':'作業効率化 · Webツール',
 'Design':'デザイン','Productivity':'作業効率化','Web tool':'Webツール',
 'Visit official website ↗':'公式サイトを開く ↗','Browse more tools':'ほかのツールを探す',
 'What you can do':'できること','About this listing':'この紹介について','At a glance':'基本情報','Category':'カテゴリ','Pricing model':'料金体系',
 'ToolFavor helps you discover independent websites and useful tools. This page is an editorial introduction, not a review or endorsement.':'ToolFavorは便利なツールや個人制作のサイトを紹介しています。このページは編集部による概要紹介です。レビューや推奨の認証ではありません。',
 'Features, pricing and availability can change. Check the official website for current details.':'機能、料金、提供状況は変更される場合があります。最新情報は公式サイトをご確認ください。',
 'Edit photos and layered graphics directly in a browser.':'写真やレイヤー付きの画像を、ブラウザー上で編集できます。',
 'Edit images in the browser':'ブラウザー上で画像を編集','Work with layered graphics':'レイヤー付きの画像を編集','Export designs in common image formats':'一般的な画像形式で書き出し',
 'Create printable graph paper and custom grids for study, planning, and design.':'勉強、計画、デザインに使う方眼紙を、好きなグリッドで作れます。',
 'Configure a grid to match your project':'用途に合わせてグリッドを設定','Generate printable paper layouts':'印刷用の用紙レイアウトを作成','Download and print your result':'完成した用紙を保存・印刷',
 'Convert hourly wages into estimated earnings across common pay periods.':'時給をもとに、働く時間に応じた収入の目安を計算できます。',
 'Compare hourly and salary figures':'時給と給与を換算・比較','Explore different work schedules':'勤務時間を変えて比較','Estimate income before making decisions':'働き方を決める前に収入を試算',
 'Meet the creator':'制作者について','Explore more projects featured in the founding creator portfolio.':'創設者のポートフォリオで、ほかの制作物もご覧いただけます。','COLDDCC’s projects →':'COLDDCCの制作実績 →',
 '© ToolFavor · Independent discovery directory':'© ToolFavor · 便利なWebサイトとツールの案内',
 'For Developers':'開発者の方へ','Your work deserves to be':'あなたの制作物を、','discovered.':'必要としている人へ。',
 'ToolFavor brings together useful tools, inspiring websites, and the people who build them. Submit a project to our curated directory.':'便利なツールや魅力的なサイトと、その作り手を紹介しています。あなたのプロジェクトも掲載を申請できます。',
 'Free listings':'基本掲載は無料','Share your tool or creative website for editorial review. We do not charge for standard submissions.':'ツールやサイトを編集部の審査にお送りください。通常の掲載申請に料金はかかりません。',
 'Curated discovery':'用途から見つかる','Help people find your work by category, task, and pricing model. Inclusion is subject to review.':'カテゴリ、用途、料金から制作物を探せます。掲載には審査があります。',
 'Developer profiles':'開発者プロフィール','Planned: a free portfolio connecting your tools and websites under one public profile.':'ツールやWebサイトを一つにまとめる、無料ポートフォリオ機能を計画しています。',
 'Coming later — not yet available.':'一般向けには準備中です。','Permanent creator IDs':'固定のクリエイター番号',
 'Planned: a unique, permanent numeric ID paired with your username, issued by our future account database.':'ユーザー名と組み合わせて使う、変更されない数字のIDを計画しています。',
 'No IDs are being issued yet.':'一般向けのID発行はまだ開始していません。','See a creator portfolio':'ポートフォリオの例を見る',
 'Preview how projects from an existing personal website can live together on ToolFavor.':'複数の制作物を一つにまとめたプロフィールをご覧いただけます。',
 'Explore COLDDCC’s portfolio →':'COLDDCCのポートフォリオ →','How submission works':'掲載申請の流れ',
 'Open the GitHub form, provide your website URL and a clear description, then submit it for review. Submission does not guarantee publication. Never submit passwords or private information.':'GitHubのフォームにURLと紹介文を入力し、審査にお送りください。申請しても掲載が確約されるものではありません。パスワードや非公開情報は入力しないでください。',
 'Contact / Feedback →':'お問い合わせ →','← Back to directory':'← ツール一覧に戻る',
 'Creator portfolio (EN)':'ポートフォリオ（英語）','个人作品集（中文）':'ポートフォリオ（中国語）',
 'Creator portfolio →':'制作者のポートフォリオ →','Contact · Feedback':'お問い合わせ・ご意見',
 'Have an idea or a correction?':'ご意見や修正のご連絡はこちらへ',
 'Report a broken link, suggest a better description, ask about collaboration, or get in touch about work opportunities.':'リンク切れ、紹介文の修正、共同制作、お仕事のご相談などを受け付けています。',
 'Write to ToolFavor':'ToolFavorに連絡する',
 'This form opens your email app with a prepared message. It does not send data to our server. Please avoid including sensitive information.':'入力内容を入れたメール作成画面が開きます。このフォームからサーバーに情報は送信されません。機密情報は入力しないでください。',
 'What is this about?':'お問い合わせの種類','Website feedback':'サイトへのご意見','Incorrect tool information':'ツール情報の修正','Collaboration':'共同制作のご相談','Hiring / portfolio inquiry':'採用・制作実績について','Other':'その他',
 'Your name (optional)':'お名前（任意）','Message':'お問い合わせ内容','Open email app →':'メールアプリを開く →',
 'No email app configured? Write directly to':'メールアプリを使わない場合はこちらへ：','Home':'ホーム',
 'Web Tool':'Webツール','Printable':'印刷用','Images':'画像','Utility':'便利ツール','Team Builder':'編成ツール',
 'Calculator':'計算ツール','Music':'音楽','Educational':'学習','Company project':'業務関連','Healthcare':'医療',
 'Multilingual':'多言語','Anime':'アニメ','Information architecture':'情報設計','Operations':'運用','Browser extension':'ブラウザー拡張',
 'View project ↗':'制作物を見る ↗','View source ↗':'ソースを見る ↗','Visit website ↗':'サイトを開く ↗',
 'Contact / Feedback ↗':'お問い合わせ ↗',
 'This is a curated portfolio, not a verified employment record. Company-associated work is labeled separately. Project links do not guarantee current availability; roles and contributions can be clarified on request.':'制作実績をまとめたポートフォリオです。企業関連の制作物は区別して掲載しています。リンク先の公開状況や共同制作の担当範囲は、必要に応じてお問い合わせください。',
 '© ToolFavor · Discover The Best Websites & Tools':'© ToolFavor · 便利なWebサイトとツールを探す',
}
CATS = {'All':'すべて','AI':'AI','AI Images':'AI画像生成','AI Video':'AI動画生成','Design':'デザイン','Developer':'開発','Productivity':'作業効率化','Inspiration':'アイデア・参考','Learning':'学習','Video & Audio':'動画・音声','Marketing':'マーケティング','Discovery':'サービスを探す'}

def clean_path(path):
    # Cloudflare Pages 308-redirects *.html to the extensionless URL; always publish that one.
    path = path.replace('index.html', '')
    return path[:-5] if path.endswith('.html') else path

def local_url(path):
    return '/ja/' + clean_path(path)

def english_url(path):
    return '/' + clean_path(path)

def seo(h, path, ja):
    h = re.sub(r'<!-- locale-links -->.*?<!-- /locale-links -->','',h,flags=re.S)
    en, jp = english_url(path), local_url(path)
    tags = '<!-- locale-links -->' + ''.join(f'<link rel="alternate" hreflang="{lang}" href="https://toolfavor.com{url}">' for lang,url in [('en',en),('ja',jp),('x-default',en)]) + '<!-- /locale-links -->'
    h=h.replace('</head>',tags+'</head>')
    if ja:
        h=h.replace('<html lang="en">','<html lang="ja">')
        h=re.sub(r'<link rel="canonical"[^>]*>',f'<link rel="canonical" href="https://toolfavor.com{jp}">',h)
    return h

def switch(h,path,ja):
    h=re.sub(r'<!-- language-nav -->.*?<!-- /language-nav -->','',h,flags=re.S)
    nav=f'<!-- language-nav --><nav aria-label="Language" class="locale-switch"><a href="{english_url(path)}" lang="en"'+(' aria-current="page"' if not ja else '')+'>English</a><a href="'+local_url(path)+'" lang="ja"'+(' aria-current="page"' if ja else '')+'>日本語</a></nav><!-- /language-nav -->'
    css='<style>.locale-switch{display:flex;justify-content:center;gap:14px;padding:10px 16px;background:#fff;font:13px/1.5 system-ui,sans-serif;border-bottom:1px solid #dfe3ee}.locale-switch a{color:#6548d6}.locale-switch [aria-current]{font-weight:750;text-decoration:underline}html[lang=ja] body{font-family:system-ui,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif}html[lang=ja] h1{line-height:1.35;letter-spacing:-.025em}html[lang=ja] .nav{height:auto;min-height:68px;flex-wrap:wrap;padding-block:12px}html[lang=ja] .links{flex-wrap:wrap}html[lang=ja] p{overflow-wrap:anywhere}</style>'
    return h.replace('</head>',css+'</head>',1).replace('<body>','<body>'+nav,1)

def translate_markup(h):
    # Do not replace names or strings in the executable catalog data.
    parts=re.split(r'(<script\b.*?</script>)',h,flags=re.S)
    for i in range(0,len(parts),2):
        def text_node(m):
            raw=m[1]; text=html.unescape(raw).strip()
            if text in UI:
                return '>'+html.escape(UI[text],quote=False)+'<'
            return m[0]
        parts[i]=re.sub(r'>([^<>]+)<',text_node,parts[i])
        for src,dst in sorted(UI.items(),key=lambda kv:-len(kv[0])):
            for form in {src,html.escape(src,quote=False)}:
                parts[i]=parts[i].replace('>'+form+'<','>'+html.escape(dst,quote=False)+'<')
        # Attributes have their own values; avoid translating URLs or IDs.
        for src,dst in {'Search tools and websites':'ツールやWebサイトを検索','Search websites, tools, or what you want to do...':'ツール名・用途・キーワードで検索…','Pricing':'料金','Type':'種類','Sort':'並び順'}.items():
            parts[i]=parts[i].replace('"'+src+'"','"'+dst+'"')
    return ''.join(parts)

def build():
    source=(ROOT/'index.html').read_text()
    catalog=json.JSONDecoder().raw_decode(source.split('const data=',1)[1])[0]
    descriptions=(ROOT/'scripts/ja-descriptions.txt').read_text().splitlines()
    assert len(descriptions)==len(catalog), (len(descriptions),len(catalog))
    for path in PAGES:
        p=ROOT/path; en=p.read_text()
        en=re.sub(r'<style>\.locale-switch\{.*?</style>','',en,flags=re.S)
        h=en
        h=translate_markup(h)
        if path=='index.html':
            old=json.JSONDecoder().raw_decode(h.split('const data=',1)[1])[0]
            translated=[[*x[:2],d,*x[3:],x[2]] for x,d in zip(old,descriptions)]
            begin=h.index('const data=')+len('const data=');_,length=json.JSONDecoder().raw_decode(h[begin:])
            h=h[:begin]+json.dumps(translated,ensure_ascii=False,separators=(',',':'))+h[begin+length:]
            h=h.replace("b.textContent=c;","b.textContent=labels[c]||c;")
            h=h.replace("const cats=","const labels="+json.dumps(CATS,ensure_ascii=False)+";const cats=")
            h=h.replace("[x[0],x[1],x[2],x[3]]","[x[0],x[1],x[2],x[3],x[7],labels[x[3]]]")
            h=h.replace("'/tools/'+detail","'/ja/tools/'+detail")
            h=h.replace("[x[3],x[5]==='freemium'?'Freemium':x[5]==='free'?'Free':'Paid']","[labels[x[3]]||x[3],x[5]==='freemium'?'無料プランあり':x[5]==='free'?'無料':'有料']")
            h=h.replace("detail?'Details →':'Visit ↗'","detail?'詳細 →':'サイトへ ↗'")
            h=h.replace("detail?'View details for '+x[0]:'Visit '+x[0]+' (opens in new tab)'","detail?x[0]+'の詳細':x[0]+'を開く（新しいタブ）'")
            h=h.replace("rows.length+' curated results · Showing '+Math.min(visibleLimit,rows.length)","rows.length+'件中 '+Math.min(visibleLimit,rows.length)+'件を表示'")
            h=h.replace('Redirecting to the public GitHub submission form. A GitHub account is required.','GitHubの公開申請フォームを開きます。GitHubアカウントが必要です。')
            h=h.replace('<title>ToolFavor — Discover The Best Websites & Tools</title>','<title>便利なWebサイト・AIツールを探す | ToolFavor</title>')
            h=h.replace('Discover the best websites and tools. Curated useful apps, developer resources, and inspiring websites.','AI画像生成・動画生成、デザイン、開発、仕事効率化のツールを日本語で紹介。用途や無料プランの有無から探せるToolFavor。')
        elif path=='creators/1/index.html':
            msgstart=h.index('const messages=')+len('const messages='); messages=json.JSONDecoder().raw_decode(h[msgstart:])[0]
            ds=h.index('const projectDescriptions=')+len('const projectDescriptions='); desc=json.JSONDecoder().raw_decode(h[ds:])[0]
            h=re.sub(r'(<[a-z0-9]+\b[^>]*data-i18n="([^"]+)"[^>]*>)(.*?)(</[a-z0-9]+>)',lambda m:m[1]+html.escape(messages['ja'].get(m[2],m[3]))+m[4],h,flags=re.S)
            h=re.sub(r'(<p data-project-desc="(\d+)">).*?(</p>)',lambda m:m[1]+html.escape(desc['ja'][int(m[2])])+m[3],h)
            h=re.sub(r'<div class="langbar"[^>]*>.*?</div>','',h,flags=re.S)
            h=h.replace('let initial=new URLSearchParams(location.search).get("lang");','let initial="ja";')
            h=h.replace('"Professional headline"','"肩書き"').replace('"Education / background"','"学歴・経歴"').replace('"Core skills"','"主なスキル"').replace('"Work preference / collaboration"','"働き方・協業"').replace('"About me"','"自己紹介"')
            h=h.replace('Save in this browser','このブラウザーに保存').replace('Saved locally · not published to other visitors.','このブラウザーに保存しました。ほかの方には公開されません。').replace('Preview updated; browser storage unavailable.','プレビューを更新しましたが、ブラウザーに保存できませんでした。')
            h=h.replace('save.textContent="Save in this browser"','save.textContent="このブラウザーに保存"').replace('cancel.textContent="Cancel"','cancel.textContent="キャンセル"')
            h=h.replace('Display name (up to 40 characters)','表示名（40文字以内）')
            for src,dst in {'About me · 个人简介':'自己紹介','✎ 修改简介':'✎ 自己紹介を編集','Edit profile details':'プロフィールを編集','Personal edits are stored in this browser only.':'編集内容はこのブラウザーだけに保存されます。','Independent developer · Portfolio':'個人開発者 · ポートフォリオ','Featured creator':'注目のクリエイター','Original portfolio source ↗':'元のポートフォリオ ↗','Permanent ID':'固定ID','Creative Website':'個人サイト','Travel':'旅行','SEO Content':'SEOコンテンツ','Gaming':'ゲーム','Research':'調査'}.items():
                h=h.replace(src,dst)
            h=h.replace('<title>COLDDCC — Independent Web Developer & SEO Portfolio | ToolFavor</title>','<title>COLDDCCの制作実績：Web制作・SEO・AI活用 | ToolFavor</title>')
            h=h.replace('COLDDCC portfolio: independent web products, technical SEO, multilingual websites, content operations and AI-assisted workflows.','COLDDCCの制作実績。Webツール、多言語サイト、テクニカルSEO、コンテンツ運用、AIを活用した制作をご紹介。')
        else:
            h=re.sub(r'<title>(.*?)</title>',lambda m:'<title>'+({'developers.html':'開発者向け：サイト掲載とポートフォリオ','contact.html':'お問い合わせ・修正のご連絡'}.get(path,Path(path).stem+'の機能・料金'))+' | ToolFavor</title>',h)
            h=re.sub(r'(<meta name="description" content=")[^"]*',lambda m:m[1]+('ToolFavorへのお問い合わせ、掲載情報の修正、お仕事や共同制作のご相談。' if path=='contact.html' else '便利なツールとWebサイトを日本語で紹介。機能や料金、公式リンクを確認できます。'),h)
        # Only rewrite routes that actually have a Japanese equivalent.
        for target in LINK_TARGETS:
            if target=='index.html':
                h=h.replace('href="/"','href="/ja/"')
            else:
                h=h.replace('href="'+english_url(target)+'"','href="'+local_url(target)+'"')
        h=h.replace('href="/creators/colddcc.html"','href="/ja/creators/1/"')
        h=switch(seo(h,path,True),path,True)
        dest=ROOT/'ja'/path; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(h)
        # Alternate links and language navigation are also visible from English.
        # Strip previously injected styles so repeated builds stay deterministic.
        en=re.sub(r'<style>\.locale-switch\{.*?</style>','',en,flags=re.S)
        p.write_text(switch(seo(en,path,False),path,False))
    sitemap=ROOT/'sitemap.xml'; xml=sitemap.read_text()
    for path in PAGES:
        url='https://toolfavor.com'+local_url(path)
        if '<loc>'+url+'</loc>' not in xml:
            xml=xml.replace('</urlset>','<url><loc>'+url+'</loc></url>\n</urlset>')
    sitemap.write_text(xml)
    print(f'Generated {len(PAGES)} Japanese pages and {len(catalog)} translated catalog entries.')

if __name__=='__main__':
    build()
    if (ROOT/'zh-cn/index.html').exists():
        import runpy
        runpy.run_path(str(Path(__file__).with_name('build-zh.py')))['refresh_navigation']()
