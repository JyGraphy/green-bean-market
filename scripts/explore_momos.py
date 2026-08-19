#!/usr/bin/env python3
"""모모스커피 신규 플랫폼 구조 탐색 — 스크래퍼 재작성을 위한 1회성 조사 도구.

배경: momos.co.kr 이 cafe24(`/product/<슬러그>/<id>/category/...`)에서
다른 솔루션(`/shop_view?idx=<숫자>`)으로 이전했다. 그 결과
 - 저장된 상품 URL 115개가 전부 404
 - 스크래퍼는 상품을 0개 추출 → guard_store_replacement 가 교체를 막아
   죽은 데이터가 그대로 보존됨 (안전장치는 정상 작동)

이 스크립트는 새 구조에서 스크래퍼를 쓰는 데 필요한 것만 뽑아 출력한다:
카테고리 목록, 상품 목록 페이지, 상품 카드의 실제 마크업, 페이지네이션 방식.

GitHub Actions 에서 실행한다(세션은 쇼핑몰 접근이 403).
"""
from __future__ import annotations

import re
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = 'https://momos.co.kr'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}


def get(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    return r.status_code, r.text, r.url


def main():
    print(f'=== ① 첫 화면 구조: {BASE} ===')
    code, html, final = get(BASE)
    print(f'HTTP {code} · 최종 {final} · {len(html):,}바이트')
    soup = BeautifulSoup(html, 'lxml')
    print(f'제목: {soup.title.get_text(strip=True) if soup.title else "-"}')

    # 내비게이션 링크 — 생두 카테고리를 찾는다
    print('\n내비게이션/카테고리 후보 (텍스트 → 링크):')
    seen = set()
    for a in soup.find_all('a'):
        txt = a.get_text(' ', strip=True)
        h = a.get('href', '')
        if not h or h.startswith(('#', 'javascript:')):
            continue
        if not txt or len(txt) > 30:
            continue
        key = (txt, h)
        if key in seen:
            continue
        seen.add(key)
        if any(k in txt for k in ('생두', 'Green', 'GREEN', 'Coffee', 'COFFEE', '원두')) \
           or re.search(r'(Ethiopia|Colombia|Columbia|CostaRica|Brazil|Kenya)', h, re.I):
            print(f'   {txt[:28]:<28} → {h}')

    # ② 생두로 보이는 카테고리 페이지 조사
    print('\n=== ② 상품 목록 페이지 조사 ===')
    candidates = []
    for a in soup.find_all('a'):
        h = a.get('href', '')
        txt = a.get_text(' ', strip=True)
        if h and ('생두' in txt or 'green' in h.lower()):
            candidates.append(urljoin(BASE, h))
    # 후보가 없으면 국가 카테고리라도 본다
    if not candidates:
        for a in soup.find_all('a'):
            h = a.get('href', '')
            if re.fullmatch(r'/(Ethiopia|Columbia|Colombia|CostaRica|Brazil|Kenya)', h or ''):
                candidates.append(urljoin(BASE, h))
    candidates = list(dict.fromkeys(candidates))[:3]
    print(f'조사할 후보: {candidates}')

    for cat in candidates:
        print(f'\n--- {cat} ---')
        c, h2, _ = get(cat)
        if c != 200:
            print(f'   HTTP {c} — 건너뜀')
            continue
        s2 = BeautifulSoup(h2, 'lxml')
        views = [a.get('href') for a in s2.select('a[href*="shop_view"]')]
        views = list(dict.fromkeys(v for v in views if v))
        print(f'   HTTP 200 · {len(h2):,}바이트 · shop_view 링크 {len(views)}개')
        for v in views[:3]:
            print(f'      {v}')
        # 상품 카드 마크업 샘플 — 이름/가격 셀렉터를 정하기 위해 필요
        if views:
            a0 = s2.select_one('a[href*="shop_view"]')
            card = a0
            for _ in range(4):           # 카드 컨테이너까지 거슬러 올라간다
                if card.parent and card.parent.name not in ('body', 'html', '[document]'):
                    card = card.parent
            sample = re.sub(r'\s+', ' ', card.prettify())[:1400]
            print(f'\n   [상품 카드 마크업 샘플]\n   {sample}\n')
        # 페이지네이션 단서
        pg = [a.get('href') for a in s2.find_all('a')
              if a.get('href') and re.search(r'page|pageNum|p=', a.get('href'))]
        if pg:
            print(f'   페이지네이션 후보: {list(dict.fromkeys(pg))[:5]}')

    # ③ 상품 상세 페이지 한 건
    print('\n=== ③ 상품 상세 페이지 확인 ===')
    for cat in candidates:
        c, h2, _ = get(cat)
        if c != 200:
            continue
        s2 = BeautifulSoup(h2, 'lxml')
        a0 = s2.select_one('a[href*="shop_view"]')
        if not a0:
            continue
        url = urljoin(BASE, a0.get('href'))
        c3, h3, _ = get(url)
        s3 = BeautifulSoup(h3, 'lxml')
        print(f'   {url}')
        print(f'   HTTP {c3} · 제목: {s3.title.get_text(strip=True) if s3.title else "-"}')
        prices = re.findall(r'[\d,]{4,}\s*원', h3)[:5]
        print(f'   페이지에서 발견한 가격 형태: {prices}')
        break


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as e:
        print(f'✗ 네트워크 오류: {e}')
        sys.exit(1)
