"""네이버 공식 오픈API(쇼핑 검색)로 스마트스토어 상품 수집.

스마트스토어 직접 접근은 데이터센터 IP에서 차단되지만, 오픈API는 서버 사용을
전제로 한 공식 경로라 CI(GitHub Actions)에서도 동작한다.

준비 (1회):
  1. https://developers.naver.com/apps → 애플리케이션 등록 → '검색' API 선택
  2. 발급된 Client ID/Secret을 리포 Settings > Secrets and variables > Actions에
     NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 으로 등록
  (scrape.yml이 이 시크릿을 env로 주입한다. 미설정 시 스크래퍼는 스킵.)

한계:
  - 검색 기반이라 네이버쇼핑에 노출되지 않은 상품은 누락될 수 있다.
    여러 검색어(생두·주요 산지)를 합집합해 재현율을 높인다.
  - 품절 상품은 검색 결과에서 빠지는 경향 → is_soldout 미검출(목록에서 제외됨).
  - 급감·소멸은 common.guard_store_replacement()가 방어한다.

쿼터: 하루 25,000회 — 본 모듈 사용량은 쿼리 20개 × 최대 10페이지 = 200회 수준.
"""
import html
import os
import re
import time

import requests

API = 'https://openapi.naver.com/v1/search/shop.json'

# 생두 상품 재현율을 높이기 위한 검색어 합집합
QUERIES = [
    '생두', '커피 생두', '생두 1kg', '스페셜티 생두', '디카페인 생두',
    '에티오피아 생두', '케냐 생두', '콜롬비아 생두', '브라질 생두',
    '과테말라 생두', '코스타리카 생두', '파나마 생두', '온두라스 생두',
    '엘살바도르 생두', '페루 생두', '인도네시아 생두', '예가체프 생두',
    '게이샤 생두', '내추럴 생두', '워시드 생두',
]

_TAG = re.compile(r'</?b>')


def _norm(s):
    return re.sub(r'\s+', '', s or '')


def have_keys():
    return bool(os.environ.get('NAVER_CLIENT_ID') and os.environ.get('NAVER_CLIENT_SECRET'))


def _search(query, start, display=100):
    r = requests.get(
        API,
        params={'query': query, 'display': display, 'start': start, 'sort': 'sim'},
        headers={
            'X-Naver-Client-Id': os.environ['NAVER_CLIENT_ID'],
            'X-Naver-Client-Secret': os.environ['NAVER_CLIENT_SECRET'],
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def fetch_store_products(mall_names, require_keyword=None, queries=None, max_pages=10, delay=0.15):
    """쇼핑 검색 결과에서 판매처가 mall_names에 해당하는 상품만 추출.

    mall_names: 판매처명 문자열 또는 표기 후보 리스트 — 공백 무시 비교로
                한 번의 검색 패스에서 모든 후보를 동시에 매칭한다.
    require_keyword: 지정 시 상품명에 이 키워드가 있어야 수집 (예: '생두' — 원두 제외용)
    queries: 검색어 목록. 기본값은 판매처명들 + 생두 일반 검색어 —
             상품명에 '생두'가 없는 몰(예: 아마티보)은 판매처명 검색으로 잡는다.
    반환: [{'name','price','url','is_soldout'}]
    """
    names = [mall_names] if isinstance(mall_names, str) else list(mall_names)
    targets = {_norm(n) for n in names}
    found = {}
    qlist = queries if queries is not None else list(dict.fromkeys(names + QUERIES))
    for q in qlist:
        for page in range(max_pages):
            start = 1 + page * 100
            if start > 1000:  # API 최대 offset
                break
            try:
                data = _search(q, start)
            except requests.HTTPError as e:
                print(f'  [openapi] "{q}" p{page + 1} HTTP 오류: {e} — 다음 쿼리로')
                break
            items = data.get('items', [])
            for it in items:
                if _norm(it.get('mallName')) not in targets:
                    continue
                name = html.unescape(_TAG.sub('', it.get('title') or '')).strip()
                if not name:
                    continue
                if require_keyword and require_keyword not in name:
                    continue
                pid = it.get('productId') or it.get('link')
                price = int(it.get('lprice') or 0)
                if not price:
                    continue
                found[pid] = {
                    'name': name,
                    'price': price,
                    'url': it.get('link'),
                    'is_soldout': False,  # 품절 상품은 검색 결과에서 제외되는 경향
                }
            if len(items) < 100:  # 마지막 페이지
                break
            time.sleep(delay)
    return list(found.values())
