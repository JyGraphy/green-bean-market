"""
커피리브레 생두소분 스크래퍼
URL: https://coffeelibre.kr/product/list.html?cate_no=57
플랫폼: Cafe24 (서버렌더링)
[소분] 태그가 붙은 상품 = 1kg 단위 구매 가능
"""
import re, json, time, os
import requests
from bs4 import BeautifulSoup

STORE   = '커피리브레'
BASE    = 'https://coffeelibre.kr'
# cate_no=57: 생두소분 카테고리
CAT_URL = BASE + '/product/list.html?cate_no=57&page={page}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

ORIGIN_MAP = {
    '에티오피아':'에티오피아','케냐':'케냐','탄자니아':'탄자니아','르완다':'르완다',
    '우간다':'우간다','콩고':'콩고민주공화국','브라질':'브라질','콜롬비아':'콜롬비아',
    '과테말라':'과테말라','코스타리카':'코스타리카','파나마':'파나마',
    '엘살바도르':'엘살바도르','온두라스':'온두라스','멕시코':'멕시코',
    '자메이카':'자메이카','페루':'페루','볼리비아':'볼리비아','에콰도르':'에콰도르',
    '니카라과':'니카라과','인도네시아':'인도네시아','인도':'인도',
    '베트남':'베트남','예멘':'예멘','중국':'중국','파푸아뉴기니':'파푸아뉴기니','하와이':'하와이',
}
REGION_MAP = {
    '에티오피아':'아프리카','케냐':'아프리카','탄자니아':'아프리카','르완다':'아프리카',
    '우간다':'아프리카','콩고민주공화국':'아프리카',
    '브라질':'중남미','콜롬비아':'중남미','과테말라':'중남미','코스타리카':'중남미',
    '파나마':'중남미','엘살바도르':'중남미','온두라스':'중남미','멕시코':'중남미',
    '자메이카':'중남미','페루':'중남미','볼리비아':'중남미','에콰도르':'중남미','니카라과':'중남미',
    '인도네시아':'아시아/태평양','인도':'아시아/태평양','베트남':'아시아/태평양',
    '예멘':'아시아/태평양','중국':'아시아/태평양','파푸아뉴기니':'아시아/태평양','하와이':'아시아/태평양',
}

def guess_origin(name):
    for k, v in ORIGIN_MAP.items():
        if k in name:
            return v, REGION_MAP.get(v, '기타')
    return '알수없음', '기타'

def guess_process(name):
    n = name.lower()
    if any(x in n for x in ['무산소', 'anaerobic', '카보닉', 'carbonic', 'infused', '인퓨즈드']): return '무산소발효'
    if any(x in n for x in ['허니', 'honey', '레드허니', '화이트허니', '옐로우허니']): return '허니'
    if any(x in n for x in ['펄프드내추럴', 'pulped natural', 'pulped']): return '펄프드내추럴'
    if any(x in n for x in ['내추럴', 'natural', '레포사도']): return '내추럴'
    if any(x in n for x in ['워시드', 'washed', 'fully washed']): return '워시드'
    if any(x in n for x in ['웻훌', 'wet hul']): return '웻훌드'
    return '알수없음'

def fetch(url, session):
    r = session.get(url, timeout=15)
    r.raise_for_status()
    return r.text

