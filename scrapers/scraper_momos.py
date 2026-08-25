"""
모모스커피 생두 스크래퍼
URL: https://momos.co.kr/greenbean (랜딩) / https://momos.co.kr/Product_GreenBean (구 그리드)
플랫폼: 아임웹(imweb) — 2026년 cafe24에서 이전

**2026-08-25 전면 재작성 — 전체 카탈로그에서 [생두] 필터**
그동안은 /Product_GreenBean 위젯의 category/widget_code 로 목록 AJAX 를 호출했다.
그런데 모모스가 /greenbean 랜딩을 새로 내면서 위젯을 다시 만들었고, 그 위젯 category
(`s20260722c87183a44b18a`)는 드립백 14개만 돌려준다. 정작 볼리비아 등 신상 생두는
다른 category 에 흩어져 있어서, 위젯 하나만 보면 대부분을 놓친다(2026-08-25 실측:
위젯 28개 vs 실제 생두 74개).

**해결: category 를 비워서 전체 상품을 받는다.**
목록 AJAX `GET /ajax/get_shop_list_view.cm?category=&page=N&pagesize=K&sort=recent` 는
category 가 비면 **전체 카탈로그**를 돌려준다(2026-08-25 실측 214개). 여기서 이름에
`[생두]` 가 든 것만 생두로 추린다. 이 방식은 아임웹이 위젯을 다시 만들어도 영향받지
않는다 — widget_code/category 에 의존하지 않기 때문이다.

**카드 구조 (AJAX 응답 조각)**
    div.shop-item._shop_item[data-product-properties='{...json...}']
      └ a.shop-item-thumb[href="/Product_GreenBean/?idx=<숫자>"]
          └ h2 상품명, p.pay 가격
`data-product-properties` JSON 에 name/price/idx 가 그대로 들어 있어 이걸 1차 소스로,
마크업(h2/p.pay/a[href])을 보강용으로 쓴다.

**품절 감지 (2026-08-25 도입)**
목록의 `.prod_icon.sold_out` 은 전 카드에 렌더되는 숨은 템플릿이라 신뢰 불가.
대신 **상세페이지 서버 HTML 의 "is_soldout":true/false** 가 상품별 권위 신호다
(JS 없이 나온다). add_soldout() 이 수집된 생두마다 상세페이지를 받아 채운다.
"""
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HEADERS, abs_url, to_products, update_json

STORE = '모모스커피'
BASE = 'https://momos.co.kr'
LIST_PATH = '/Product_GreenBean'
LANDING = '/greenbean'
AJAX_PATH = '/ajax/get_shop_list_view.cm'
ID_START = 101          # 모모스 ID 구간 시작 (alloc_ids 가 충돌은 알아서 피한다)
MAX_PAGES = 40          # 폭주 방지 (전체 카탈로그 ~200개 / pagesize)
PAGE_SIZE = 100         # 전체를 몇 번의 요청으로 훑는다
IDX_RE = re.compile(r'[?&]idx=(\d+)')
# 상세페이지 서버 HTML 에 들어 있는 권위 있는 품절 플래그 (2026-08-25 실측).
SOLDOUT_RE = re.compile(r'"is_soldout"\s*:\s*(true|false)')


def fetch_soldout(session, url):
    """상세페이지에서 상품별 실제 품절 여부를 읽는다. 실패 시 None(모름)."""
    try:
        r = session.get(url, timeout=25)
        m = SOLDOUT_RE.search(r.text)
        if m:
            return m.group(1) == 'true'
    except requests.RequestException:
        pass
    return None


def add_soldout(session, beans):
    """수집된 생두마다 상세페이지를 받아 품절 여부를 채운다.

    모모스는 상시 품절이 많은데 목록엔 신뢰할 품절 신호가 없어, 상품별 상세페이지의
    "is_soldout" 을 권위 신호로 쓴다.
    """
    unknown = 0
    for it in beans:
        so = fetch_soldout(session, it['url'])
        if so is None:
            unknown += 1
        else:
            it['is_soldout'] = so
        time.sleep(0.3)
    sold = sum(1 for it in beans if it.get('is_soldout'))
    print(f'  품절 확인: {sold}개 품절 / {len(beans)}개'
          + (f' (판독 실패 {unknown}개는 모름 처리)' if unknown else ''))


