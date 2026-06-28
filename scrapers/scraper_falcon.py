"""팔콘커피 생두 스크래퍼 — Shopify /collections/korea-store-all-coffee"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '팔콘커피'
BASE  = 'https://korea.falcon-micro.com'
URL   = BASE + '/collections/korea-store-all-coffee?page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    # Shopify: 상품 카드 구조
    for card in soup.select('.product-item, .grid-item, [class*="product"]'):
        name_el = card.select_one('h3, h2, .product-title, [class*="title"], [class*="name"]')
        if not name_el: continue
        name = name_el.get_text(strip=True)
        if not name or len(name) < 3: continue
        # 가격: ₩ 또는 원
        price_text = card.get_text()
        m = re.search(r'[₩￦]([\d,]+)', price_text)
        if not m:
            m = re.search(r'([\d,]+)원', price_text)
        if not m: continue
        price = int(m.group(1).replace(',',''))
        if price < 1000: continue
        a = card.select_one('a[href*="/products/"]')
        if not a: continue
        href = a.get('href','')
        url = BASE + href if href.startswith('/') else href
        items.append({'name': name, 'price': price, 'url': url})
    return items

def parse_v2(html):
    """대안: /products/ 링크 직접 탐색"""
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    seen = set()
    for a in soup.select('a[href*="/products/"]'):
        href = a.get('href','')
        if href in seen: continue
        # 컬렉션 링크 제외
        if '/collections/' in href: continue
        name = a.get_text(strip=True)
        if not name or len(name) < 3: continue
        seen.add(href)
        parent = a
        price = 0
        for _ in range(8):
            parent = parent.parent
            if parent is None: break
            m = re.search(r'[₩￦]([\d,]+)', parent.get_text())
            if not m: m = re.search(r'([\d,]+)원', parent.get_text())
            if m:
                price = int(m.group(1).replace(',',''))
                if price > 1000: break
        if not price: continue
        url = BASE + href if href.startswith('/') else href
        items.append({'name': name, 'price': price, 'url': url})
    return items

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items, page, total = [], 1, 1
    while True:
        html = fetch(URL.format(page=page), s)
        if page == 1: total = get_total_pages(html)
        items = parse(html) or parse_v2(html)
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
    id_start = 801
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start, existing_ids))