def is_soldout_block(el):
    """품절 감지 — 썸네일 위 이미지 오버레이만 신뢰.
    (CSS 클래스/텍스트 검색은 Cafe24 숨김 템플릿·공통 조상까지 매칭되어 오탐 발생)"""
    if el is None: return False
    if el.select_one('img[alt*="품절"], img[alt*="SOLD OUT"], img[alt*="Sold out"], '
                     'img[src*="soldout"], img[src*="sold_out"], img[src*="icon_soldout"]'): return True
    return False

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []

    for a in soup.select('a[href*="product_no"]'):
        text = a.get_text(strip=True)
        # [소분] 태그가 붙은 것만 (1kg 단위)
        if not text.startswith('[소분]'):
            continue

        href = a.get('href', '')
        url = BASE + href if href.startswith('/') else href

        # 상품명에서 [소분] 제거
        name = re.sub(r'^\[소분\]\s*', '', text).strip()
        if not name:
            continue

        # 품절은 상품 자신의 li 안에서만 확인 (상위 공통 조상까지 올라가면 전체 오염)
        li_el = a.find_parent('li')
        soldout = is_soldout_block(li_el)

        # 부모 블록에서 가격 찾기
        parent = a
        price = 0
        for _ in range(10):
            parent = parent.parent
            if parent is None:
                break
            block_text = parent.get_text()
            m = re.search(r'([\d,]+)원', block_text)
            if m:
                price = int(m.group(1).replace(',', ''))
                if price > 1000:
                    break

        if not price and not soldout:
            continue

        items.append({'name': name, 'price': price, 'url': url, 'is_soldout': soldout})

    return items

def get_total_pages(html):
    nums = re.findall(r'[?&]page=(\d+)', html)
    return max((int(n) for n in nums), default=1)

def scrape():
    print(f"[{STORE}] 생두소분 스크래핑 시작 (cate_no=57)...")
    session = requests.Session()
    session.headers.update(HEADERS)

    all_items = []
    page = 1
    total_pages = None

    while True:
        url = CAT_URL.format(page=page)
        print(f"  페이지 {page}: {url}")
        try:
            html = fetch(url, session)
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            break

        if total_pages is None:
            total_pages = get_total_pages(html)
            print(f"  총 {total_pages}페이지")

        items = parse_page(html)
        if not items and page > 1:
            print(f"  ⚠️ 상품 없음 — 종료")
            break

        all_items.extend(items)
        print(f"  → {len(items)}개 [소분] 상품")

        if page >= total_pages:
            break
        page += 1
        time.sleep(1.0)

    # 중복 제거
    seen, unique = set(), []
    for i in all_items:
        if i['url'] not in seen:
            seen.add(i['url'])
            unique.append(i)

    print(f"[{STORE}] 총 {len(unique)}개 수집")
    return unique

def to_products(items, id_start, taken=None):
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from common import alloc_ids, is_non_bean
    items = [it for it in items if not is_non_bean(it['name'])]  # 비생두 제외
    ids = alloc_ids(len(items), id_start, taken)
    results = []
    for i, item in enumerate(items):
        origin, region = guess_origin(item['name'])
        name = item['name']
        results.append({
            "id":         ids[i],
            "store":      STORE,
            "name":       name,
            "price":      item['price'],
            "origin":     origin,
            "region":     region,
            "process":    guess_process(name),
            "notes":      "",
            "url":        item['url'],
            "is_new":     any(x in name for x in ['2026', '25/26', '2025/26', '2025/2026']),
            "is_decaf":   '디카페인' in name,
            "is_special": any(x in name for x in ['게이샤','파카마라','에스메랄다']) or item['price'] >= 50000,
            "is_soldout": item.get('is_soldout', False),
        })
    return results

if __name__ == '__main__':
    items = scrape()

    root = os.path.join(os.path.dirname(__file__), '..')
    json_path = os.path.join(root, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    kept = [p for p in data['products'] if p['store'] != STORE]
    existing_ids = {p['id'] for p in kept}

    # 커피리브레 기존 ID 범위: 637~713
    id_start = 637
    while id_start in existing_ids:
        id_start += 1

    new_products = to_products(items, id_start, existing_ids)

    # 안전장치: 공용 가드로 빈/부분 결과 시 기존 데이터 보존 (단일 진실 공급원)
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import guard_store_replacement
    old_count = sum(1 for p in data['products'] if p['store'] == STORE)
    guard_store_replacement(STORE, old_count, len(new_products))

    data['products'] = kept + new_products

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ products.json 업데이트: {STORE} {len(new_products)}개 (이전 {old_count}개)")
