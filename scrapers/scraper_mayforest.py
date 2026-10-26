"""오월의숲 생두 스크래퍼 — Cafe24 cate_no=50

**2026-10-26 품절 감지 수정**
목록 썸네일의 품절 이미지 오버레이(is_soldout_block)를 신뢰했더니 37개 상품이
전부(100%) 품절로 잡혔다. GitHub Actions 실측 결과, 상세페이지 schema.org
availability 는 전부 InStock 이었다 — 즉 Cafe24 가 품절 이미지를 전 상품 li 에
숨겨진 템플릿으로 깔아둔 것이고(코빈즈 div.soldout·모모스 .prod_icon.sold_out 과
같은 함정), 실제로는 재고가 있었다. HTML 파싱만으로는 CSS 로 숨겨진 오버레이의
표시 여부를 알 수 없다. 그래서 목록 오버레이는 버리고, **상세페이지의 권위 신호
schema.org "availability"** 로 상품별 품절을 판정한다(상품 수가 적어 부담 적음).
"""
import re, time, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *
from bs4 import BeautifulSoup

STORE = '오월의숲'
BASE  = 'https://mayforest.kr'
URL   = BASE + '/product/list.html?cate_no=50&page={page}'

# 상세페이지 서버 HTML 의 schema.org 재고 신호 (JS 없이 나온다).
AVAIL_RE = re.compile(r'"availability"\s*:\s*"?(?:https?://schema\.org/)?'
                      r'(InStock|OutOfStock|SoldOut|BackOrder|Discontinued)', re.I)
SOLDOUT_WORDS = ('outofstock', 'soldout', 'discontinued')


def fetch_soldout(url, session):
    """상세페이지 availability 로 품절 판정. 판독 실패 시 None(모름)."""
    try:
        html = fetch(url, session)
    except Exception:
        return None
    m = AVAIL_RE.search(html)
    if m:
        return m.group(1).lower() in SOLDOUT_WORDS
    return None


def add_soldout(items, session):
    """상품별 상세페이지를 받아 품절 여부를 채운다(목록 오버레이는 신뢰 불가).

    상세 availability 가 OutOfStock 이면 품절. 판독 실패(None)는 거짓 품절을
    만들지 않기 위해 재고(False)로 둔다.
    """
    unknown = 0
    for it in items:
        so = fetch_soldout(it['url'], session)
        if so is None:
            unknown += 1
        it['is_soldout'] = bool(so)
        time.sleep(0.3)
    sold = sum(1 for it in items if it['is_soldout'])
    print(f"  품절 확인(상세 availability): {sold}개 품절 / {len(items)}개"
          + (f" (판독 실패 {unknown}개는 재고로 둠)" if unknown else ""))

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
        # 품절은 목록에서 판단하지 않는다 — 품절 오버레이가 전 상품에 템플릿으로
        # 깔려 100% 오탐이 났다(2026-10-26). 수집 후 add_soldout() 이 상세페이지
        # availability 로 상품별로 채운다.
        items.append({'name': raw, 'price': price, 'url': url, 'is_soldout': False})
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
    add_soldout(unique, s)
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
