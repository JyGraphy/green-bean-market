"""오월의숲 생두 스크래퍼 — Cafe24 cate_no=50"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '오월의숲'
BASE  = 'https://mayforest.kr'
URL   = BASE + '/product/list.html?cate_no=50&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    # 가격 span → 부모 체인 → 상품명 링크
    for price_span in soup.find_all(string=re.compile(r'\d[\d,]+원')):
        price_m = re.search(r'([\d,]+)원', price_span)
        if not price_m: continue
        price = int(price_m.group(1).replace(',',''))
        if price < 1000: continue
        # 부모 체인에서 상품 URL, 이름 찾기
        parent = price_span.parent
        name, url = None, None
        for _ in range(10):
            parent = parent.parent
            if parent is None: break
            a = parent.select_one('a[href*="/product/"]')
            if a:
                raw = a.get_text(strip=True)
                # "상품명:[커피생두] " 접두어 제거
                raw = re.sub(r'^상품명:', '', raw).strip()
                raw = re.sub(r'^\[커피생두\]\s*', '', raw).strip()
                if raw and len(raw) > 3:
                    name = raw
                    href = a.get('href','')
                    url = BASE + href if href.startswith('/') else href
                    break
        if name and url:
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
    id_start = 551
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