def parse_cards(html):
    """상품 카드에서 이름·가격·링크를 뽑는다.

    data-product-properties JSON(name/price/idx)을 1차 소스로, 마크업을 보강용으로
    쓴다. 목록 페이지와 AJAX 응답 조각이 같은 마크업이라 둘 다 이 함수로 처리한다.
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for card in soup.select('div._shop_item, div.shop-item'):
        name, price, idx = '', None, None

        raw = card.get('data-product-properties')
        if raw:
            try:
                p = json.loads(raw)
                name = (p.get('name') or '').strip()
                price = int(p.get('price') or 0)
                idx = p.get('idx')
            except (ValueError, TypeError):
                pass

        # 상세 링크 — 아임웹이 실제로 링크하는 URL 우선
        a = card.find('a', href=lambda h: h and IDX_RE.search(h))
        href = a['href'] if a else None

        # data-product-properties 가 없으면 마크업에서 보강
        if not name:
            h = card.find(['h2', 'h3'])
            name = h.get_text(' ', strip=True) if h else ''
        if not name:
            continue
        if not price:
            pay = card.select_one('p.pay, .item-pay p, .pay')
            if pay:
                m = re.search(r'([\d,]+)\s*원', pay.get_text(' ', strip=True))
                if m:
                    price = int(m.group(1).replace(',', ''))

        # URL 확정: href 우선, 없으면 idx 로 구성(idx 는 아임웹 전역 상품 id)
        if href:
            url = abs_url(BASE, href)
        elif idx:
            url = f'{BASE}{LIST_PATH}/?idx={idx}'
        else:
            continue

        items.append({
            'name': name,
            'price': price or 0,
            'url': url,
            'is_soldout': False,   # add_soldout() 에서 상세페이지 기준으로 덮어씀
        })
    return items


def fetch_all_products(session):
    """category 를 비워 전체 카탈로그를 페이지네이션으로 받는다.

    category='' → 전체 상품(2026-08-25 실측 214개). 위젯 category/widget_code 에
    의존하지 않아 모모스가 위젯을 다시 만들어도 영향받지 않는다.
    """
    items, seen = [], set()
    for page in range(1, MAX_PAGES + 1):
        q = {'category': '', 'page': page, 'pagesize': PAGE_SIZE, 'sort': 'recent'}
        try:
            r = session.get(BASE + AJAX_PATH, params=q, timeout=25,
                            headers={'X-Requested-With': 'XMLHttpRequest',
                                     'Accept': 'application/json',
                                     'Referer': BASE + LANDING})
            data = r.json()
        except Exception as e:
            print(f'  페이지 {page} 실패: {type(e).__name__}: {e}')
            break
        msg = data.get('msg')
        if msg and msg != 'SUCCESS':
            print(f'  페이지 {page}: msg={msg} — 종료')
            break
        page_items = parse_cards(data.get('html') or '')
        fresh = [it for it in page_items if it['url'] not in seen]
        print(f'  페이지 {page}: {len(page_items)}개 (신규 {len(fresh)}개)')
        if not fresh:
            break
        seen.update(it['url'] for it in fresh)
        items.extend(fresh)
        time.sleep(0.4)
    return items


def scrape():
    print(f'[{STORE}] 스크래핑 시작...')
    session = requests.Session()
    session.headers.update(HEADERS)

    items = fetch_all_products(session)

    if not items:
        # 전체 조회가 빈손이면 랜딩/그리드 페이지에 그려진 첫 화면 분량만 건진다.
        # 그것도 급감이면 가드가 교체를 막아 기존 데이터가 보존된다.
        for path in (LANDING, LIST_PATH):
            try:
                html = session.get(BASE + path, timeout=25).text
            except requests.RequestException:
                continue
            items = parse_cards(html)
            if items:
                print(f'  ⚠️ 전체 AJAX 실패 — {path} 페이지 분 {len(items)}개만 수집')
                break

    beans = finalize(items)
    add_soldout(session, beans)
    return beans


def finalize(items):
    """수집 결과를 생두만 남기고 정리한다."""
    # 생두만 남긴다 — 전체 카탈로그에 원두/드립백/굿즈가 섞여 오므로 [생두] 표기로 가른다.
    # ('[개인결제창-생두]' 같은 결제창은 '[생두]' 정확 표기가 아니라 자동 제외된다)
    beans = [it for it in items if '[생두]' in it['name']]
    print(f'  전체 {len(items)}개 중 [생두] {len(beans)}개')

    # 접두어 제거 (clean_name 은 상태 라벨만 떼므로 [생두]는 여기서 처리)
    for it in beans:
        it['name'] = re.sub(r'\[\s*생두\s*\]\s*', '', it['name']).strip()

    # 가격 없는 항목 제외 — 우리 사이트는 가격 비교가 목적이라 0원은 비교 대상이
    # 아니다. 실제로 걸리는 건 커핑 행사(예: "2026 Panama Business Cupping") 같은
    # 비판매 항목이다.
    dropped = [it for it in beans if it['price'] <= 0]
    beans = [it for it in beans if it['price'] > 0]
    if dropped:
        print(f'  가격 없는 항목 {len(dropped)}개 제외: '
              f'{[it["name"][:30] for it in dropped[:3]]}')

    print(f'[{STORE}] 총 {len(beans)}개 수집')
    return beans


if __name__ == '__main__':
    items = scrape()

    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    existing_ids = {p['id'] for p in data['products'] if p['store'] != STORE}

    products = to_products(items, STORE, ID_START, existing_ids)
    # update_json 안에서 guard_store_replacement 가 빈/급감 결과를 막는다.
    update_json(STORE, products)
