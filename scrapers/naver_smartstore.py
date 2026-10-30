"""네이버 스마트스토어 공용 스크래핑 모듈.

⚠️ 네이버는 데이터센터 IP(GitHub Actions, 클라우드)를 차단한다(429 또는 로그인 리다이렉트).
   실측: GH Actions에서 requests → 429, Playwright 실브라우저 → 로그인 월.
   따라서 스마트스토어 스크래퍼는 run_all.py(CI)에 넣지 않고,
   가정용 IP의 로컬 PC에서 수동 실행한다:

       python scrapers/scraper_amativo.py
       python scrapers/scraper_ruber.py

   수집 결과는 data/products.json에 반영되므로 커밋하면 된다.
   (매일 갱신 CI는 이 store들을 건드리지 않아 데이터가 보존된다 — 더블유빈/콤파스커피와 동일 구조)

내부 API (비공식, 스마트스토어 프론트가 쓰는 것과 동일):
  - 상점 정보:  GET /i/v1/smart-stores?url={storeId}            → {'id': 채널번호, ...}
  - 상품 목록:  GET /i/v2/channels/{채널번호}/categories/{카테고리}/products
                ?categorySearchType={STDCATG|DISPCATG}&sortType=TOTALSALE&page=N&pageSize=40
                → {'totalCount': N, 'simpleProducts': [...]}
    · 전체 상품: 카테고리 'ALL' + STDCATG
    · 특정 진열 카테고리(32자리 hex): DISPCATG
"""
import re
import time

import requests

BASE = 'https://smartstore.naver.com'

# 브라우저에 가깝게 — 쿠키 없는 맨 요청은 네이버가 429로 막는다(2026-10 실측: 가정용
# IP에서도 첫 API 호출부터 429). 그래서 (1) 스토어 페이지를 먼저 한 번 열어 세션 쿠키
# (NNB 등)를 받고 (2) 그 세션으로 Referer 를 붙여 내부 API 를 호출한다.
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
PAGE_HEADERS = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}
API_HEADERS = {
    'User-Agent': UA,
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'X-Requested-With': 'XMLHttpRequest',
}
# 하위호환: 기존 코드가 import 하던 이름 유지
HEADERS = API_HEADERS


class NaverBlocked(Exception):
    """네이버가 이 요청을 차단함 (429/로그인 리다이렉트)."""


def warmup(session, store_id):
    """스토어 페이지를 먼저 열어 세션 쿠키를 받는다(이후 API 429 방지).

    실패해도 치명적이지 않다 — API 호출에서 다시 판정한다.
    """
    try:
        session.get(f'{BASE}/{store_id}', headers=PAGE_HEADERS, timeout=20)
    except requests.RequestException:
        pass


def _get_json(session, url, referer):
    """세션 쿠키 + Referer 로 내부 API 호출. 429 는 몇 번 재시도 후 NaverBlocked."""
    headers = dict(API_HEADERS, Referer=referer)
    last = None
    for attempt in range(3):
        r = session.get(url, headers=headers, timeout=20)
        if 'nid.naver.com' in r.url:
            raise NaverBlocked('네이버 로그인 월로 리다이렉트됨 (차단).')
        if r.status_code == 429:
            last = 429
            time.sleep(2 * (attempt + 1))   # 2s, 4s 백오프 후 재시도
            continue
        r.raise_for_status()
        return r.json()
    raise NaverBlocked(
        f'네이버가 접근을 차단했습니다 (HTTP {last}). 쿠키 워밍업·재시도에도 429 가 계속됩니다 — '
        '네이버 안티봇이 requests 호출을 막는 상태입니다. 브라우저 기반 수집(Playwright)이 필요할 수 있습니다.')


def get_channel_id(store_id, session=None):
    s = session or requests.Session()
    info = _get_json(s, f'{BASE}/i/v1/smart-stores?url={store_id}',
                     referer=f'{BASE}/{store_id}')
    chid = info.get('id')
    if not chid:
        raise RuntimeError(f'{store_id}: 채널 ID를 찾지 못함 — 응답 키: {list(info)[:20]}')
    return chid


def _parse_weight_grams(name):
    """상품명에서 중량(g)을 추출. 못 찾으면 None."""
    n = name.lower().replace(',', '')
    m = re.search(r'(\d+(?:\.\d+)?)\s*kg', n)
    if m:
        return float(m.group(1)) * 1000
    m = re.search(r'(\d+)\s*g(?![a-z])', n)
    if m:
        return float(m.group(1))
    return None


def normalize_price_1kg(name, price):
    """중량이 상품명에 명시된 경우 1kg 기준 가격으로 환산.

    중량 미표기 시 생두는 관례상 1kg 단위 판매가 많아 그대로 둔다.
    100g 미만(샘플)이나 환산 결과가 비정상(500원 미만)인 경우도 원가 유지.
    """
    grams = _parse_weight_grams(name)
    if not grams or grams == 1000 or grams < 100:
        return price
    per_kg = round(price * 1000 / grams / 10) * 10
    return per_kg if per_kg >= 500 else price


def fetch_products(store_id, category='ALL', session=None, page_size=40, delay=0.6):
    """스마트스토어 상품 전체 수집 → [{'name','price','url','is_soldout'}].

    category: 'ALL'(전체) 또는 진열 카테고리 ID(32자리 hex → DISPCATG로 조회)
    """
    s = session or requests.Session()
    warmup(s, store_id)                      # 쿠키 먼저 받기 (429 방지)
    referer = f'{BASE}/{store_id}'
    chid = get_channel_id(store_id, s)
    ctype = 'STDCATG' if category == 'ALL' else 'DISPCATG'
    items, page = [], 1
    while True:
        data = _get_json(
            s,
            f'{BASE}/i/v2/channels/{chid}/categories/{category}/products'
            f'?categorySearchType={ctype}&sortType=TOTALSALE&page={page}&pageSize={page_size}',
            referer=referer)
        prods = data.get('simpleProducts') or data.get('products') or []
        total = data.get('totalCount', 0)
        for p in prods:
            name = (p.get('name') or '').strip()
            if not name:
                continue
            benefits = p.get('benefitsView') or {}
            price = benefits.get('discountedSalePrice') or p.get('salePrice') or 0
            if not price:
                continue
            prod_no = p.get('id') or p.get('productNo')
            items.append({
                'name': name,
                'price': normalize_price_1kg(name, int(price)),
                'url': f'{BASE}/{store_id}/products/{prod_no}',
                'is_soldout': p.get('productStatusType') == 'OUTOFSTOCK',
            })
        print(f'  p{page} → {len(prods)}개 (누적 {len(items)}/{total})')
        if page * page_size >= total or not prods:
            break
        page += 1
        time.sleep(delay)
    # url 기준 중복 제거
    seen, unique = set(), []
    for it in items:
        if it['url'] not in seen:
            seen.add(it['url'])
            unique.append(it)
    return unique


def save(store_name, items, id_start):
    """common.to_products + update_json으로 저장 (ID 충돌 방지·안전장치 포함)."""
    import json
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import to_products, update_json

    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    kept = [p for p in data['products'] if p['store'] != store_name]
    existing_ids = {p['id'] for p in kept}
    update_json(store_name, to_products(items, store_name, id_start, existing_ids))
