#!/usr/bin/env python3
"""모모스 스크래퍼 드라이런 — 저장하지 않고 수집 결과만 확인한다.

새 스크래퍼(`scrapers/scraper_momos.py`, 아임웹 대응)를 실전 투입하기 전에
**몇 개가 잡히는지 먼저 본다.** 기존 115개 대비 절반(58개) 미만이면
`guard_store_replacement` 가 교체를 막는데, 그게 스크래퍼 부족인지 실제 상품
감소인지 구분하지 않고 밀어넣으면 상품이 통째로 사라질 수 있기 때문이다.

Claude Code 세션은 쇼핑몰 접근이 403이라 GitHub Actions 에서 실행한다.
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scrapers'))

import json  # noqa: E402

import scraper_momos as M  # noqa: E402
from common import to_products  # noqa: E402


def main():
    items = M.scrape()

    with open(os.path.join(ROOT, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    old = [p for p in data['products'] if p['store'] == M.STORE]
    existing_ids = {p['id'] for p in data['products'] if p['store'] != M.STORE}

    products = to_products(items, M.STORE, M.ID_START, existing_ids)

    print('\n' + '=' * 60)
    print(f'드라이런 결과: 기존 {len(old)}개 → 신규 {len(products)}개')
    threshold = int(len(old) * 0.5)
    if len(products) < threshold:
        print(f'⚠️ 급감 가드 임계({threshold}개) 미만 — 이대로 돌리면 교체가 차단된다.')
    else:
        print(f'✅ 급감 가드 임계({threshold}개) 이상 — 안전하게 교체 가능.')

    print(f'\n원산지 분포: {dict(Counter(p["origin"] for p in products).most_common(12))}')
    print(f'가공방식 분포: {dict(Counter(p["process"] for p in products).most_common())}')
    print(f'품절: {sum(1 for p in products if p["is_soldout"])}개')
    bad = [p for p in products if not str(p['url']).startswith('http')]
    print(f'상대경로 url: {len(bad)}건 (0이어야 함)')

    print('\n샘플 8개:')
    for p in products[:8]:
        print(f'  [{p["id"]}] {p["name"][:52]:52} {p["price"]:>7,}원 '
              f'{p["origin"]:6} {p["process"]:8} {p["url"]}')


if __name__ == '__main__':
    main()
