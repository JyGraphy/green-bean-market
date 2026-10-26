#!/usr/bin/env python3
"""한 store의 상품 링크가 왜 죽었는지 진단한다 — GitHub Actions 전용.

**왜 필요한가**
`check_links.py` 는 한 store의 dead 비율이 30%를 넘으면 "URL 구조 변경 의심"으로
**제거를 보류**한다(대량 삭제 사고 방지). 이건 올바른 설계지만, 보류된 뒤에 아무도
확인하지 않으면 죽은 링크가 그대로 사용자에게 노출된다.
실제로 모모스커피 115개가 100% dead 상태로 방치돼 있었다(2026-08-19 발견).

이 스크립트는 그 보류 신호를 받아 **실제로 뭐가 바뀌었는지** 알아낸다:
저장된 URL을 찔러보고, 쇼핑몰 목록 페이지를 새로 받아 현재 href 형식과 비교한다.

Claude Code 세션은 쇼핑몰 접근이 403으로 막히므로 GitHub Actions에서 실행한다.

사용법:
    python3 scripts/diagnose_store.py --store 모모스커피
    python3 scripts/diagnose_store.py --store 모모스커피 --sample 8
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'products.json'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# store → 상품 목록 페이지 (스크래퍼와 같은 주소)
LISTING = {
    '모모스커피': 'https://momos.co.kr/product/list.html?cate_no=64',
    '커피리브레': 'https://coffeelibre.kr/product/list.html?cate_no=45',
    '오월의숲': 'https://mayforest.kr/product/list.html?cate_no=50&page=1',
}

# 품절 신호 진단용 — store별 목록 상품 li 셀렉터 (스크래퍼와 동일해야 함).
# 품절이 전 상품에 100%로 뜨면 '품절 오버레이가 템플릿으로 전 상품에 깔린' 오탐
# (모모스 .prod_icon.sold_out 사건과 같은 유형)일 가능성이 높다. 이 진단은 목록의
# 오버레이 비율과 상세페이지의 권위 신호(schema.org availability)를 함께 보여줘
# '진짜 전부 품절'과 '오탐'을 구분하게 돕는다.
LI_SELECTOR = {
    '오월의숲': '.xans-product-listnormal ul.prdList > li',
    '커피리브레': '.xans-product-listnormal ul.prdList > li',
}
# 목록 썸네일 위 품절 이미지 오버레이 (common.is_soldout_block 과 동일 기준)
SOLDOUT_IMG_SEL = ('img[alt*="품절"], img[alt*="SOLD OUT"], img[alt*="Sold out"], '
                   'img[src*="soldout"], img[src*="sold_out"], img[src*="icon_soldout"]')


def load_urls(store: str) -> list[dict]:
    d = json.loads(DATA.read_text(encoding='utf-8'))
    P = d['products'] if isinstance(d, dict) else d
    return [p for p in P if p.get('store') == store]


def probe(url: str) -> tuple[int | None, str]:
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        return r.status_code, r.url
    except requests.RequestException as e:
        return None, f'{type(e).__name__}: {e}'


def shape(url: str) -> str:
    """URL을 형태(패턴)로 요약해 비교하기 쉽게 만든다."""
    p = urlparse(unquote(url))
    segs = [s for s in p.path.split('/') if s]
    out = []
    for s in segs:
        if s.isdigit():
            out.append('<숫자>')
        elif re.search(r'[가-힣]', s):
            out.append('<한글슬러그>')
        elif re.fullmatch(r'[a-z0-9-]+', s):
            out.append('<영문슬러그>')
        else:
            out.append(s)
    return '/' + '/'.join(out) + (f'?{p.query.split("=")[0]}=…' if p.query else '')


AVAIL_RE = re.compile(r'"availability"\s*:\s*"?(?:https?://schema\.org/)?'
                      r'(InStock|OutOfStock|SoldOut|BackOrder|PreOrder)', re.I)


def diagnose_soldout(store: str, listing: str, sample: int):
    """목록의 품절 오버레이 비율 + 상세페이지 권위 신호(schema availability)를 본다.

    '어떤 store가 100% 품절'은 거의 항상 오버레이 템플릿 오탐이다. 목록 비율이
    수상하면 상세페이지의 schema.org availability 로 교차검증한다.
    """
    sel = LI_SELECTOR.get(store)
    if not sel:
        return
    print(f'\n④ 품절 신호 진단 ({store})')
    try:
        r = requests.get(listing, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, 'lxml')
    except requests.RequestException as e:
        print(f'   ✗ 목록 재요청 실패: {e}')
        return
    lis = soup.select(sel)
    overlay, detail_links = 0, []
    samples = []
    for li in lis:
        img = li.select_one(SOLDOUT_IMG_SEL)
        if img:
            overlay += 1
            if len(samples) < 3:
                samples.append(str(img)[:140])
        a_tag = li.select_one('a[href*="/product/"]')
        if a_tag and a_tag.get('href') and 'list.html' not in a_tag['href']:
            detail_links.append(a_tag['href'])
    n = len(lis)
    print(f'   목록 상품 {n}개 중 품절 오버레이 있는 것: {overlay}개'
          + (f' ({overlay/n*100:.0f}%)' if n else ''))
    if n and overlay == n:
        print('   🔴 전 상품(100%)이 오버레이 보유 → 품절 이미지가 템플릿으로 전 상품에 '
              '깔렸을 가능성이 매우 높음(오탐). 상세페이지 권위 신호로 교차검증한다.')
    for s in samples:
        print(f'      오버레이 예: {s}')

    # 상세페이지 schema.org availability 로 교차검증 (JS 없이 서버 HTML 에 나옴)
    from urllib.parse import urljoin
    base = f'{urlparse(listing).scheme}://{urlparse(listing).netloc}'
    uniq = list(dict.fromkeys(detail_links))[:sample]
    print(f'   상세페이지 {len(uniq)}개 availability 교차검증:')
    avails = {}
    for h in uniq:
        full = urljoin(base + '/', h)
        try:
            rr = requests.get(full, headers=HEADERS, timeout=20)
            m = AVAIL_RE.search(rr.text)
            av = m.group(1) if m else '(availability 없음)'
            # 보조 신호: 상세페이지에 품절 오버레이/텍스트가 실제로 있는지
            dsoup = BeautifulSoup(rr.text, 'lxml')
            dimg = bool(dsoup.select_one(SOLDOUT_IMG_SEL))
        except requests.RequestException as e:
            av, dimg = f'요청실패 {type(e).__name__}', False
        avails[av] = avails.get(av, 0) + 1
        print(f'      availability={av:28} 품절이미지={dimg}  {full[:80]}')
    print(f'   요약: {avails}')
    instock = avails.get('InStock', 0)
    if n and overlay == n and instock:
        print(f'   ✅ 판정: 목록은 100% 품절로 보이지만 상세 availability 에 InStock 이 '
              f'{instock}개 → 목록 오버레이는 오탐. 스크래퍼를 상세 availability 기준으로 고쳐야 함.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--store', required=True)
    ap.add_argument('--sample', type=int, default=6)
    a = ap.parse_args()

    prods = load_urls(a.store)
    if not prods:
        print(f'✗ "{a.store}" 상품이 data/products.json 에 없습니다.')
        sys.exit(1)

    print(f'=== {a.store} · 저장된 상품 {len(prods)}개 ===\n')

    # 품절 신호 진단을 먼저 실행한다 — 아래 링크 형태 진단은 중간 return 이 많아
    # 여기서 호출해야 어떤 경로로도 실행이 보장된다.
    _listing = LISTING.get(a.store)
    if _listing and a.store in LI_SELECTOR:
        diagnose_soldout(a.store, _listing, a.sample)
        print()

    # ① 저장된 URL 상태 확인
    print(f'① 저장된 URL {a.sample}개 확인')
    codes = {}
    for p in prods[:a.sample]:
        code, final = probe(p['url'])
        codes[code] = codes.get(code, 0) + 1
        print(f'   [{code}] {p["url"][:95]}')
        if code and code != 404 and final != p['url']:
            print(f'         → 리다이렉트: {final[:95]}')
    print(f'   요약: {codes}\n')
    print(f'   저장된 URL 형태: {shape(prods[0]["url"])}\n')

    # ② 쇼핑몰 목록 페이지에서 현재 href 를 새로 수집
    listing = LISTING.get(a.store)
    if not listing:
        print(f'② 목록 페이지 주소가 등록돼 있지 않습니다 (LISTING 에 추가 필요) — 여기까지.')
        return
    print(f'② 목록 페이지에서 현재 링크 확인: {listing}')
    code, final = probe(listing)
    if code != 200:
        print(f'   ✗ 목록 페이지 자체가 HTTP {code} — 쇼핑몰 구조가 크게 바뀌었거나 차단됨')
        return
    if final != listing:
        print(f'   ↪ 리다이렉트됨: {final}')
    r = requests.get(listing, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, 'lxml')

    # 페이지가 실제로 무엇을 주는지 먼저 확인한다 (셀렉터 문제 vs 구조 변경 구분)
    title = (soup.title.get_text(strip=True) if soup.title else '(제목 없음)')
    all_a = soup.find_all('a')
    scripts = soup.find_all('script')
    print(f'   페이지 제목: {title}')
    print(f'   HTML {len(r.text):,}바이트 · <a> {len(all_a)}개 · <script> {len(scripts)}개')
    if '생두' in r.text:
        print('   본문에 "생두" 문자열 있음')
    else:
        print('   ⚠️ 본문에 "생두" 문자열이 없음 — 이 카테고리가 더 이상 생두가 아닐 수 있음')
    if len(all_a) < 5 and len(scripts) > 3:
        print('   ⚠️ 링크가 거의 없고 스크립트가 많음 — 클라이언트 렌더링(SPA) 전환 의심')

    hrefs = []
    for a_tag in soup.select('a[href*="/product/"]'):
        h = a_tag.get('href', '')
        if h and 'list.html' not in h:
            hrefs.append(h)
    hrefs = list(dict.fromkeys(hrefs))
    print(f'   현재 목록에서 상품 링크 {len(hrefs)}개 추출')

    if not hrefs:
        print('   ✗ /product/ 링크를 못 찾음. 페이지에 실제로 있는 링크 형태를 조사합니다:')
        pats = {}
        for a_tag in all_a:
            h = a_tag.get('href', '')
            if not h or h.startswith(('#', 'javascript:', 'mailto:')):
                continue
            key = shape(h if h.startswith('http') else 'https://x' + (h if h.startswith('/') else '/' + h))
            pats[key] = pats.get(key, 0) + 1
        for k, c in sorted(pats.items(), key=lambda kv: -kv[1])[:12]:
            print(f'      {c:>4}개  {k}')
        if not pats:
            print('      (링크가 하나도 없음 — 서버가 빈 껍데기 HTML을 주는 상태)')
        # 카테고리 번호가 바뀌었는지 단서 찾기
        cats = sorted(set(re.findall(r'cate_no=(\d+)', r.text)))
        if cats:
            print(f'   페이지에 등장하는 cate_no 값: {cats[:20]}')
            print('   → 생두 카테고리 번호가 바뀌었을 수 있습니다(현재 스크래퍼는 64 사용).')
        return

    from urllib.parse import urljoin
    base = f'{urlparse(listing).scheme}://{urlparse(listing).netloc}'
    for h in hrefs[:a.sample]:
        full = urljoin(base + '/', h)
        c, _ = probe(full)
        print(f'   [{c}] {full[:95]}')
    print(f'\n   현재 URL 형태: {shape(urljoin(base + "/", hrefs[0]))}')

    # ③ 판정
    print('\n③ 판정')
    old_shape, new_shape = shape(prods[0]['url']), shape(urljoin(base + '/', hrefs[0]))
    if old_shape == new_shape:
        print('   형태는 동일 — 개별 상품이 내려갔거나(품절/단종) 상품 ID가 갱신된 것으로 보입니다.')
        print('   → 스크래퍼를 다시 돌려 최신 목록으로 교체하는 것이 해법입니다.')
    else:
        print(f'   ⚠️ URL 형태가 달라졌습니다.')
        print(f'      저장됨: {old_shape}')
        print(f'      현재  : {new_shape}')
        print('   → 쇼핑몰이 URL 구조를 바꿨습니다. 스크래퍼 재실행으로 교체해야 합니다.')


if __name__ == '__main__':
    main()
