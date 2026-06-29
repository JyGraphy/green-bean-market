"""커만사 생두 스크래퍼 — Godomall cateCd=022"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '커만사'
BASE  = 'https://comansa.kr'
URL   = BASE + '/goods/goods_list.php?cateCd=022&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.select('a[href*="goods_view.php"]'):
        name = a.get_text(strip=True)
        # "(커피생두)" 접두어 제거
        name = re.sub(r'^\(커피생두\)\s*', '', name).strip()
        if not name or len(name) < 3: continue
        # 품절 오버레이/배지 링크 텍스트는 상품명이 아님 → 스킵
        if re.fullmatch(r'(SOLD\s?OUT|SOLDOUT|품절|준비중|일시품절)', name, re.I): continue
        parent = a
        price = 0
        for _ in range(8):
            parent = parent.parent
            if parent is None: break
            prices = re.findall(r'([\d,]+)원', parent.get_text())
            if prices:
                price = int(prices[-1].replace(',',''))
                if price > 1000: break
        if not price: continue
        href = a.get('href','')
        url = abs_url(BASE + '/goods/', href)  # 상대경로(../goods/...)도 절대화
        items.append({'name': name, 'price': price, 'url': url})
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
    id_start = 1001
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start, existing_ids))
