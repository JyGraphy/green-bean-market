#!/usr/bin/env python3
"""모모스커피 신규 플랫폼(아임웹) 상품 카드 구조 확인 — 스크래퍼 재작성 마지막 조사.

밝혀진 것 (2026-08-19, GitHub Actions 실측):
 - momos.co.kr 이 cafe24 → **아임웹(imweb)** 으로 이전. 옛 URL 은 전부 404.
 - 생두 목록 페이지: `/Product_GreenBean`
 - **상품 링크는 서버 HTML 에 들어 있다**: `/Product_GreenBean/?idx=<숫자>`
   (아임웹은 shop_view 페이지의 슬러그를 바꿀 수 있어서, 앞서 `shop_view?idx=` 로만
    찾았을 때 0개로 보였던 것이다. 자바스크립트 렌더링이 아니었다.)
 - `/api/public/*` 는 실재하지 않는다 — 아임웹이 미지 경로에 SPA HTML 을 그대로 준다
   (응답 크기가 전부 1,875,630바이트로 동일한 것이 증거).

남은 질문: **상품 카드에서 이름·가격·품절을 어느 태그에서 읽는가**, 그리고 **페이지네이션**.
"""
from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

BASE = 'https://momos.co.kr'
LIST_PATH = '/Product_GreenBean'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}
IDX_RE = re.compile(r'[?&]idx=(\d+)')


def get(path):
    r = requests.get(BASE + path, headers=HEADERS, timeout=30)
    return r


def main():
    print('=' * 60)
    print(f'=== {BASE}{LIST_PATH} 상품 카드 구조 ===')
    r = get(LIST_PATH)
    print(f'HTTP {r.status_code} · {len(r.text):,}바이트')
    soup = BeautifulSoup(r.text, 'lxml')

    links = [a for a in soup.find_all('a', href=True) if IDX_RE.search(a['href'])]
    idxs = sorted({IDX_RE.search(a['href']).group(1) for a in links})
    print(f'idx 링크 {len(links)}개 · 고유 상품 {len(idxs)}개')
    print(f'idx 범위: {idxs[:5]} … {idxs[-5:]}' if idxs else 'idx 없음')

    if not links:
        print('✗ idx 링크가 없다 — 페이지 구조가 또 달라졌다.')
        return

    # 상품 카드 컨테이너 찾기 — 링크에서 위로 올라가며 클래스가 붙은 첫 조상
    a0 = links[0]
    print('\n--- 첫 링크의 조상 체인 (클래스) ---')
    node, chain = a0, []
    for _ in range(8):
        node = node.parent
        if node is None or node.name == '[document]':
            break
        chain.append(f'{node.name}.{".".join(node.get("class") or []) or "(무클래스)"}')
    print('   ' + ' ← '.join(chain))

    # 카드 전체 HTML 을 보여준다 — 이름/가격/품절이 어느 태그에 있는지 눈으로 확인
    card = a0
    for _ in range(6):
        if card.parent is None:
            break
        card = card.parent
        cls = ' '.join(card.get('class') or [])
        if any(k in cls for k in ('item', 'goods', 'prod', 'list')):
            break
    print('\n--- 카드 HTML (앞 2500자) ---')
    print(card.prettify()[:2500])

    print('\n--- 카드 텍스트 ---')
    print(re.sub(r'\n\s*\n+', '\n', card.get_text('\n', strip=True))[:600])

    # 페이지네이션 — 전체 상품 수를 확인해야 급감 가드에 걸리지 않는다
    print('\n' + '=' * 60)
    print('=== 페이지네이션 확인 ===')
    seen_first = set(idxs)
    for page in (2, 3):
        rr = get(f'{LIST_PATH}?page={page}')
        s2 = BeautifulSoup(rr.text, 'lxml')
        ix = sorted({IDX_RE.search(a['href']).group(1)
                     for a in s2.find_all('a', href=True) if IDX_RE.search(a['href'])})
        new = set(ix) - seen_first
        print(f'?page={page}: HTTP {rr.status_code} · 고유 {len(ix)}개 · 1페이지에 없던 것 {len(new)}개')
        seen_first |= set(ix)
    print(f'→ page 파라미터로 늘어난 총 고유 상품: {len(seen_first)}개')
    print('   (1페이지와 동일하면 페이지네이션이 없거나 다른 방식이다)')

    # 상세 페이지 한 건 — 가격·품절 표기 확인용
    print('\n' + '=' * 60)
    print(f'=== 상세 페이지 확인: {LIST_PATH}/?idx={idxs[0]} ===')
    rd = get(f'{LIST_PATH}/?idx={idxs[0]}')
    sd = BeautifulSoup(rd.text, 'lxml')
    print(f'HTTP {rd.status_code} · {len(rd.text):,}바이트')
    print(f'title: {sd.title.get_text(strip=True) if sd.title else "-"}')
    og = sd.find('meta', property='og:title')
    print(f'og:title: {og.get("content") if og else "-"}')
    for sel in ('.item-price', '.item_price', '.price', '.shop-item-price', '[class*=price]'):
        el = sd.select(sel)
        if el:
            print(f'   {sel} → {[e.get_text(" ", strip=True)[:60] for e in el[:3]]}')
            break


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as e:
        print(f'✗ 네트워크 오류: {e}')
        sys.exit(1)
