"""지에스씨(GSC) 생두 스크래퍼 — Godomall cateCd=014"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '지에스씨(GSC)'
BASE  = 'https://www.gsc.coffee'
URL   = BASE + '/goods/goods_list.php?cateCd=014&page={page}'

_SOLDOUT_TOKENS = ('soldout', '품절', 'sold')

def _norm(t):
    return re.sub(r'[\s\W_]+', '', t or '').lower()

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    # 품절 상품은 같은 goodsNo에 대해 'SOLD OUT' 텍스트만 든 별도 앵커가 존재한다.
    # 앵커를 goodsNo로 묶어, 품절 토큰이 아닌 '실제 이름'을 선택하고 품절 여부를 따로 표시한다.
    groups = {}  # key(goodsNo) -> {'texts':[...], 'anchor':<name앵커>, 'href':...}
    for a in soup.select('a[href*="goods_view.php"]'):
        href = a.get('href', '')
        m = re.search(r'goodsNo=(\d+)', href)
        key = m.group(1) if m else href
        txt = a.get_text(strip=True)
        g = groups.setdefault(key, {'texts': [], 'anchor': a, 'href': href})
        if txt:
            g['texts'].append(txt)
        # 실제 이름(품절 토큰 아님)을 든 앵커를 대표로 — 가격 추출 기준점
        if txt and _norm(txt) not in _SOLDOUT_TOKENS and len(txt) >= 3:
            if _norm(g['texts'][0] if g['texts'] else '') in _SOLDOUT_TOKENS or g['anchor'].get_text(strip=True) == '':
                g['anchor'], g['href'] = a, href

    items = []
    for g in groups.values():
        real = [t for t in g['texts'] if _norm(t) not in _SOLDOUT_TOKENS and len(t) >= 3]
        if not real:
            continue  # 실제 이름을 못 찾으면 제외 (깨진 캡처)
        name = max(real, key=len)
        soldout = any(_norm(t) in _SOLDOUT_TOKENS for t in g['texts'])

        price, parent = 0, g['anchor']
        for _ in range(8):
            parent = parent.parent
            if parent is None: break
            prices = re.findall(r'([\d,]+)원', parent.get_text())  # 할인가 우선 (마지막 가격)
            if prices:
                price = int(prices[-1].replace(',', ''))
                if price > 1000: break
        if not price: continue

        href = g['href']
        url = BASE + '/goods/' + href if href.startswith('goods_view') else (BASE + href if href.startswith('/') else href)
        items.append({'name': name, 'price': price, 'url': url, 'is_soldout': soldout})
    return items

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items, page, total = [], 1, 1
    while True:
        html = fetch(URL.format(page=page), s)
        if page == 1: total = get_total_pages(html)
        items = parse(html)
        if not items and page > 1: break
        all_items.extend(items)
        print(f"  p{page}/{total} → {len(items)}개")
        if page >= total: break
        page += 1; time.sleep(0.8)
    seen, unique = set(), []
    for i in all_items:
        if i['url'] not in seen: seen.add(i['url']); unique.append(i)
    print(f"[{STORE}] 총 {len(unique)}개")
    return unique

if __name__ == '__main__':
    items = scrape()
    import json, os
    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    kept = [p for p in data['products'] if p['store'] != STORE]
    existing_ids = {p['id'] for p in kept}
    id_start = 601
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start, existing_ids))
