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
    # 메인 상품목록만 순회 (추천위젯 ul.prdList 제외, price_span 역추적은 공통 조상 오탐)
    for li in soup.select('.xans-product-listnormal ul.prdList > li'):
        a = li.select_one('a[href*="/product/"]')
        if not a:
            continue
        name_el = li.select_one('.description .name') or li.select_one('.name')
        raw = (name_el.get_text(' ', strip=True) if name_el else '')
        # "상품명 : [커피생두] " 접두어 제거
        raw = re.sub(r'^상품명\s*:\s*', '', raw).strip()
        raw = re.sub(r'^\[커피생두\]\s*', '', raw).strip()
        if not raw or len(raw) < 3:
            continue
        m = re.search(r'([\d,]+)\s*원', li.get_text())
        if not m:
            continue
        price = int(m.group(1).replace(',', ''))
        if price < 1000:
            continue
        href = a.get('href', '')
        url = abs_url(BASE, href)
        # 품절: 상품 자신의 li 안 이미지 오버레이만 신뢰
        soldout = is_soldout_block(li)
        items.append({'name': raw, 'price': price, 'url': url, 'is_soldout': soldout})
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
        key = i['url'].split('?')[0]  # 쿼리스트링(display 변형) 제거 후 중복 제거
        if key not in seen: seen.add(key); unique.append(i)
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
    update_json(STORE, to_products(items, STORE, id_start, existing_ids))
