"""커피창고 생두 스크래퍼 — Cafe24 cate_no=802"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '커피창고'
BASE  = 'https://www.coffeecg.com'
URL   = BASE + '/product/list.html?cate_no=802&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for card in soup.select('li.xans-record-'):
        a = card.select_one('a[href*="/product/"]')
        if not a: continue
        name_el = card.select_one('strong, .name')
        name = (name_el or a).get_text(strip=True)
        if not name or len(name) < 3: continue
        card_text = card.get_text()
        soldout = is_soldout_block(card)
        m = re.search(r'판매가.*?([\d,]+)원', card_text, re.DOTALL)
        if not m: m = re.search(r'([\d,]+)원', card_text)
        price = int(m.group(1).replace(',','')) if m else 0
        if price < 1000 and not soldout: continue
        href = a.get('href','')
        url = BASE + href if href.startswith('/') else href
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
    id_start = 71
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
