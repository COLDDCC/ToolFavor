"""Build Simplified Chinese pages. English remains the source catalog."""
from pathlib import Path
import importlib.util, html, json, re

spec=importlib.util.spec_from_file_location('ja_builder',Path(__file__).with_name('build-ja.py'))
ja=importlib.util.module_from_spec(spec);spec.loader.exec_module(ja)
ROOT=ja.ROOT
UI={
'Explore':'发现工具','For Developers':'开发者','For developers':'开发者','Contact / Feedback':'联系与反馈',
'Creator portfolio · EN / 中文 / 日本語':'创作者作品集','About':'关于收录','+ Submit a site':'＋ 提交网站',
'A curated corner of the internet':'发现值得收藏的网站','Independent picks':'独立精选','Discover The Best':'发现好用的','Websites & Tools':'网站与工具',
'Useful tools, remarkable websites, and creative inspiration. Find what you need without the endless scrolling.':'从AI、设计、开发到日常效率工具，按用途和价格筛选，快速找到需要的网站。',
'Search →':'搜索 →','Explore the collection':'浏览精选网站','All pricing':'全部价格','Free':'免费','Freemium':'有免费方案','Paid':'付费',
'Websites & tools':'网站与工具','Tools only':'只看工具','Websites only':'只看网站','Featured':'推荐排序','Name A–Z':'名称 A–Z','Show more websites':'加载更多网站',
'No matching results. Try clearing a filter or searching again.':'没有匹配结果，试试更换关键词或清除筛选条件。',
'Curated starter collection. Pricing and availability may change; verify details with each website.':'价格与服务可用性可能变化，使用前请查看各网站的最新说明。',
'Built something useful?':'做了一个好用的网站？','Share your tool, creative website, or developer project. Submissions are free.':'欢迎提交你的工具、创意网站或开发项目，基础收录申请免费。','Submit your website →':'提交你的网站 →',
'Independent discovery directory · No sponsored rankings':'独立精选导航 · 无付费排名','Submit a website':'提交网站',
'Submit your site for review through GitHub. This opens a public GitHub issue form for review. A GitHub account is required.':'通过GitHub公开表单提交收录申请，需要GitHub账号。表单内容将公开。',
'Website name':'网站名称','Website URL':'网站地址','Type':'类型','Tool':'工具','Website':'网站','Short description':'简短介绍','Cancel':'取消','Submit via GitHub →':'通过GitHub提交 →',
'Free AI Video Generators — 2026 Comparison':'免费AI视频生成工具对比【英文】','Compare 9 tools, free credits, watermarks and official links.':'比较9款工具的免费额度、水印和官网入口。','Explore guide →':'阅读英文指南 →',
'DeepSwapper vs DeepSwapFace — Which Is Free?':'DeepSwapper与DeepSwapFace，哪个能免费用？【英文】','Compare photo swaps, video subscriptions, daily limits and privacy claims.':'对比图片换脸、视频订阅、每日限制和隐私说明。','Read comparison →':'查看英文对比 →',
'Free AI Logo Generators — PNG, SVG & No-Signup Filters':'免费AI Logo工具：PNG、SVG与免注册筛选【英文】','Find out what you can actually download for free.':'看看哪些格式和功能真正支持免费下载。','Compare tools →':'查看英文对比 →',
'Explore tools':'工具列表','Design · Web tool':'设计 · 在线工具','Productivity · Web tool':'效率 · 在线工具','Design':'设计','Productivity':'效率','Web tool':'在线工具','Web Tool':'在线工具',
'Visit official website ↗':'访问官网 ↗','Browse more tools':'浏览更多工具','What you can do':'你可以做什么','About this listing':'关于这条收录','At a glance':'基本信息','Category':'分类','Pricing model':'价格模式',
'ToolFavor helps you discover independent websites and useful tools. This page is an editorial introduction, not a review or endorsement.':'ToolFavor介绍独立网站与实用工具。本页整理产品的基本用途，不代表测评或认证。',
'Features, pricing and availability can change. Check the official website for current details.':'功能、价格与可用性可能变化，请以官网最新信息为准。',
'Edit photos and layered graphics directly in a browser.':'直接在浏览器中编辑照片和带图层的图片。','Edit images in the browser':'在浏览器中编辑图片','Work with layered graphics':'处理带图层的设计文件','Export designs in common image formats':'导出常用格式的图片',
'Create printable graph paper and custom grids for study, planning, and design.':'按需生成适合学习、规划和设计的可打印方格纸。','Configure a grid to match your project':'按用途设置网格','Generate printable paper layouts':'生成适合打印的用纸版式','Download and print your result':'下载并打印结果',
'Convert hourly wages into estimated earnings across common pay periods.':'根据时薪和工作时间，估算不同周期的收入。','Compare hourly and salary figures':'换算和比较时薪与薪资','Explore different work schedules':'比较不同工作时长','Estimate income before making decisions':'提前试算收入',
'Meet the creator':'认识创作者','Explore more projects featured in the founding creator portfolio.':'在创始人的作品集中查看其他公开项目。','COLDDCC’s projects →':'查看COLDDCC的作品 →','© ToolFavor · Independent discovery directory':'© ToolFavor · 独立网站与工具导航',
'Your work deserves to be':'让你的作品被','discovered.':'需要它的人发现。','ToolFavor brings together useful tools, inspiring websites, and the people who build them. Submit a project to our curated directory.':'ToolFavor介绍实用工具、创意网站和背后的开发者。欢迎将你的项目提交到精选目录。',
'Free listings':'基础收录免费','Share your tool or creative website for editorial review. We do not charge for standard submissions.':'提交工具或创意网站，由编辑审核。常规收录申请不收费。','Curated discovery':'按用途发现作品','Help people find your work by category, task, and pricing model. Inclusion is subject to review.':'用户可以按分类、任务和价格找到你的作品，收录需通过审核。',
'Developer profiles':'开发者主页','Planned: a free portfolio connecting your tools and websites under one public profile.':'计划提供免费的作品集功能，将你的工具和网站汇总到一个公开主页。','Coming later — not yet available.':'面向公众的功能尚在准备中。',
'Permanent creator IDs':'永久创作者编号','Planned: a unique, permanent numeric ID paired with your username, issued by our future account database.':'计划为账号分配永久数字编号，与用户名一起使用。','No IDs are being issued yet.':'暂未开放公众编号申请。','See a creator portfolio':'查看作品集示例','Preview how projects from an existing personal website can live together on ToolFavor.':'看看多个网站项目如何汇总在同一个ToolFavor主页中。','Explore COLDDCC’s portfolio →':'查看COLDDCC的作品集 →',
'How submission works':'如何提交收录','Open the GitHub form, provide your website URL and a clear description, then submit it for review. Submission does not guarantee publication. Never submit passwords or private information.':'打开GitHub表单，填写网站地址与清晰的介绍，提交审核。申请不保证收录，请勿填写密码或私人信息。','Contact / Feedback →':'联系与反馈 →','← Back to directory':'← 返回网站目录',
'Creator portfolio (EN)':'作品集（英文）','个人作品集（中文）':'作品集（中文）','制作実績（日本語）':'作品集（日文）','Creator portfolio →':'创作者作品集 →',
'Contact · Feedback':'联系与反馈','Have an idea or a correction?':'有建议，或发现了需要修改的地方？','Report a broken link, suggest a better description, ask about collaboration, or get in touch about work opportunities.':'欢迎反馈失效链接、修改工具介绍，或联系合作与工作机会。','Write to ToolFavor':'联系ToolFavor',
'This form opens your email app with a prepared message. It does not send data to our server. Please avoid including sensitive information.':'填写后会打开邮件应用，带入你准备的内容，不会直接发送到网站服务器。请勿填写敏感信息。','What is this about?':'咨询类型','Website feedback':'网站反馈','Incorrect tool information':'工具信息有误','Collaboration':'合作咨询','Hiring / portfolio inquiry':'招聘或作品集咨询','Other':'其他','Your name (optional)':'你的称呼（选填）','Message':'留言内容','Open email app →':'打开邮件应用 →','No email app configured? Write directly to':'没有配置邮件应用？可直接写信至','Home':'首页',
'Printable':'打印','Images':'图片','Utility':'实用工具','Team Builder':'队伍搭配','Calculator':'计算器','Music':'音乐','Educational':'学习','Company project':'工作项目','Healthcare':'医疗健康','Multilingual':'多语言','Anime':'动漫','Information architecture':'信息架构','Operations':'运营','Browser extension':'浏览器扩展','View project ↗':'查看项目 ↗','View source ↗':'查看源码 ↗','Visit website ↗':'访问网站 ↗','Contact / Feedback ↗':'联系与反馈 ↗',
'This is a curated portfolio, not a verified employment record. Company-associated work is labeled separately. Project links do not guarantee current availability; roles and contributions can be clarified on request.':'这里展示公开制作项目，工作相关项目已单独标注。网站公开状态可能变化，合作项目中的职责可进一步沟通。','© ToolFavor · Discover The Best Websites & Tools':'© ToolFavor · 发现好用的网站与工具',
}
CATS={'All':'全部','AI':'AI','AI Images':'AI生图','AI Video':'AI视频','Design':'设计','Developer':'开发','Productivity':'效率','Inspiration':'灵感','Learning':'学习','Video & Audio':'视频与音频','Marketing':'营销','Discovery':'工具导航'}

