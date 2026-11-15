from pathlib import Path
from html import escape
import re
import json
import base64
from update_photo_sections import sync_photo_sections

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / 'orlando_trip_cn_2026-12-04_12-12.md'
OUT = ROOT / 'orlando_mobile_trip_cn.html'
sync_photo_sections()
photos = json.loads((ROOT / 'data/project_photos.json').read_text())
source = MD.read_text()
css = (ROOT / 'tools/base_theme.css').read_text()

counter = 0

def inline(s):
    s = escape(s, quote=False)
    s = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', lambda m: f'<a href="{escape(m[2], quote=True)}" target="_blank" rel="noopener noreferrer">{m[1]}</a>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s

def render(md):
    global counter
    lines = md.strip().splitlines(); result = []; i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line: i += 1; continue
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s:|\-]+\|$', lines[i+1].strip()):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append([x.strip() for x in lines[i].strip().strip('|').split('|')]); i += 1
            heads = rows[0]
            cells = lambda row, tag: ''.join(f'<{tag}'+(' scope="col"' if tag=='th' else '')+f'>{inline(c)}</{tag}>' for c in row)
            result.append('<div class="table-scroll" tabindex="0" role="region" aria-label="行程详情表，可左右滑动"><table><thead><tr>'+cells(heads,'th')+'</tr></thead><tbody>'+''.join('<tr>'+cells(r,'td')+'</tr>' for r in rows[2:])+'</tbody></table></div>')
            continue
        if re.match(r'^#{1,6} ', line):
            text = re.sub(r'^#+ ', '', line); result.append('<h3>'+inline(text)+'</h3>'); i += 1; continue
        if line.startswith('- ') or re.match(r'^\d+\. ', line):
            ordered = bool(re.match(r'^\d+\. ', line)); tag='ol' if ordered else 'ul'; items=[]
            while i<len(lines):
                current=lines[i].strip()
                matched=re.match(r'^\d+\. (.*)',current) if ordered else re.match(r'^- (.*)',current)
                if not matched: break
                text=matched[1]
                if re.match(r'^\[[ xX]\] ',text):
                    counter += 1; checked=' checked' if text[1].lower()=='x' else ''
                    items.append(f'<li class="check-item"><label><input type="checkbox" data-check="trip-{counter}"{checked}><span>{inline(text[4:])}</span></label></li>')
                else: items.append('<li>'+inline(text)+'</li>')
                i+=1
            result.append(f'<{tag}>'+''.join(items)+f'</{tag}>'); continue
        if line.startswith('>'):
            q=[]
            while i<len(lines) and lines[i].strip().startswith('>'):
                q.append(lines[i].strip().lstrip('>').strip()); i+=1
            result.append('<blockquote>'+inline(' '.join(q))+'</blockquote>'); continue
        if line=='---': result.append('<hr>'); i+=1; continue
        para=[]
        while i<len(lines) and lines[i].strip():
            if para and (lines[i].strip().startswith(('|','#','- ','>')) or re.match(r'^\d+\. ',lines[i].strip())): break
            para.append(lines[i].strip()); i+=1
        result.append('<p>'+inline(' '.join(para))+'</p>')
    return '\n'.join(result)

def cut(start,end=None):
    a=source.index(start)+len(start)
    return source[a:source.index(end,a) if end else len(source)].strip()

def card(title,md,badge=''):
    return f'<article class="card prose"><div class="card-title"><h3>{escape(title)}</h3>'+ (f'<span class="badge pending">{escape(badge)}</span>' if badge else '')+'</div>'+render(md)+'</article>'

def banner(title,desc):
    return f'<div class="view-banner"><div><h2>{escape(title)}</h2><p>{escape(desc)}</p></div><span class="badge flex">12/4—12/12 · EST</span></div>'

