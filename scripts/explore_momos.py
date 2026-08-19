#!/usr/bin/env python3
"""모모스커피 신규 플랫폼 구조 탐색 — 스크래퍼 재작성용 조사 도구.

지금까지 밝혀진 것 (2026-08-19, GitHub Actions 실측):
 - momos.co.kr 이 cafe24 → 다른 솔루션으로 이전
 - 옛 URL `/product/<슬러그>/<id>/category/64/...` 는 전부 404
 - 새 상품 URL 형식: `/shop_view/?idx=<숫자>`
 - 생두 카테고리: `/greenbean`, `/Product_GreenBean`
 - 그런데 카테고리 페이지(1.3MB)에 <a> 기반 상품 링크가 0개
   → 상품 목록을 자바스크립트로 그리는 것으로 보인다

이 스크립트는 그 다음 질문에 답한다:
 "상품 데이터가 HTML 안에 (JSON 등으로) 들어 있는가, 아니면 별도 API를 호출하는가?"
전자면 requests 만으로 계속 긁을 수 있고, 후자면 그 API를 직접 호출하면 된다.
"""
from __future__ import annotations

import json
import re
import sys

import requests

BASE = 'https://momos.co.kr'
CATS = ['/greenbean', '/Product_GreenBean']
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}


def main():
    for cat in CATS:
        url = BASE + cat
        print(f'\n{"=" * 60}\n=== {url} ===')
        r = requests.get(url, headers=HEADERS, timeout=25)
        html = r.text
        print(f'HTTP {r.status_code} · {len(html):,}바이트')

        # ① 원문에 shop_view 가 몇 번 나오는가 (a 태그가 아니어도)
        hits = re.findall(r'shop_view/?\?idx=(\d+)', html)
        print(f'\n① 원문 내 shop_view idx 등장: {len(hits)}회 · 고유 {len(set(hits))}개')
        if hits:
            print(f'   샘플 idx: {sorted(set(hits))[:12]}')
            # 그 주변 문맥을 보면 어떤 구조에 들어 있는지 알 수 있다
            m = re.search(r'.{220}shop_view/?\?idx=\d+.{220}', html, re.S)
            if m:
                ctx = re.sub(r'\s+', ' ', m.group(0))
                print(f'   문맥: …{ctx}…')

        # ② 상품명으로 보이는 문자열이 원문에 있는가
        for kw in ('생두', 'Ethiopia', 'Colombia', '원'):
            print(f'   "{kw}" 등장 {html.count(kw)}회')

        # ③ 인라인 JSON 후보 — 상품 배열이 통째로 박혀 있는 경우
        print('\n② 인라인 JSON 후보')
        found_json = False
        for m in re.finditer(r'(?:var|let|const)\s+(\w+)\s*=\s*(\[\{.{200,}?\}\])\s*[;\n]', html, re.S):
            name, blob = m.group(1), m.group(2)
            try:
                data = json.loads(blob)
            except Exception:
                continue
            if isinstance(data, list) and data and isinstance(data[0], dict):
                print(f'   ✓ {name} — {len(data)}건, 키: {list(data[0])[:12]}')
                found_json = True
        # __NUXT__ / __NEXT_DATA__ 같은 프레임워크 상태
        for key in ('__NUXT__', '__NEXT_DATA__', 'window.__INITIAL_STATE__'):
            if key in html:
                print(f'   ✓ {key} 발견 — 프레임워크 상태에 상품이 들어 있을 수 있음')
                found_json = True
        if not found_json:
            print('   (없음)')

        # ④ JS가 호출할 만한 API 엔드포인트
        print('\n③ API 엔드포인트 후보')
        apis = set()
        for m in re.finditer(r'["\'](/[\w/\-.]*(?:api|ajax|list|product|goods|shop)[\w/\-.]*)["\']',
                             html, re.I):
            p = m.group(1)
            if len(p) > 6 and not p.endswith(('.css', '.js', '.png', '.jpg', '.svg', '.gif', '.webp')):
                apis.add(p)
        for p in sorted(apis)[:25]:
            print(f'   {p}')
        if not apis:
            print('   (없음)')

        # ⑤ 페이지네이션 파라미터 흔적
        pgs = set(re.findall(r'[?&](page|pageNum|p|offset|start)=\d+', html))
        print(f'\n④ 페이지네이션 파라미터 흔적: {sorted(pgs) or "(없음)"}')

    # ⑥ 상품 상세가 서버 렌더링인지 확인 — 여기만 되면 상세 수집은 가능
    print(f'\n{"=" * 60}\n=== 상품 상세 페이지 확인 ===')
    r = requests.get(f'{BASE}/shop_view/?idx=2486', headers=HEADERS, timeout=25)
    h = r.text
    print(f'HTTP {r.status_code} · {len(h):,}바이트')
    t = re.search(r'<title[^>]*>(.*?)</title>', h, re.S)
    print(f'제목: {t.group(1).strip() if t else "-"}')
    print(f'가격 형태 샘플: {re.findall(r"[\\d,]{4,}\\s*원", h)[:6]}')


if __name__ == '__main__':
    try:
        main()
    except requests.RequestException as e:
        print(f'✗ 네트워크 오류: {e}')
        sys.exit(1)
