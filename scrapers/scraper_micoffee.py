"""엠아이커피 생두 스크래퍼 — Godomall cateCd=001~004,012"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE    = '엠아이커피'
BASE     = 'https://www.micoffee.co.kr'
CATS     = ['001','002','003','004','012']  # 남미,중미,아프리카,아시아,디카페인
LIST_URL = BASE + '/goods/goods_list.php?cateCd={cat}&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.select('a[href*="goods_view.php"]'):
        name = a.get_text(strip=True)
        if not name or len(name) < 3: continue
        parent = a
        price = 0
        soldout = False
        for _ in range(8):
            parent = parent.parent
            if parent is None: break
            block_text = parent.get_text()
            if not soldout:
                soldout = bool(re.search(r'품절|SOLD.?OUT', block_text))
            m = re.search(r'([\d,]+)원', block_text)
            if m:
                price = int(m.group(1).replace(',',''))
                if price > 1000: break
        if not price and not soldout: continue
        href = a.get('href','')
        url = BASE + '/goods/' + href if href.startswith('goods_view') else (BASE + href if href.startswith('/') else href)
        items.append({'name': name, 'price': price, 'url': url, 'is_soldout': soldout})
    return items

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items = []
    for cat in CATS:
        page, total = 1, 1
        while True:
            html = fetch(LIST_URL.format(cat=cat, page=page), s)
            if page == 1:
                total = get_total_pages(html)
            items = parse(html)
            if not items and page > 1: break
            all_items.extend(items)
            print(f"  cat={cat} p{page}/{total} → {len(items)}개")
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
    id_start = 201
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
