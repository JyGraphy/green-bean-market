"""
모모스커피 생두 스크래퍼
URL: https://momos.co.kr/Product_GreenBean
플랫폼: 아임웹(imweb) — 2026년 cafe24에서 이전

**2026-08-19 전면 재작성 배경**
모모스가 cafe24 → 아임웹으로 옮기면서 옛 상품 URL
`/product/<슬러그>/<id>/category/64/...` 가 전부 404가 됐다(저장된 115개 100% dead).
안전장치는 정상 작동했다 — 스크래퍼가 0개를 수집하자 guard_store_replacement 가
덮어쓰기를 막았고, check_links 는 dead 비율 100%를 "URL 구조 변경 의심"으로 보고
삭제를 보류했다. 다만 그 뒤 아무도 후속 조치를 안 해 죽은 링크가 남아 있었다.

**새 구조 (GitHub Actions 실측)**
 - 상품 URL: `/Product_GreenBean/?idx=<숫자>`  ← 서버 HTML 에 그대로 있다
 - 카드 구조:
     div.shop-item._shop_item
       └ div.item-wrap
           └ a.shop-item-thumb[href="/Product_GreenBean/?idx=7374"]
               └ div.item-overlay > div.item-pay > div
                   ├ h2                      상품명 ("[생두] …")
                   ├ p.pay                   가격 ("58,000원", 품절이면 "0원")
                   └ div.prod_icon.sold_out  품절 배지
 - 첫 페이지는 일부만 오고 '더보기'가 목록 AJAX 로 나머지를 받는다.
   호출 규격은 페이지 인라인 스크립트에 그대로 들어 있다:
     GET /ajax/get_shop_list_view.cm
       ?page=N&pagesize=98&category=<코드>&sort=recent
        &menu_url=/Product_GreenBean/&widget_code=<코드>
   → {"msg":"SUCCESS","html":"<카드 HTML>"}
   category/widget_code 는 하드코딩하지 않고 **매번 페이지에서 추출**한다.
   모모스가 위젯을 다시 만들면 코드가 바뀌는데, 박아두면 그때 조용히 0개가 된다.
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
AJAX_PATH = '/ajax/get_shop_list_view.cm'
ID_START = 101          # 모모스 ID 구간 시작 (alloc_ids 가 충돌은 알아서 피한다)
MAX_PAGES = 30          # 폭주 방지
IDX_RE = re.compile(r'[?&]idx=(\d+)')


def fetch_html(session, path, **kw):
    r = session.get(BASE + path, timeout=25, **kw)
    r.raise_for_status()
    return r.text


def parse_cards(html):
    """상품 카드에서 이름·가격·링크·품절을 뽑는다.

    목록 페이지와 AJAX 응답 조각이 같은 마크업이라 둘 다 이 함수로 처리한다.
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for card in soup.select('div.shop-item, div._shop_item'):
        a = card.find('a', href=lambda h: h and IDX_RE.search(h))
        if not a:
            continue
        h = card.find(['h2', 'h3'])
        if not h:
            continue
        name = h.get_text(' ', strip=True)
        if not name:
            continue

        # 가격 — p.pay 가 표준. 품절이면 "0원"으로 온다.
        price = 0
        pay = card.select_one('p.pay, .item-pay p, .pay')
        if pay:
            m = re.search(r'([\d,]+)\s*원', pay.get_text(' ', strip=True))
            if m:
                price = int(m.group(1).replace(',', ''))

        # 품절 — 품절 상품에만 렌더되는 배지. 클래스 템플릿 오탐이 없는지 실측 확인함.
        soldout = card.select_one('.prod_icon.sold_out, .prod_icon.soldout') is not None

        items.append({
            'name': name,
            'price': price,
            'url': abs_url(BASE, a['href']),
            'is_soldout': soldout,
        })
    return items