matches=list(re.finditer(r'^### (12/(\d+) (周.))｜([^\n]+)$',source,re.M))
days=[]
shorts=['抵达 · 入住','冒险岛','Studios＋冒险岛','Epic Universe','EPCOT','Silver Springs','清泉＋Mount Dora','海滩或湖畔','MCO 返程']
for idx,m in enumerate(matches):
    body=source[m.end():matches[idx+1].start() if idx+1<len(matches) else source.index('## 5. 交通和租车')]
    for marker in ['### 环球三天怎么玩','### 周三到周五详细版']:
        if marker in body: body=body[:body.index(marker)]
    days.append(dict(day=int(m[2]),label=m[1],title=m[4],body=body.strip(),short=shorts[idx],id=f'day-12-{m[2]}'))
assert len(days)==9
universal='### 环球三天怎么玩'+cut('### 环球三天怎么玩','### 12/5 周六｜')
tickets=cut('### 环球 3 日票','### 三人票价与购票方案')
pricing=cut('### 三人票价与购票方案｜2026/11/15 查询','### 当日排队与官方 App')
queue_links=cut('### 当日排队与官方 App｜旅行当天点这里','## 4. 每日详细安排')
checks=cut('## 7. 预约与临近复核清单','## 8. 天气与体力的临场取舍')
transport=cut('## 5. 交通和租车：只租后半段','## 6. 餐饮节奏：围绕当天主线')
packing=cut('## 9. 简洁打包单','## 10. 常用入口')
links=cut('## 10. 常用入口').split('\n---')[0]
weather=cut('## 8. 天气与体力的临场取舍','## 9. 简洁打包单')
info=cut('## 1. 已确认与待落地','## 2. 一眼看懂每天安排')
lodging=cut('### 暂定住宿｜Reunion Resort 一楼公寓','## 2. 一眼看懂每天安排').split('“The Ringring”')[0]

def picker(kind):
    return '<div class="day-picker" aria-label="选择日期">'+''.join(f'<button class="day-pill" type="button" data-{kind}-target="{d["id"]}" aria-pressed="false"><span>12/{d["day"]} {d["label"].split()[-1]}</span><strong>{d["short"]}</strong></button>' for d in days)+'</div>'