def refresh_navigation():
    locales=[('en','English',''),('ja','日本語','ja'),('zh-CN','简体中文','zh-cn')]
    for path in ja.PAGES:
        en=ja.english_url(path)
        urls={code:(en if not folder else '/'+folder+en) for code,label,folder in locales}
        tags='<!-- locale-links -->'+''.join(f'<link rel="alternate" hreflang="{code}" href="https://toolfavor.com{url}">' for code,url in urls.items())+f'<link rel="alternate" hreflang="x-default" href="https://toolfavor.com{en}"><!-- /locale-links -->'
        for code,label,folder in locales:
            p=ROOT/folder/path if folder else ROOT/path
            if not p.exists():continue
            h=p.read_text();h=re.sub(r'<!-- locale-links -->.*?<!-- /locale-links -->',tags,h,flags=re.S)
            links=[]
            for c,l,f in locales:
                url=urls[c]+('?lang=en' if c=='en' and path=='creators/1/index.html' else '')
                links.append(f'<a href="{url}" lang="{c}"'+(' aria-current="page"' if c==code else '')+'>'+l+'</a>')
            nav='<!-- language-nav --><nav aria-label="Language" class="locale-switch">'+''.join(links)+'</nav><!-- /language-nav -->'
            h=re.sub(r'<!-- language-nav -->.*?<!-- /language-nav -->',lambda m:nav,h,flags=re.S)
            h=h.replace('html[lang=ja]',':is(html[lang=ja],html[lang=zh-CN])') if ':is(html[lang=ja]' not in h else h
            p.write_text(h)

