"""Keep the Markdown photo index aligned with the HTML photo manifest."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent.parent
START = '<!-- project-photos:start -->'
END = '<!-- project-photos:end -->'

def sync_photo_sections():
    path = ROOT / 'orlando_trip_cn_2026-12-04_12-12.md'
    photos = json.loads((ROOT / 'data/project_photos.json').read_text())
    text = re.sub(re.escape(START) + r'.*?' + re.escape(END) + r'\n*', '', path.read_text(), flags=re.S)
    def insert(match):
        day = int(match[1])
        items = [p for p in photos if p['day'] == day]
        if not items:
            return match[0]
        block = [START, '#### 当天项目图片', '', '图片对应当天行程；“可选”和 A／B 路线仍按原计划取舍。图片为项目与景观参考，不代表当天运营、天气或观看位置。', '', '| 项目与图片 | 行程定位／图片来源 |', '| --- | --- |']
        for p in items:
            license_note = f" · [{p['license']}]({p['license_url']}) · {p['changes']}" if p.get('license') else ''
            block.append(f"| **{p['title']}**<br>![{p['alt']}]({p['local_path']}) | {p['tag']} · [{p['credit']}]({p['source_url']}){license_note} |")
        block += ['', END, '']
        return match[0] + '\n' + '\n'.join(block) + '\n'
    text = re.sub(r'^### 12/(\d+) 周.｜[^\n]+\n', insert, text, flags=re.M)
    text = text.replace('行程规划 v6（加入 Reunion 暂定住宿）', '行程规划 v7（Reunion 住宿＋每日项目图片）')
    path.write_text(text)

if __name__ == '__main__':
    sync_photo_sections()