summarynotes=['晚上入住，先睡好','海格、迅猛龙、绿巨人','主路线需 Park-to-Park','五个核心 ride＋两场表演','料理鼠王＋银河护卫队；烟花提前找位','取车后短线划水，午餐可去 Ocala','上游 Emerald Cut；湖边午餐可选','Sarasota 长途／Winter Park 恢复日','18:30 MCO 国内航班']
overview=''.join(f'<a class="overview-row" href="#{d["id"]}"><span class="time-chip">12/{d["day"]} {d["label"].split()[-1]}</span><span><strong>{d["short"]}</strong><small>{summarynotes[i]}</small></span><span aria-hidden="true">↗</span></a>' for i,d in enumerate(days))
quick=[('跨园票','12/6 两个园','Express 不提供跨园权限，需 Park-to-Park。'),('Epic','12/7 完整一天','两场表演先选场次；不要只顾着排项目。'),('烟花','12/8 提前找位','T−75 分钟选位，T−60 分钟基本定点。'),('取车','12/9 上午','Silver Springs 船班目标 11:30，衔接取车。'),('返程','12/12 18:30','MCO 国内航班；目标约 15:00 到机场还车。')]
quickhtml=''.join(f'<div class="quick-row"><span class="time-chip">{a}</span><div><strong>{b}</strong><br><span class="muted">{c}</span></div></div>' for a,b,c in quick)
foodnotes=[
'晚上抵达后就在民宿附近叫餐，补好第二天早餐、水与零食；不为了餐厅绕远路。',
'**午餐：Three Broomsticks 三把扫帚**，Hogsmeade 里坐下吃英式简餐，至少休息 45 分钟。晚餐园内或回民宿解决。\n\n[官方餐厅与菜单](https://www.universalorlando.com/web/en/us/things-to-do/dining/three-broomsticks)',
'**午餐：Leaky Cauldron 破釜酒吧**，在对角巷吃热餐。与 Bourne 场次衔接时留步行时间；晚上早点回民宿。\n\n[官方餐厅与菜单](https://www.universalorlando.com/web/en/us/things-to-do/dining/leaky-cauldron)',
'**午餐：Mead Hall**，放在伯克岛 ride 与表演之间，坐下 45–60 分钟。肉类、鱼类、三明治按当日菜单选；晚上在所在区域简单吃，不跨园赶正式晚餐。\n\n[Mead Hall 官方介绍](https://www.universalorlando.com/web/en/us/things-to-do/dining/mead-hall)',
cut('#### 当天餐饮与拍照', '#### 时间不足时按这个顺序删'),
'**首选：Ivy on the Square**，53 S Magnolia Ave, Ocala；计划 14:30 午餐，出发前核对周三接单时间。炸鸡、鱼类或汉堡按当天菜单选，预算 $25–40／人。\n\n**省事备选：园内 Springside Café**，官网列 10:30–18:30，三明治／汉堡／沙拉，预算 $15–25／人；吃完可早点返程。\n\n预算未含税、小费与酒水。\n\n[Ivy 官网](https://ivyonthesquareocala.com/) · [Ivy 导航](https://www.google.com/maps/search/?api=1&query=Ivy+on+the+Square+Ocala) · [园区 Café](https://silversprings.com/plan-your-day/dining-options/)',
'**午餐：Pisces Rising**，239 W 4th Ave, Mount Dora；目标约 13:30。周四午餐 11:30–15:00；可选 crab cakes／coconut shrimp 分享，主食按当天菜单选。预算 $25–40／人，未含税、小费与酒水。\n\n**晚餐可选：Columbia Celebration**，仅民宿靠迪士尼／Celebration 且不累时考虑；周五会吃同品牌的话今晚不重复。\n\n[Pisces 菜单](https://www.piscesrisingdining.com/menu/) · [营业时段](https://www.piscesrisingdining.com/about/) · [导航](https://www.google.com/maps/search/?api=1&query=Pisces+Rising+Mount+Dora) · [Columbia Celebration](https://www.columbiarestaurant.com/celebration)',
'**Sarasota 版：Columbia，St. Armands Circle 店**，411 St. Armands Cir；目标约 13:45–14:00。周五 11:00–22:00；Cuban Sandwich、1905 Salad、Half and Half Combo 按食量搭配，预算 $25–40／人。\n\n**Winter Park 版：Briarpatch 或 Prato 二选一。** Briarpatch 适合松饼／法式吐司＋咸口早餐，周五 07:30–16:00；Prato 意大利午餐 11:00–16:00。预算约 $25–45／人。以上预算未含税、小费与酒水。\n\n[Columbia Sarasota](https://www.columbiarestaurant.com/st-armands-circle-sarasota) · [Briarpatch 菜单](https://thebriarpatchrestaurant.com/food-and-drink/brunch) · [Prato 菜单与预订](https://www.pratoitalian.com/winter-park/)',
'**民宿附近早午餐。** 不去远处追餐厅，按退房和还车时间安排；目标约 15:00 到机场还车。'
]
foodhtml=''.join(f'<article class="card food-detail prose" id="food-{d["id"]}" data-food-id="{d["id"]}" hidden><div class="card-title"><h3>{d["label"]} · 吃什么</h3><span class="badge flex">{d["short"]}</span></div>{render(foodnotes[i])}<p><a class="button" href="#{d["id"]}">查看当天完整路线 ↗</a></p></article>' for i,d in enumerate(days))
def photo_gallery(day):
    items = [p for p in photos if p['day'] == day]
    if not items:
        return ''
    figures = []
    for number, p in enumerate(items, 1):
        image = 'data:image/jpeg;base64,' + base64.b64encode((ROOT / p['local_path']).read_bytes()).decode()
        license_note = f'<span class="photo-credit"><a href="{p["license_url"]}" target="_blank" rel="noopener noreferrer">{p["license"]}</a> · {p["changes"]}</span>' if p.get('license') else ''
        figures.append(f'<figure class="project-photo"><button type="button" class="photo-zoom" aria-label="放大：{escape(p["title"], quote=True)}"><img src="{image}" alt="{escape(p["alt"], quote=True)}" loading="lazy" decoding="async" width="800" height="600"></button><figcaption><span class="photo-order">{number:02}</span><strong>{escape(p["title"])}</strong><span class="photo-tag">{escape(p["tag"])}</span><a class="photo-credit" href="{escape(p["source_url"], quote=True)}" target="_blank" rel="noopener noreferrer">图片来源：{escape(p["credit"])}</a>{license_note}</figcaption></figure>')
    return f'<aside class="day-photos" aria-label="12/{day} 项目图片"><h3>今天会看到什么 <span>{len(items)} 张</span></h3><p class="photo-note">点击放大 · 可选项目按体力取舍</p><div class="photo-grid">'+''.join(figures)+'</div></aside>'

