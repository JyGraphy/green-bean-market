"""
상품 링크(생두사 상품 페이지) 연결성 검증 — 매일 06시 갱신 파이프라인용.

각 상품의 url에 HTTP 요청을 보내 실제로 연결되는지 확인하고, '죽은 링크'만
products.json에서 제거한 뒤 최종 커밋되도록 한다.

판정 (보수적 — 오삭제 방지가 최우선):
  - ok        : 2xx / 3xx 응답               → 유지
  - dead      : 404 / 410 (페이지 확실히 없음) → 제거 대상
  - ambiguous : 403 / 429 / 5xx / 타임아웃 / 연결오류 등
                (쇼핑몰 봇차단·일시장애일 수 있음)  → 유지

안전장치:
  1. dead는 404/410만. 봇차단(403)·일시장애는 절대 제거하지 않는다.
  2. 한 store의 dead 비율이 STORE_DEAD_GUARD(기본 30%) 초과면 URL 스킴 변경
     등 구조적 사유로 보고 그 store는 제거를 보류한다(경고만).
  3. 검증 게이트(validate_data.py)가 뒤에서 store별 급감을 한 번 더 차단한다.
  4. 체커 자체 오류는 비치명적 — 제거 없이 통과(데이터 보존).

예의(politeness): 도메인별로 순차 처리 + 지연을 두고, 도메인 간에는 병렬.
"""
import json, os, sys, time, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scrapers'))
import requests
from common import HEADERS

ROOT       = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE  = os.path.join(ROOT, 'data', 'products.json')
DATES_FILE = os.path.join(ROOT, 'data', 'product_dates.json')
REPORT     = os.path.join(ROOT, 'data', 'link_check.json')

DEAD_CODES       = {404, 410}
TIMEOUT          = 15
PER_DOMAIN_DELAY = 0.4   # 같은 쇼핑몰 연속 요청 간 지연(초)
STORE_DEAD_GUARD = 0.30  # store dead 비율이 이 값 초과면 제거 보류


def check_url(session, url):
    """(status_code|None, 'ok'|'dead'|'ambiguous') 반환."""
    if not url or not url.startswith('http'):
        return None, 'ambiguous'  # 잘못된 url은 함부로 지우지 않음
    for method in ('head', 'get'):
        try:
            r = session.request(method, url, timeout=TIMEOUT, allow_redirects=True,
                                stream=(method == 'get'))
            code = r.status_code
            if method == 'get':
                r.close()
            if code in DEAD_CODES:
                return code, 'dead'
            if code < 400:
                return code, 'ok'
            if code in (405, 501) and method == 'head':
                continue  # HEAD 미지원 → GET 재시도
            return code, 'ambiguous'  # 403/429/5xx 등
        except requests.RequestException:
            if method == 'get':
                return None, 'ambiguous'  # 타임아웃/연결오류 → 보존
            continue
    return None, 'ambiguous'


def check_all(products):
    """products → {id: (code, verdict)}. 도메인별 순차 + 도메인 간 병렬."""
    by_domain = defaultdict(list)
    for p in products:
        dom = urlparse(p.get('url', '')).netloc or '_invalid'
        by_domain[dom].append(p)

    results = {}

    def run_domain(items):
        s = requests.Session()
        s.headers.update(HEADERS)
        for p in items:
            results[p['id']] = check_url(s, p.get('url', ''))
            time.sleep(PER_DOMAIN_DELAY)

    with ThreadPoolExecutor(max_workers=min(16, len(by_domain) or 1)) as ex:
        list(ex.map(run_domain, by_domain.values()))
    return results


def main():
    with open(JSON_FILE, encoding='utf-8') as f:
        data = json.load(f)
    products = data['products']
    print(f"🔗 상품 링크 검증 시작 — {len(products)}개")

    results = check_all(products)

    # store별 집계
    per_store = defaultdict(lambda: {'ok': 0, 'dead': 0, 'ambiguous': 0, 'dead_ids': []})
    for p in products:
        code, verdict = results.get(p['id'], (None, 'ambiguous'))
        st = per_store[p['store']]
        st[verdict] += 1
        if verdict == 'dead':
            st['dead_ids'].append(p['id'])

    # store별 dead 비율 가드 → 제거 대상 확정
    to_remove, held = set(), []
    for store, st in per_store.items():
        total = st['ok'] + st['dead'] + st['ambiguous']
        ratio = st['dead'] / total if total else 0
        if st['dead'] and ratio > STORE_DEAD_GUARD:
            held.append(f"{store}: dead {st['dead']}/{total} ({ratio:.0%}) — URL 구조 변경 의심, 제거 보류")
        else:
            to_remove.update(st['dead_ids'])

    # 리포트 출력
    print("📊 store별 링크 상태 (ok / dead / ambiguous):")
    for store in sorted(per_store):
        st = per_store[store]
        print(f"   {store:12s}  ✅{st['ok']:4d}  💀{st['dead']:3d}  ⚠️{st['ambiguous']:3d}")
    if held:
        print("\n⚠️  제거 보류(가드 발동):")
        for h in held:
            print(f"   - {h}")

    # 죽은 링크 제거
    if to_remove:
        before = len(products)
        data['products'] = [p for p in products if p['id'] not in to_remove]
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # product_dates 정리
        if os.path.exists(DATES_FILE):
            with open(DATES_FILE, encoding='utf-8') as f:
                dates = json.load(f)
            for rid in to_remove:
                dates.pop(str(rid), None)
            with open(DATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(dates, f, ensure_ascii=False)
        print(f"\n🗑️  죽은 링크(404/410) {len(to_remove)}개 제거 — {before} → {len(data['products'])}개")
    else:
        print("\n✅ 죽은 링크 없음 — 제거 없음")

    # 리포트 파일
    summary = {
        'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'total': len(products),
        'removed': sorted(to_remove),
        'held_stores': held,
        'per_store': {s: {k: v for k, v in st.items() if k != 'dead_ids'}
                      for s, st in per_store.items()},
    }
    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # 체커 자체 오류는 비치명적 — 데이터 보존하고 통과
        print(f"⚠️  링크 검증 중 오류({e}) — 제거 없이 통과(데이터 보존)")
        sys.exit(0)
