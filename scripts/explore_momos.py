#!/usr/bin/env python3
"""모모스 스크래퍼 드라이런 + 두 가지 검증.

새 스크래퍼(`scrapers/scraper_momos.py`, 아임웹 대응)는 28개를 수집한다(기존 115개).
그대로 밀어넣기 전에 두 가지를 확인해야 한다.

① **28개가 진짜 전부인가** — 목록 AJAX 가 페이징을 실제로 하는지 검증한다.
   pagesize 를 작게 줘서 page1/page2 가 서로 다른 상품을 주면 페이징이 동작하는
   것이고, 그렇다면 pagesize=98 로 받은 28개가 전량이다.
   (페이징이 아예 안 먹는 거라면 28개는 '첫 화면 분량'일 뿐이다.)

② **28개 전부 품절로 잡힌 것이 사실인가** — 전 상품 100% 품절은 이 저장소가
   여러 번 겪은 '숨겨진 템플릿 배지' 오탐의 전형적 신호다(common.is_soldout_block
   주석 참고: cafe24 btnSoldout, godomall div.soldout 사례). 배지 요소의 style /
   부모 클래스를 실제로 찍어 확인한다.

Claude Code 세션은 쇼핑몰 접근이 403이라 GitHub Actions 에서 실행한다.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scrapers'))

import requests  # noqa: E402
from bs4 import BeautifulSoup  # noqa: E402

import scraper_momos as M  # noqa: E402
from common import HEADERS, to_products  # noqa: E402


def check_paging():
    print('=' * 60)
    print('① 목록 AJAX 페이징이 실제로 동작하는가')
    s = requests.Session()
    s.headers.update(HEADERS)
    html = s.get(M.BASE + M.LIST_PATH, timeout=25).text
    params = M.extract_ajax_params(html)
    if not params:
        print('   파라미터 추출 실패 — 확인 불가')
        return
    for size in ('6', '98'):
        seen = {}
        for page in (1, 2, 3):
            q = dict(params, page=page, pagesize=size)
            r = s.get(M.BASE + M.AJAX_PATH, params=q, timeout=25,
                      headers={'X-Requested-With': 'XMLHttpRequest',
                               'Referer': M.BASE + M.LIST_PATH})
            ids = sorted(set(re.findall(r'[?&]idx=(\d+)', (r.json() or {}).get('html') or '')))
            seen[page] = set(ids)
            print(f'   pagesize={size:>2} page={page} → {len(ids)}개 {ids[:6]}')
        p1, p2 = seen.get(1, set()), seen.get(2, set())
        if p2 - p1:
            print(f'   → pagesize={size}: page2 에 새 상품 {len(p2 - p1)}개 — 페이징 동작함')
        else:
            print(f'   → pagesize={size}: page2 가 page1 과 동일 — 페이징 무시됨')
        print(f'   → pagesize={size} 합계 고유: {len(p1 | p2 | seen.get(3, set()))}개')


def check_soldout():
    print('\n' + '=' * 60)
    print('② 품절 배지가 진짜인가 (전 상품 품절 = 템플릿 오탐 의심)')
    s = requests.Session()
    s.headers.update(HEADERS)
    soup = BeautifulSoup(s.get(M.BASE + M.LIST_PATH, timeout=25).text, 'html.parser')
    cards = soup.select('div.shop-item, div._shop_item')
    print(f'   카드 {len(cards)}개')
    with_badge = 0
    for i, card in enumerate(cards[:6]):
        h = card.find(['h2', 'h3'])
        name = h.get_text(' ', strip=True)[:44] if h else '?'
        badges = card.select('.prod_icon')
        info = []
        for b in badges:
            info.append(f'class={b.get("class")} style={b.get("style")!r} '
                        f'text={b.get_text(" ", strip=True)[:14]!r}')
        if card.select_one('.prod_icon.sold_out'):
            with_badge += 1
        print(f'   [{i}] {name:44} 배지 {len(badges)}개')
        for x in info:
            print(f'        {x}')
    total_badge = sum(1 for c in cards if c.select_one('.prod_icon.sold_out'))
    print(f'   → .prod_icon.sold_out 보유 카드: {total_badge}/{len(cards)}')
    if cards and total_badge == len(cards):
        print('   ⚠️ 전 상품이 배지를 가짐 = 숨겨진 템플릿. 이 신호는 신뢰할 수 없다.')

    # 상세 페이지에서 실제 구매 가능 여부 확인 (표본 3건)
    print('\n   상세 페이지 표본 확인:')
    links = [a['href'] for a in soup.find_all('a', href=True) if M.IDX_RE.search(a['href'])]
    for href in list(dict.fromkeys(links))[:3]:
        d = BeautifulSoup(s.get(M.BASE + href, timeout=25).text, 'html.parser')
        t = d.find('title')
        btn = d.select('.btn_buy, ._buy_btn, .item-buy, [class*=soldout], [class*=sold_out]')
        marks = [f'{b.get("class")}|{(b.get("style") or "")[:24]}' for b in btn[:4]]
        print(f'      {href} · {t.get_text(strip=True)[:44] if t else "-"}')
        print(f'         구매/품절 관련 요소: {marks}')


def dry_run():
    print('\n' + '=' * 60)
    print('③ 드라이런 (저장하지 않음)')
    items = M.scrape()
    with open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    old = [p for p in data['products'] if p['store'] == M.STORE]
    existing_ids = {p['id'] for p in data['products'] if p['store'] != M.STORE}
    products = to_products(items, M.STORE, M.ID_START, existing_ids)

    print(f'\n기존 {len(old)}개 → 신규 {len(products)}개 (급감 임계 {int(len(old) * 0.5)}개)')
    print(f'원산지: {dict(Counter(p["origin"] for p in products).most_common(12))}')
    print(f'가공방식: {dict(Counter(p["process"] for p in products).most_common())}')
    print(f'품절 표시: {sum(1 for p in products if p["is_soldout"])}개')
    print(f'상대경로 url: {sum(1 for p in products if not str(p["url"]).startswith("http"))}건 (0이어야 함)')


if __name__ == '__main__':
    check_paging()
    check_soldout()
    dry_run()