def build():
    descriptions=(ROOT/'scripts/zh-cn-descriptions.txt').read_text().splitlines()
    catalog=json.JSONDecoder().raw_decode((ROOT/'index.html').read_text().split('const data=',1)[1])[0]
    assert len(catalog)==len(descriptions),(len(catalog),len(descriptions))
    ja.UI=UI
    for path in ja.PAGES:
        h=(ROOT/path).read_text()
        h=re.sub(r'<style>(?:\.locale-switch|:is\().*?</style>','',h,flags=re.S)
        h=ja.translate_markup(h)
        for a,b in {'ツールやWebサイトを検索':'搜索工具与网站','ツール名・用途・キーワードで検索…':'搜索网站、工具或你想完成的任务…','料金':'价格','種類':'类型','並び順':'排序'}.items():
            h=h.replace('"'+a+'"','"'+b+'"')
        if path=='index.html':
            start=h.index('const data=')+len('const data=');old,length=json.JSONDecoder().raw_decode(h[start:])
            data=[[*x[:2],d,*x[3:],x[2]] for x,d in zip(old,descriptions)]
            h=h[:start]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+h[start+length:]
            h=h.replace('const cats=','const labels='+json.dumps(CATS,ensure_ascii=False)+';const cats=').replace('b.textContent=c;','b.textContent=labels[c]||c;')
            h=h.replace('[x[0],x[1],x[2],x[3]]','[x[0],x[1],x[2],x[3],x[7],labels[x[3]]]')
            h=h.replace("'/tools/'+detail+'.html'","'/zh-cn/tools/'+detail+'.html'")
            h=h.replace("[x[3],x[5]==='freemium'?'Freemium':x[5]==='free'?'Free':'Paid']","[labels[x[3]]||x[3],x[5]==='freemium'?'有免费方案':x[5]==='free'?'免费':'付费']")
            h=h.replace("detail?'Details →':'Visit ↗'","detail?'查看详情 →':'访问网站 ↗'")
            h=h.replace("detail?'View details for '+x[0]:'Visit '+x[0]+' (opens in new tab)'","detail?'查看'+x[0]+'详情':'访问'+x[0]+'（新标签页）'")
            h=h.replace("rows.length+' curated results · Showing '+Math.min(visibleLimit,rows.length)","'共 '+rows.length+' 个结果 · 已显示 '+Math.min(visibleLimit,rows.length)+' 个'")
            h=h.replace('Redirecting to the public GitHub submission form. A GitHub account is required.','即将打开GitHub公开收录表单，需要GitHub账号。')
        elif path=='creators/1/index.html':
            messages=json.JSONDecoder().raw_decode(h.split('const messages=',1)[1])[0]
            desc=json.JSONDecoder().raw_decode(h.split('const projectDescriptions=',1)[1])[0]
            h=re.sub(r'(<[a-z0-9]+\b[^>]*data-i18n="([^"]+)"[^>]*>)(.*?)(</[a-z0-9]+>)',lambda m:m[1]+html.escape(messages['zh'].get(m[2],m[3]))+m[4],h,flags=re.S)
            h=re.sub(r'(<p data-project-desc="(\d+)">).*?(</p>)',lambda m:m[1]+html.escape(desc['zh'][int(m[2])])+m[3],h)
            h=re.sub(r'<div class="langbar"[^>]*>.*?</div>','',h,flags=re.S)
            h=h.replace('let initial=new URLSearchParams(location.search).get("lang");','let initial="zh";')
            extra={'About me · 个人简介':'个人简介','✎ 修改简介':'✎ 修改简介','Edit profile details':'修改个人资料','Personal edits are stored in this browser only.':'修改仅保存在当前浏览器中。','Independent developer · Portfolio':'独立开发者 · 作品集','Featured creator':'精选创作者','Original portfolio source ↗':'原作品集源码 ↗','Permanent ID':'永久编号','Creative Website':'创意网站','Travel':'旅行','SEO Content':'SEO内容','Gaming':'游戏','Research':'资料研究','Professional headline':'职业定位','Education / background':'教育与经历','Core skills':'核心技能','Work preference / collaboration':'工作偏好与合作','About me':'个人简介','Save in this browser':'保存到当前浏览器','Saved locally · not published to other visitors.':'已在当前浏览器保存，其他访客不会看到这些修改。','Preview updated; browser storage unavailable.':'已更新预览，但浏览器存储不可用。','Display name (up to 40 characters)':'展示名称（最多40个字符）'}
            for a,b in sorted(extra.items(),key=lambda kv:-len(kv[0])):h=h.replace(a,b)
            h=h.replace('cancel.textContent="Cancel"','cancel.textContent="取消"')
        titles={'index.html':'发现好用的网站与AI工具 | ToolFavor','creators/1/index.html':'COLDDCC作品集：网站开发、SEO与AI应用 | ToolFavor','developers.html':'开发者：网站收录与作品集 | ToolFavor','contact.html':'联系与反馈 | ToolFavor'}
        title=titles.get(path,Path(path).stem+'：功能、价格与官网 | ToolFavor')
        h=re.sub(r'<title>.*?</title>','<title>'+title+'</title>',h)
        description='发现AI生图、AI视频、设计、开发与效率工具，按用途和价格筛选，快速找到需要的网站。' if path=='index.html' else '了解ToolFavor收录的实用工具与独立创作项目，查看功能介绍、官网链接和创作者信息。'
        h=re.sub(r'(<meta name="description" content=")[^"]*',lambda m:m[1]+description,h)
        for target in ja.PAGES:
            en=ja.english_url(target);h=h.replace('href="'+en+'"','href="/zh-cn'+en+'"')
        h=h.replace('href="/creators/colddcc.html"','href="/zh-cn/creators/1/"')
        h=h.replace('<html lang="en">','<html lang="zh-CN">')
        h=re.sub(r'<link rel="canonical"[^>]*>',f'<link rel="canonical" href="https://toolfavor.com/zh-cn{ja.english_url(path)}">',h)
        # Shared styling and marker blocks are supplied by the Japanese builder.
        h=ja.switch(h,path,True)
        dest=ROOT/'zh-cn'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(h)
    refresh_navigation()
    sitemap=ROOT/'sitemap.xml';s=sitemap.read_text()
    for path in ja.PAGES:
        u='https://toolfavor.com/zh-cn'+ja.english_url(path)
        if '<loc>'+u+'</loc>' not in s:s=s.replace('</urlset>',f'<url><loc>{u}</loc></url>\n</urlset>')
    sitemap.write_text(s)
    print(f'Generated {len(ja.PAGES)} Simplified Chinese pages and {len(catalog)} catalog descriptions.')

if __name__=='__main__':build()
