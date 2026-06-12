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
    seen = set()

    for li in soup.select('ul.prdList li, li.xans-record-'):
        # 상품 링크
        a = li.select_one('a[href*="/product/"]')
        if not a: continue
        href = a.get('href', '')
        if not href or href in seen or '/list' in href: continue
        seen.add(href)
        url = BASE + href if href.startswith('/') else href

        # 상품명
        li_text = li.get_text(separator=' ', strip=True)
        raw = a.get('title') or a.get_text(strip=True)
        raw = re.sub(r'^상품명[:\s]*', '', raw).strip()
        raw = re.sub(r'^\[커피생두\]\s*', '', raw).strip()
        # 텍스트에서 "상품명 :" 패턴으로 추출
        m = re.search(r'상품명\s*[:\s]+([^\n판]{4,80})', li_text)
        if m and len(m.group(1).strip()) > 3:
            raw = re.sub(r'^\[커피생두\]\s*', '', m.group(1).strip()).strip()
        if not raw or len(raw) < 3: continue

        # 품절 감지: img alt="품절", soldout 클래스, 텍스트
        soldout = is_soldout_block(li)

        # 가격
        price_m = re.search(r'판매가[^0-9]*([\d,]+)원', li_text)
        if not price_m:
            price_m = re.search(r'([\d,]+)원', li_text)
        price = int(price_m.group(1).replace(',', '')) if price_m else 0
        if price < 1000 and not soldout: continue

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
