"""블레스빈 생두 스크래퍼 — 자체 플랫폼 /shop/list.php?ca_id=20
목록 페이지에 가격 없음 → 상품 코드만 수집 후 개별 페이지 방문
"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE    = '블레스빈'
BASE     = 'https://www.blessbean.co.kr'
LIST_URL = BASE + '/shop/list-20?page={page}'

def parse_list(html):
    """목록에서 (상품명, URL) 수집"""
    soup = BeautifulSoup(html, 'html.parser')
    seen_code, items = set(), []
    for a in soup.select('a[href*="ca_id"]'):
        href = a.get('href','')
        # /shop/XX-XXXXXX 패턴 상품 URL
        m = re.search(r'/shop/([A-Z]{2}-\w+)', href)
        if not m: continue
        code = m.group(1)
        name = a.get_text(strip=True)
        # 이름이 없거나 배지 텍스트면 skip
        if not name or len(name) < 3: continue
        if name in ['DC','SOLD','품절','준비중','간편주문','생두']: continue
        if code in seen_code: continue
        seen_code.add(code)
        url = BASE + f'/shop/{code}'
        items.append({'name': name, 'url': url})
    return items

def fetch_price(url, session):
    """개별 상품 페이지에서 1kg 가격 추출"""
    try:
        html = fetch(url, session)
        text = html
        # "1kg + XX,XXX원" 패턴 우선
        m = re.search(r'1kg\s*\+\s*([\d,]+)원', text)
        if m: return int(m.group(1).replace(',',''))
        # "1 kg + XX,XXX원" 변형
        m = re.search(r'1\s*kg[^<]{0,20}([\d,]+)원', text)
        if m: return int(m.group(1).replace(',',''))
        # 첫 번째 의미있는 가격 (0원 제외)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for t in soup.find_all(string=re.compile(r'\d[\d,]+원')):
            p_m = re.search(r'([\d,]+)원', t)
            if p_m:
                p = int(p_m.group(1).replace(',',''))
                if p >= 5000: return p
        return 0
    except Exception:
        return 0

def scrape():
    print(f"[{STORE}] 시작...")
    s = new_session()
    all_items, page, total = [], 1, 1
    while True:
        html = fetch(LIST_URL.format(page=page), s)
        if page == 1:
            # 블레스빈은 page=1&page=N 이중 파라미터 형태
            nums = re.findall(r'page=(\d+)', html)
            total = max((int(n) for n in nums), default=1)
        items = parse_list(html)
        all_items.extend(items)
        print(f"  p{page}/{total} → {len(items)}개 링크")
        if not items and page > 1: break
        if page >= total: break
        page += 1; time.sleep(0.8)

    # 중복 제거
    seen, unique = set(), []
    for i in all_items:
        if i['url'] not in seen: seen.add(i['url']); unique.append(i)

    # 개별 가격 수집
    result = []
    for i, item in enumerate(unique):
        price = fetch_price(item['url'], s)
        if price > 0:
            result.append({'name': item['name'], 'price': price, 'url': item['url']})
            print(f"  [{i+1}/{len(unique)}] {item['name'][:40]} → {price:,}원")
        else:
            print(f"  [{i+1}/{len(unique)}] ⚠️ 가격없음: {item['name'][:40]}")
        time.sleep(0.5)

    print(f"[{STORE}] 총 {len(result)}개")
    return result

if __name__ == '__main__':
    items = scrape()
    import json, os
    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    kept = [p for p in data['products'] if p['store'] != STORE]
    existing_ids = {p['id'] for p in kept}
    id_start = 401
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
