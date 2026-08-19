#!/usr/bin/env python3
"""모모스커피 신규 플랫폼 구조 탐색 — 스크래퍼 재작성용 조사 도구.

지금까지 밝혀진 것 (2026-08-19, GitHub Actions 실측):
 - momos.co.kr 이 cafe24 → **아임웹(imweb)** 으로 이전
 - 옛 URL `/product/<슬러그>/<id>/category/64/...` 는 전부 404
 - 생두는 imweb 기본 쇼핑이 아니라 **자체 앱**(momos-dev.twomos.com)으로 운영
 - 생두 페이지 `/greenbean`, `/Product_GreenBean` 은 자바스크립트로 목록을 그린다
 - 그 목록이 쓰는 **공개 API**가 HTML 안에 노출돼 있다:
     /api/public/green-beans   /api/public/products
     /api/public/origins       /api/public/filters
   (imweb 기본 목록 AJAX `/ajax/get_shop_list_view.cm` 도 존재)

이 스크립트는 그 API들의 **응답 형태**를 확인한다 — 어떤 필드에 상품명·가격·
원산지·상세링크가 들어 있는지 알아야 스크래퍼를 쓸 수 있다.
"""
from __future__ import annotations

import json
import re
import sys

import requests

BASE = 'https://momos.co.kr'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Referer': BASE + '/Product_GreenBean',
}

# 목록 API 후보. 페이지네이션 파라미터가 필요할 수 있어 몇 가지 변형을 함께 시도한다.
CANDIDATES = [
    '/api/public/green-beans',
    '/api/public/green-beans?page=1&size=100',
    '/api/public/green-beans?page=1&limit=100',
    '/api/public/products',
    '/api/public/products?page=1&size=100',
    '/api/public/origins',
    '/api/public/filters',
]


def brief(obj, depth=0, max_depth=3):
    """JSON 구조를 짧게 요약해 출력한다 (전체를 쏟아내면 로그가 못 쓴다)."""
    pad = '  ' * depth
    if isinstance(obj, dict):
        for k, v in list(obj.items())[:25]:
            if isinstance(v, (dict, list)) and depth < max_depth:
                kind = 'dict' if isinstance(v, dict) else f'list[{len(v)}]'
                print(f'{pad}{k}: {kind}')
                brief(v, depth + 1, max_depth)
            else:
                s = str(v)
                print(f'{pad}{k}: {s[:90]}')
    elif isinstance(obj, list):
        if not obj:
            print(f'{pad}(빈 배열)')
            return
        print(f'{pad}[0]:')
        brief(obj[0], depth + 1, max_depth)


def probe_api():
    print('=' * 60)
    print('=== 공개 API 응답 확인 ===')
    for path in CANDIDATES:
        url = BASE + path
        print(f'\n--- {url} ---')
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
        except requests.RequestException as e:
            print(f'   오류: {type(e).__name__}: {e}')
            continue
        ctype = r.headers.get('content-type', '')
        print(f'   HTTP {r.status_code} · {ctype} · {len(r.content):,}바이트')
        if r.status_code != 200:
            print(f'   본문 앞부분: {r.text[:200]!r}')
            continue
        if 'json' not in ctype.lower():
            print(f'   JSON 아님. 앞부분: {r.text[:200]!r}')
            continue
        try:
            data = r.json()
        except Exception as e:
            print(f'   JSON 파싱 실패: {e}')
            continue
        brief(data)
        # 상품 배열을 찾으면 첫 항목 전체를 그대로 보여준다 (필드명을 정확히 알아야 한다)
        arr = None
        if isinstance(data, list):
            arr = data
        elif isinstance(data, dict):
            for key in ('data', 'items', 'list', 'results', 'content', 'products', 'greenBeans'):
                v = data.get(key)
                if isinstance(v, list) and v:
                    arr = v
                    break
                if isinstance(v, dict):
                    for k2 in ('items', 'list', 'content', 'results'):
                        if isinstance(v.get(k2), list) and v[k2]:
                            arr = v[k2]
                            break
                if arr:
                    break
        if arr:
            print(f'\n   ▶ 상품 배열 {len(arr)}건 · 첫 항목 원본:')
            print('   ' + json.dumps(arr[0], ensure_ascii=False, indent=2)[:2500].replace('\n', '\n   '))


def probe_imweb_ajax():
    """imweb 기본 목록 AJAX — 생두가 여기 있을 수도 있어 함께 확인한다."""
    print('\n' + '=' * 60)
    print('=== imweb 목록 AJAX 확인 ===')
    url = BASE + '/ajax/get_shop_list_view.cm'
    for method in ('get', 'post'):
        try:
            fn = requests.get if method == 'get' else requests.post
            r = fn(url, headers=HEADERS, timeout=25,
                   **({'params': {'page': 1}} if method == 'get' else {'data': {'page': 1}}))
        except requests.RequestException as e:
            print(f'   {method.upper()} 오류: {e}')
            continue
        print(f'   {method.upper()} HTTP {r.status_code} · {len(r.content):,}바이트')
        idxs = sorted(set(re.findall(r'shop_view/?\?idx=(\d+)', r.text)))
        print(f'      shop_view idx {len(idxs)}개 {idxs[:10]}')
        print(f'      앞부분: {r.text[:200]!r}')


def probe_detail_link():
    """상품 상세 링크 형식 확인 — 우리가 저장할 url 이 이것이다."""
    print('\n' + '=' * 60)
    print('=== 생두 페이지 원문에서 상세 링크 힌트 찾기 ===')
    r = requests.get(BASE + '/Product_GreenBean',
                     headers={**HEADERS, 'Accept': 'text/html'}, timeout=25)
    h = r.text
    for pat, label in [
        (r'["\'](/[Pp]roduct_?[Gg]reen[Bb]ean[^"\']*)["\']', '생두 경로'),
        (r'["\']([^"\']*green-?beans?/[^"\']*)["\']', 'green-bean 경로'),
        (r'["\']([^"\']*detail[^"\']*)["\']', 'detail 경로'),
        (r'\{\{[^}]{0,60}\}\}', '템플릿 자리표시자'),
    ]:
        found = sorted(set(re.findall(pat, h)))[:12]
        print(f'   {label}: {found}')


if __name__ == '__main__':
    try:
        probe_api()
        probe_imweb_ajax()
        probe_detail_link()
    except requests.RequestException as e:
        print(f'✗ 네트워크 오류: {e}')
        sys.exit(1)