def daily_card(d):
    body = re.sub(r'<!-- project-photos:start -->.*?<!-- project-photos:end -->', '', d['body'], flags=re.S)
    return f'<article class="day-card day-detail" id="{d["id"]}" data-day-id="{d["id"]}" hidden><div class="date-box"><div class="month">DEC 2026</div><div class="daynum">{d["day"]:02}</div><div class="weekday">{d["label"].split()[-1]}</div></div><div class="day-content prose"><h2>{escape(d["title"])}</h2><div class="day-layout"><div class="day-copy">{render(body)}</div>{photo_gallery(d["day"])}</div></div></article>'

dayhtml=''.join(daily_card(d) for d in days)

extra=r'''
:root{--muted:#56636a;--shadow:0 3px 8px rgba(54,44,28,.025),0 16px 36px rgba(54,44,28,.06)}
body{font-size:16px;line-height:1.65} .hero{position:relative;isolation:isolate;min-height:285px;background:#123f3c;overflow:hidden}.hero-inner{position:relative;z-index:1;padding-bottom:38px}.hero h1{font-size:clamp(42px,7vw,72px);line-height:1.08;letter-spacing:-.035em}.hero p{max-width:600px}.hero-art{position:absolute;inset:auto 0 0 auto;width:54%;height:100%;opacity:.38;z-index:0}.app-shell{padding-bottom:50px}.top-grid{margin-top:0}.home-stack{gap:18px}.nav-strip{margin-top:0;padding-top:12px}.nav-strip a{min-height:44px;display:flex;align-items:center}.view-banner{margin-bottom:16px}.panel{min-width:0}.overview-row{display:grid;grid-template-columns:112px 1fr 16px;gap:16px;align-items:center;padding:15px 4px;border-top:1px solid var(--line);color:var(--ink);font-weight:400}.overview-row:first-child{border-top:0}.overview-row:hover{text-decoration:none;background:#f4f2e8}.overview-row small{display:block;color:var(--muted);font-size:13px;margin-top:3px}.overview-row strong{font-size:16px}.overview-row .time-chip{font-size:12px}.stats{margin:20px 0}.stat strong{font-variant-numeric:tabular-nums}.day-picker{grid-template-columns:repeat(5,minmax(0,1fr));margin:18px 0}.day-pill{min-height:80px}.day-detail{margin-top:20px;min-width:0}.day-content{min-width:0}.day-content>h2{font-size:25px;line-height:1.35;margin:0 0 16px}.prose{overflow-wrap:anywhere}.prose p{color:var(--ink);margin:0 0 16px;font-size:15px;line-height:1.85}.prose h3{font-size:18px;line-height:1.5;margin:30px 0 13px;padding-top:16px;border-top:1px solid var(--line)}.prose .card-title h3{margin:0;padding:0;border:0}.prose ul,.prose ol{padding-left:22px;margin:0 0 20px;font-size:15px}.prose li{margin:9px 0}.prose a{text-decoration:underline;text-underline-offset:3px}.prose .button{text-decoration:none;min-height:44px}.table-scroll{width:100%;max-width:100%;overflow-x:auto;margin:18px 0 24px;border:1px solid var(--line);border-radius:12px;overscroll-behavior-x:contain}.table-scroll table{width:100%;border-collapse:collapse;font-size:14px;line-height:1.75}.table-scroll th,.table-scroll td{padding:12px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line);border-right:1px solid rgba(202,188,170,.3);min-width:100px}.table-scroll th{background:#eceee3;color:var(--teal-dark);font-size:13px}.table-scroll tr:last-child td{border-bottom:0}.table-scroll td:first-child{font-weight:650;min-width:100px}.table-scroll tr:nth-child(even) td{background:rgba(245,241,232,.5)}.check-item{list-style:none;margin-left:-20px!important}.check-item label{display:flex;gap:12px;align-items:flex-start;padding:8px 0;cursor:pointer;min-height:44px}.check-item input{width:20px;height:20px;flex:0 0 20px;margin-top:4px;accent-color:var(--teal)}.check-item input:checked+span{text-decoration:line-through;color:var(--muted)}blockquote{background:#edf1e7;border-left:3px solid var(--teal);margin:18px 0;padding:16px}button,a,input{touch-action:manipulation}button:active{transform:translateY(1px)}a:focus-visible,button:focus-visible,input:focus-visible,.table-scroll:focus-visible{outline:3px solid #ae562f;outline-offset:4px}.skip-link{position:absolute;left:16px;top:-100px;padding:12px;background:#fff;z-index:100}.skip-link:focus{top:8px}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:12px 0}.toolbar button{min-height:44px;padding:8px 14px;background:var(--paper);color:var(--ink);border:1px solid var(--line-strong);border-radius:9px;font:inherit;cursor:pointer}.toolbar span{font-size:13px;color:var(--muted)}.decision-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.decision-grid .card{margin:0}.intro-note{font-size:14px;color:var(--muted);margin:12px 0}.badge{white-space:normal;text-align:center}.footer{padding:20px 4px;line-height:1.8}.hero .eyebrow{font-size:12px}.prose hr{border:0;border-top:1px solid var(--line);margin:24px 0}[hidden]{display:none!important}
@media(max-width:720px){.top-grid{grid-template-columns:1fr}.decision-grid{grid-template-columns:1fr}.hero-art{width:100%;opacity:.22}.hero-inner{padding:30px 18px}.hero{min-height:250px}.hero p{font-size:15px}.day-picker{grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.day-pill{padding:10px 9px;min-height:78px}.day-pill strong{font-size:13px;-webkit-line-clamp:3}.day-pill span{font-size:11px}.day-card{display:block;padding:16px}.date-box{display:flex;gap:10px;align-items:center;width:max-content;text-align:left;margin-bottom:16px;padding:8px 12px}.date-box .daynum{font-size:22px;margin:0}.day-content>h2{font-size:23px}.table-scroll table{min-width:530px}.table-scroll th,.table-scroll td{padding:10px 12px}.app-shell{padding:12px}.stats{gap:6px}.stat{min-height:74px;padding:9px}.stat strong{font-size:23px}.overview-row{grid-template-columns:93px 1fr 13px;gap:10px}.overview-row strong{font-size:15px}.prose p{font-size:15px}.card,.panel{padding:16px}.toolbar{flex-wrap:wrap}.view-banner h2{font-size:23px}.prose h3{font-size:17px}.nav-strip{gap:6px}.nav-strip a{padding:9px 14px;font-size:14px}.table-hint{display:block}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media print{.hero{min-height:0;background:#fff;color:#000;box-shadow:none}.hero p,.hero .eyebrow{color:#333}.hero-art,.nav-strip,.day-picker,.toolbar,.skip-link{display:none!important}.app-view[hidden],.day-detail[hidden],.food-detail[hidden]{display:block!important}.app-view{min-height:0}.date-box{background:#eee;color:#000}.card,.panel,.day-card{box-shadow:none;break-inside:auto}.table-scroll{overflow:visible}.table-scroll table{min-width:0}.day-card{break-before:page}.app-shell{max-width:none}.hero-inner{padding:12px 0}.prose a{color:#222}body{background:#fff}.table-scroll tr{break-inside:avoid}}
'''
extra += '\n' + (ROOT / 'tools/mickey_theme.css').read_text()
extra += '\n' + (ROOT / 'tools/project_photos.css').read_text()

