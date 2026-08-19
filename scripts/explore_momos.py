#!/usr/bin/env python3
"""모모스커피(아임웹) 생두 상품이 실제로 몇 개이고 어디에 흩어져 있는지 확인.

여기까지 확정된 사실 (2026-08-19, GitHub Actions 실측):
 - momos.co.kr 이 cafe24 → **아임웹(imweb)** 으로 이전. 옛 URL 은 전부 404.
 - 상품 링크는 **서버 HTML 에 있다**: `/Product_GreenBean/?idx=<숫자>`
 - 카드 구조:
     div.shop-item._shop_item
       └ div.item-wrap
           └ a._fade_link.shop-item-thumb[href="/Product_GreenBean/?idx=7374"]
               └ div.item-overlay > div.item-pay > div
                   ├ h2               ← 상품명 ("[생두] …")
                   ├ p.pay            ← 가격 ("58,000원", 품절이면 "0원")
                   └ div.prod_icon.sold_out ← 품절 배지 (SOLDOUT)

**남은 문제**: `/Product_GreenBean` 에 고유 상품이 28개뿐인데 우리가 저장한 건 115개다.
`?page=2` 는 1페이지와 같은 결과를 준다. 둘 중 하나다.
  (가) 페이지네이션 방식이 달라서 나머지를 못 보고 있다
  (나) 생두가 여러 카테고리(B2B 등)로 흩어졌다 — 옛 cate_no=64 가 통합 카테고리였다
이 스크립트가 그 둘을 가른다. 28개로 그냥 교체하면 급감 가드에 걸리고,
가드를 우회해 밀어넣으면 상품 87개가 사라진다. 그래서 반드시 먼저 확인한다.
"""
from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = 'https://momos.co.kr'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}
IDX_RE = re.compile(r'[?&]idx=(\d+)')

# 생두가 있을 만한 페이지 — 사이트 자체 JS 주석에 나열된 쇼핑 슬러그에서 추렸다
PAGES = [
    '/Product_GreenBean',
    '/greenbean',
    '/ForBusiness_Shop',
    '/ForBusiness',
    '/b2b',
    '/ProductArchive',
    '/shop',
]


def idx_of(soup):
    return {IDX_RE.search(a['href']).group(1)
            for a in soup.find_all('a', href=True) if IDX_RE.search(a['href'])}


def bean_cards(soup):
    """[생두] 로 시작하는 상품만 센다 — 원두/굿즈가 섞인 페이지 구분용."""
    out = []
    for item in soup.select('div.shop-item, div._shop_item'):
        a = item.find('a', href=IDX_RE.search)
        h = item.find(['h2', 'h3'])
        if not a or not h:
            continue
        name = h.get_text(' ', strip=True)
        out.append((name, a['href']))
    return out


def main():
    print('=' * 60)
    print('=== 생두가 어느 페이지에 몇 개 있는가 ===')
    total = {}
    for path in PAGES:
        try:
            r = requests.get(BASE + path, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f'{path:22} 오류 {type(e).__name__}')
            continue
        if r.status_code != 200:
            print(f'{path:22} HTTP {r.status_code}')
            continue
        soup = BeautifulSoup(r.text, 'lxml')
        ids = idx_of(soup)
        cards = bean_cards(soup)
        beans = [c for c in cards if '[생두]' in c[0]]
        print(f'{path:22} HTTP 200 · idx {len(ids):3}개 · 카드 {len(cards):3}개 · [생두] {len(beans):3}개')
        total[path] = ids
        for n, h in beans[:3]:
            print(f'{"":24}예) {n[:55]}  {h}')

    allids = set().union(*total.values()) if total else set()
    print(f'\n→ 모든 페이지 합계 고유 idx: {len(allids)}개')

    # ── 페이지네이션 방식 찾기 ──────────────────────────────────────────
    print('\n' + '=' * 60)
    print('=== /Product_GreenBean 페이지네이션 조사 ===')
    r = requests.get(BASE + '/Product_GreenBean', headers=HEADERS, timeout=30)
    soup = BeautifulSoup(r.text, 'lxml')

    # 총 개수 표기 ("총 28개" 등)
    for m in re.finditer(r'(총\s*[\d,]+\s*개|[\d,]+\s*개의\s*상품|total[^<]{0,20}\d+)', r.text):
        print(f'   개수 표기: {m.group(0)[:60]}')

    # 페이징 UI
    for sel in ('.pagination', '._pagination', '.paging', '._paging', '[class*=page]'):
        els = soup.select(sel)
        if els:
            print(f'\n   {sel} → {len(els)}개')
            print('   ' + els[0].prettify()[:900].replace('\n', '\n   '))
            break
    else:
        print('   페이징 UI 없음 → 무한스크롤이거나 전량 표시')

    # 위젯 데이터 — 아임웹은 목록 AJAX 를 부를 때 이 값들을 쓴다
    print('\n   위젯 요소 속성:')
    for sel in ('div._widget_data', 'div.shop-content.widget', 'div.shop-grid'):
        el = soup.select_one(sel)
        if el:
            attrs = {k: (str(v)[:80]) for k, v in el.attrs.items()}
            print(f'      {sel}: {attrs}')

    # 페이지 안에서 목록 AJAX 호출에 쓰이는 파라미터 이름 찾기
    print('\n   get_shop_list_view 호출 문맥:')
    for m in re.finditer(r'.{250}get_shop_list_view.{350}', r.text, re.S):
        print('      …' + re.sub(r'\s+', ' ', m.group(0))[:560] + '…')
        break

    # ── 목록 AJAX 를 파라미터와 함께 실제로 호출 ────────────────────────
    print('\n' + '=' * 60)
    print('=== 목록 AJAX 파라미터 시도 ===')
    url = BASE + '/ajax/get_shop_list_view.cm'
    trials = [
        {'page': 2},
        {'page': 2, 'category': 'Product_GreenBean'},
        {'page': 2, 'unit_code': 'Product_GreenBean'},
        {'page': 2, 'code': 'Product_GreenBean'},
        {'page': 2, 'limit': 100},
        {'page': 1, 'limit': 200},
    ]
    for params in trials:
        try:
            rr = requests.post(url, headers={**HEADERS, 'X-Requested-With': 'XMLHttpRequest',
                                             'Referer': BASE + '/Product_GreenBean'},
                               data=params, timeout=30)
        except requests.RequestException as e:
            print(f'   {params} → 오류 {e}')
            continue
        ids = set(re.findall(r'[?&]idx=(\d+)', rr.text))
        print(f'   {params} → HTTP {rr.status_code} · {len(rr.content):,}바이트 · idx {len(ids)}개')
        if ids:
            print(f'      샘플: {sorted(ids)[:10]}')


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as e:
        print(f'✗ 네트워크 오류: {e}')
        sys.exit(1)