def extract_ajax_params(html):
    """페이지 인라인 스크립트에서 목록 AJAX 호출 파라미터를 그대로 읽어온다.

    하드코딩하지 않는 이유: category/widget_code 는 아임웹이 위젯마다 발급하는
    값이라 모모스가 위젯을 다시 만들면 바뀐다. 박아두면 그날부터 조용히 0개가 되고,
    가드가 막아주긴 해도 원인 파악에 또 며칠이 걸린다.
    """
    m = re.search(r'get_shop_list_view\.cm.{0,600}', html, re.S)
    if not m:
        return None
    blob = m.group(0)
    params = {}
    for key in ('pagesize', 'category', 'sort', 'menu_url', 'widget_code'):
        km = re.search(r"['\"]" + key + r"['\"]\s*:\s*['\"]([^'\"]+)['\"]", blob)
        if km:
            params[key] = km.group(1)
        else:  # pagesize 처럼 따옴표 없는 숫자
            km = re.search(r"['\"]" + key + r"['\"]\s*:\s*(\d+)", blob)
            if km:
                params[key] = km.group(1)
    if 'category' not in params or 'widget_code' not in params:
        return None
    params.setdefault('pagesize', '98')
    params.setdefault('sort', 'recent')
    params.setdefault('menu_url', LIST_PATH + '/')
    return params


def scrape():
    print(f'[{STORE}] 스크래핑 시작...')
    session = requests.Session()
    session.headers.update(HEADERS)

    html = fetch_html(session, LIST_PATH)
    items = parse_cards(html)
    print(f'  1페이지: {len(items)}개')

    params = extract_ajax_params(html)
    if not params:
        # 파라미터를 못 찾아도 1페이지 분은 살린다. 급감이면 가드가 막는다.
        print('  ⚠️ 목록 AJAX 파라미터를 못 찾았습니다 — 1페이지만 수집합니다.')
    else:
        print(f'  목록 AJAX 파라미터: category={params["category"]} '
              f'widget_code={params["widget_code"]} pagesize={params["pagesize"]}')
        seen = {it['url'] for it in items}
        for page in range(2, MAX_PAGES + 1):
            q = dict(params, page=page)
            try:
                r = session.get(BASE + AJAX_PATH, params=q, timeout=25,
                                headers={'X-Requested-With': 'XMLHttpRequest',
                                         'Referer': BASE + LIST_PATH})
                data = r.json()
            except Exception as e:
                print(f'  페이지 {page} 실패: {type(e).__name__}: {e}')
                break
            if data.get('msg') != 'SUCCESS':
                print(f'  페이지 {page}: msg={data.get("msg")} — 종료')
                break
            page_items = parse_cards(data.get('html') or '')
            fresh = [it for it in page_items if it['url'] not in seen]
            print(f'  페이지 {page}: {len(page_items)}개 (신규 {len(fresh)}개)')
            if not fresh:
                break
            seen.update(it['url'] for it in fresh)
            items.extend(fresh)
            time.sleep(0.5)

    # 생두만 남긴다 — 목록에 원두/굿즈가 섞여 와도 [생두] 표기로 가른다.
    beans = [it for it in items if '[생두]' in it['name']]
    print(f'  전체 {len(items)}개 중 [생두] {len(beans)}개')
    if not beans and items:
        # [생두] 표기 규칙이 바뀐 경우까지 통째로 버리지는 않는다.
        print('  ⚠️ [생두] 표기가 하나도 없습니다 — 표기 규칙 변경 가능성. 전체를 사용합니다.')
        beans = items

    # 접두어 제거 (clean_name 은 상태 라벨만 떼므로 [생두]는 여기서 처리)
    for it in beans:
        it['name'] = re.sub(r'\[\s*생두\s*\]\s*', '', it['name']).strip()

    # 가격도 없고 품절도 아니면 카드가 덜 그려진 것 → 제외
    beans = [it for it in beans if it['price'] > 0 or it['is_soldout']]

    soldout = sum(1 for it in beans if it['is_soldout'])
    print(f'[{STORE}] 총 {len(beans)}개 수집 (품절 {soldout}개)')
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