hero='''<svg class="hero-art" viewBox="0 0 750 320" aria-hidden="true"><circle cx="620" cy="82" r="42" fill="var(--mickey-white)"/><path d="M0 265 Q110 230 220 265 T440 270 T750 252V320H0Z" fill="var(--mickey-red)"/><g fill="none" stroke="var(--mickey-yellow)" stroke-width="3"><path d="M70 240C130 70 250 68 300 223S458 230 510 136S642 83 705 238"/><path d="M82 240C142 82 238 83 288 229S470 245 523 143S633 98 693 240"/><path d="M130 161V252M185 118V253M242 148V253M310 241V263M415 229V260M500 155V251M568 105V254M635 136V253"/></g><g fill="var(--mickey-white)"><path d="M450 256V165H470V128L483 94L496 128V165H520V256Z"/><path d="M405 256V195H425V159L438 135L451 159V256Z"/><path d="M520 256V186H540V151L553 121L566 151V256Z"/><circle cx="358" cy="205" r="40"/></g><g fill="none" stroke="var(--mickey-yellow)" stroke-width="7"><path d="M670 320V206M670 221Q640 185 614 202M670 215Q693 177 724 188M670 222Q705 206 738 222"/></g></svg>'''
nav=[('home','速览'),('timeline','每日'),('bookings','票价·预订'),('food','餐饮'),('transport','交通'),('packing','打包'),('links','链接·排队')]
html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light"><meta name="theme-color" content="#191816"><title>奥兰多旅行计划 · 2026.12.04–12.12</title><style>'''+css+extra+'''</style></head><body><a class="skip-link" href="#content">跳到行程内容</a><header class="hero" id="top">'''+hero+'''<div class="hero-inner"><span class="eyebrow">2026.12.04–12.12 · 3 人 · Orlando & Springs</span><h1>Orlando Trip</h1><p>Epic 留一整天，冒险岛多玩一点。后半程划清泉、看湖景，在海边坐到日落。</p></div></header><main class="app-shell" id="content"><nav class="nav-strip" aria-label="页面导航">'''+''.join(f'<a href="#{a}">{b}</a>' for a,b in nav)+'''</nav><section class="app-view" id="home" data-view="home"><div class="home-stack"><div class="top-grid"><section class="panel"><div class="card-title"><div><h2>行程概览</h2><p>同一间民宿，前四天乐园，后三天看风景。</p></div><span class="badge pending">规划中 · v7</span></div><div class="stats"><div class="stat"><span>同行</span><strong>3 人</strong></div><div class="stat"><span>乐园</span><strong>4 园</strong></div><div class="stat"><span>住宿</span><strong>8 晚</strong></div><div class="stat"><span>租车开始</span><strong>12/9</strong></div></div><div class="route-line"><span>Epic＋Express</span><span>冒险岛优先</span><span>清泉与海边</span></div></section><section class="panel"><div class="card-title"><h2>最容易忘的事</h2></div><div class="quick-list">'''+quickhtml+'''</div></section></div>'''+banner('每天一条主线','点击日期，直接进入当天的路线、餐厅、拍照与取舍。')+'<section class="panel">'+overview+'</section><div class="decision-grid">'+card('环球三天','12/5 海格、迅猛龙、绿巨人。12/6 Studios 精选＋冒险岛补刷，需跨园票。12/7 Epic 五个核心 ride＋两场表演。\n\n[打开 Epic 当天](#day-12-7)')+card('后半程怎么选','Silver Springs 短线，King’s Landing 可与 Mount Dora 组合。周五 Sarasota 是长途日；不想累就 Winter Park。\n\n[看周五两条路线](#day-12-11)')+card('三人购票预算','**环球：$2,708.73 含税**，旧双园跨园两天＋Epic 一天促销票与三日普通 Express。**EPCOT：预算 $731.66–811.53／三人**，门票价已核，LL 是预估。\n\n[看明细、比价与购票链接](#bookings)')+'</div>'+card('暂定住宿 · Reunion Resort','**12/4–12/12，8 晚；三卧两卫，一楼。** 尚未确认预订。环球三天预留更宽的打车时间，12/12 按 10:00 前退房。\n\n[房源、价格记录与入住待办](#bookings)')+'<details class="card prose"><summary>住宿、航班与已确认信息</summary>'+render(info)+'</details><details class="card prose"><summary>天气、体力与恢复优先版</summary>'+render(weather)+'</details></div></section>'
html+='<section class="app-view" id="timeline" data-view="daily" hidden>'+banner('每日行程','每次只展开一天。表格在手机上可左右滑动，官方与导航链接可直接打开。')+picker('day')+'<div class="toolbar"><button type="button" data-step="-1">← 前一天</button><span id="day-position" aria-live="polite"></span><button type="button" data-step="1">后一天 →</button></div><details class="card prose"><summary>环球三日：项目名称、Express 与跨园前提</summary>'+render(universal)+'</details>'+dayhtml+'</section>'
html+='<section class="app-view" id="bookings" data-view="bookings" hidden>'+banner('预订与待办','暂定 Reunion 住宿，尚待确认订单。勾选状态只保存在本浏览器，不代表实际完成预订。')+card('暂定住宿 · Reunion 一楼公寓',lodging,'8 晚 · 尚未确认预订')+card('三人票价 · 怎么买更划算',pricing,'11/15 查询')+card('门票与 Express',tickets,'请核对产品')+card('预约清单',checks)+card('环球 Express 执行说明',universal)+'</section>'
html+='<section class="app-view" id="food" data-view="food" hidden>'+banner('每天吃什么','先看当天首选，备选按体力选。周三到周五含地址、预算、菜单与营业信息。')+picker('food')+foodhtml+'</section>'
html+='<section class="app-view" id="transport" data-view="transport" hidden>'+banner('航班 · 民宿 · 租车','乐园几天打车；周边游再取车。拿到民宿门牌后复核车程。')+card('已确认信息',info)+card('交通执行',transport)+'</section>'
html+='<section class="app-view" id="packing" data-view="packing" hidden>'+banner('打包与出门前检查','12 月注意晚风，水上活动带干衣，乐园轻装。')+card('打包清单',packing)+card('每天离开民宿前','- [ ] 手机、电量和充电宝\n- [ ] 当天门票／Express／预订确认信\n- [ ] 证件、水、零食、薄外套\n- [ ] 今天的目标、午餐和最晚回程时间\n- [ ] 水上日带防水袋、毛巾和干衣\n- [ ] 返程日查航班、还车门店和航站楼')+'</section>'
html+='<section class="app-view" id="links" data-view="links" hidden>'+banner('关键链接','官网用于核对最新规则，导航用于到现场；正文各处也保留了来源。')+card('四园当日排队 · 官方 App',queue_links)+card('景点、购票与导航',links)+card('餐厅与活动','- [Ivy on the Square](https://ivyonthesquareocala.com/)\n- [Silver Springs 餐饮](https://silversprings.com/plan-your-day/dining-options/)\n- [Pisces Rising](https://www.piscesrisingdining.com/)\n- [Columbia Sarasota](https://www.columbiarestaurant.com/st-armands-circle-sarasota)\n- [Briarpatch](https://thebriarpatchrestaurant.com/hours-and-location)\n- [Prato](https://www.pratoitalian.com/winter-park/)\n- [Winter Park Scenic Boat Tour](https://scenicboattours.com/)\n- [环球 Express 产品与覆盖](https://www.universalorlando.com/web/en/us/tickets-packages/express-passes)')+'</section>'
html+='''<footer class="footer">Updated Nov 15, 2026 · 所有时间为佛罗里达当地时间 EST<br>营业时间、演出场次、实时路况与余位需临近复核。规划不代表已预订。<br>页面内容可离线查看；官网与导航链接需要联网。</footer></main><noscript><style>.app-view[hidden],.day-detail[hidden],.food-detail[hidden]{display:block!important}.day-picker,.toolbar{display:none}</style></noscript><script>
(()=>{
const views=[...document.querySelectorAll('[data-view]')],days=[...document.querySelectorAll('[data-day-id]')],foods=[...document.querySelectorAll('[data-food-id]')],nav=[...document.querySelectorAll('.nav-strip a')];
const ids=days.map(x=>x.dataset.dayId);const today=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
let selected=ids.find(id=>'2026-12-'+id.split('-').at(-1).padStart(2,'0')>=today)||ids.at(-1);let foodSelected=selected;
function paint(){let hash=decodeURIComponent(location.hash.slice(1));let view={timeline:'daily',home:'home',bookings:'bookings',food:'food',transport:'transport',packing:'packing',links:'links'}[hash]||'home';if(hash.startsWith('day-')&&ids.includes(hash)){view='daily';selected=hash}if(hash.startsWith('food-day-')&&ids.includes(hash.slice(5))){view='food';foodSelected=hash.slice(5)}
views.forEach(x=>x.hidden=x.dataset.view!==view);nav.forEach(x=>{if((x.hash==='#timeline'?'daily':x.hash.slice(1))===view)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current')});
days.forEach(x=>x.hidden=x.dataset.dayId!==selected);foods.forEach(x=>x.hidden=x.dataset.foodId!==foodSelected);
for(const kind of ['day','food'])document.querySelectorAll('[data-'+kind+'-target]').forEach(b=>{const active=b.dataset[kind+'Target']===(kind==='day'?selected:foodSelected);b.classList.toggle('is-active',active);b.setAttribute('aria-pressed',String(active))});
document.getElementById('day-position').textContent=(ids.indexOf(selected)+1)+' / '+ids.length+' 天';document.querySelector('[data-step="-1"]').disabled=selected===ids[0];document.querySelector('[data-step="1"]').disabled=selected===ids.at(-1);
}
document.querySelectorAll('[data-day-target]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.dayTarget}));document.querySelectorAll('[data-food-target]').forEach(b=>b.addEventListener('click',()=>{location.hash='food-'+b.dataset.foodTarget}));
document.querySelectorAll('[data-step]').forEach(b=>b.addEventListener('click',()=>{const i=ids.indexOf(selected)+Number(b.dataset.step);if(ids[i]){location.hash=ids[i];document.querySelector('#timeline').scrollIntoView({block:'start'})}}));
document.querySelectorAll('a[href^="#"]').forEach(a=>{a.removeAttribute('target');a.removeAttribute('rel')});
document.querySelectorAll('[data-check]').forEach(c=>{const key='orlando-v3-'+c.dataset.check;try{const saved=localStorage.getItem(key);if(saved!==null)c.checked=saved==='true'}catch{}c.addEventListener('change',()=>{try{localStorage.setItem(key,String(c.checked))}catch{}})});
window.addEventListener('hashchange',paint);paint();
})();
</script></body></html>'''
photo_viewer = '''<dialog id="photo-viewer" class="photo-viewer" aria-label="项目图片大图"><button type="button" class="photo-close" aria-label="关闭图片">关闭 ×</button><img alt=""><p></p></dialog><script>
const photoViewer = document.getElementById('photo-viewer');
let photoTrigger;
document.addEventListener('click', event => {
  const trigger = event.target.closest('.photo-zoom');
  if (!trigger) return;
  photoTrigger = trigger;
  const image = trigger.querySelector('img');
  const full = photoViewer.querySelector('img');
  full.src = image.src;
  full.alt = image.alt;
  photoViewer.querySelector('p').textContent = trigger.closest('figure').querySelector('strong').textContent;
  photoViewer.showModal();
});
photoViewer.querySelector('button').addEventListener('click', () => photoViewer.close());
photoViewer.addEventListener('click', event => { if (event.target === photoViewer) photoViewer.close(); });
photoViewer.addEventListener('close', () => { photoViewer.querySelector('img').removeAttribute('src'); photoTrigger?.focus(); });
</script>'''
html = html.replace('</body>', photo_viewer + '</body>')
OUT.write_text(html)
(ROOT / 'index.html').write_text(html)
print(f'Generated {OUT} ({len(html.encode()):,} bytes), {len(days)} days, 7 views.')
