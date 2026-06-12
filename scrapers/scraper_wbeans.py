"""더블유빈 생두 스크래퍼 — Godomall goods_search.php?acec=000062"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '더블유빈'
BASE  = 'https://wbeans.com'
URL   = BASE + '/goods/goods_search.php?acec=000062&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for card in soup.select('div.item_cont'):
        # 상품명: item_name 클래스 또는 strong
        name_el = card.select_one('.item_name, strong')
        if not name_el: continue
        name = name_el.get_text(strip=True)
        if not name or len(name) < 3: continue
        if name in ['장바구니','찜하기']: continue

        card_text = card.get_text()
        soldout = is_soldout_block(card)

        # URL: 부모 li나 상위에서 goods_view 링크
        parent = card.parent
        a = parent.select_one('a[href*="goods_view"]') if parent else None
        if not a: continue
        href = a.get('href','')
        if href.startswith('..'): href = href.replace('..', '/goods')
        url = BASE + href if href.startswith('/') else href

        # 가격 (품절이면 0 허용, update_json에서 기존 가격 복원)
        price_m = re.search(r'([\d,]+)원', card_text)
        price = int(price_m.group(1).replace(',','')) if price_m else 0
        if price < 1000 and not soldout: continue

        items.append({'name': name, 'price': price, 'url': url, 'is_soldout': soldout})
    return items

def get_total_pages_wbeans(html):
    nums = re.findall(r'page=(\d+)', html)
    return max((int(n) for n in nums), default=1)

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items, page, total = [], 1, 1
    while True:
        html = fetch(URL.format(page=page), s)
        if page == 1:
            total = get_total_pages_wbeans(html)
            print(f"  총 {total}페이지")
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
    id_start = 901
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
