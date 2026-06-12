"""아얀투 생두 스크래퍼 — imweb /greenbean/?&page=N"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '아얀투'
BASE  = 'https://ayantu.co.kr'
URL   = BASE + '/greenbean/?&page={page}&sort=recent'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    # imweb 상품 구조: 상품 카드에 제목 + 가격
    for card in soup.select('.prd-item, .product-item, [class*="prd"], li[class*="item"]'):
        name_el = card.select_one('strong, .title, .name, h3, h4')
        if not name_el: continue
        name = name_el.get_text(strip=True)
        if not name or len(name) < 3: continue
        price_m = re.search(r'([\d,]+)원', card.get_text())
        if not price_m: continue
        price = int(price_m.group(1).replace(',',''))
        if price < 1000: continue
        a = card.select_one('a[href*="idx"]') or card.select_one('a')
        if not a: continue
        href = a.get('href','')
        url = BASE + href if href.startswith('/') else href
        items.append({'name': name, 'price': price, 'url': url})
    return items

def parse_v2(html):
    """대안: 전체 텍스트에서 상품명+가격+링크 추출"""
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.select('a[href*="idx="]'):
        name = a.get_text(strip=True)
        if not name or len(name) < 3: continue
        parent = a
        price = 0
        for _ in range(6):
            parent = parent.parent
            if parent is None: break
            m = re.search(r'([\d,]+)원', parent.get_text())
            if m:
                price = int(m.group(1).replace(',',''))
                if price > 1000: break
        if not price: continue
        href = a.get('href','')
        url = BASE + href if href.startswith('/') else href
        items.append({'name': name, 'price': price, 'url': url})
    return items

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items, page, total = [], 1, 1
    while True:
        html = fetch(URL.format(page=page), s)
        if page == 1:
            total = get_total_pages(html)
            print(f"  총 {total}페이지")
        items = parse(html) or parse_v2(html)
        if not items and page > 1: break
        all_items.extend(items)
        print(f"  p{page} → {len(items)}개")
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
    id_start = 301
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
