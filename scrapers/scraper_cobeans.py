"""코빈즈커피 생두 스크래퍼 — Custom(Wisa) big_section.php?cno1=1014"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '코빈즈커피'
BASE  = 'https://www.cobeans.com'
URL   = BASE + '/shop/big_section.php?cno1=1014&page={page}'

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for a in soup.select('a[href*="detail.php?pno="]'):
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
                soldout = is_soldout_block(parent)
            prices = re.findall(r'([\d,]+)원', block_text)
            valid = [int(p.replace(',','')) for p in prices if int(p.replace(',','')) > 1000]
            if valid:
                price = valid[-1]
                break
        if not price and not soldout: continue
        href = a.get('href','')
        url = BASE + '/shop/' + href if href.startswith('detail') else (BASE + href if href.startswith('/') else href)
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
    id_start = 251
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
