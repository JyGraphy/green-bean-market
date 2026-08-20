"""
가공방식 보강 — 상품명으로 가공방식을 못 잡은 상품의 상세페이지를 받아 추출.

상품명에 가공정보가 없어 process='알수없음'인 상품만 대상으로, 상세페이지 본문에서
가공방식(한글/영문)을 찾아 채운다. 요청 수를 줄이기 위해 '알수없음'만 조회한다.

추출 우선순위 (오탐 최소화):
  1. '가공/프로세스/process' 라벨 주변 텍스트에서 추출 (정밀)
  2. 실패 시 본문 전체에서 추출 (재현율 보강)
둘 다 common.guess_process를 사용하므로 키워드 정책이 일관된다.

안전장치:
  - 알수없음만 조회(기존 분류는 건드리지 않음)
  - 도메인별 순차+지연, 도메인 간 병렬 (예의)
  - 네트워크/파싱 오류는 비치명적 — 해당 상품은 그대로 두고 진행
  - 스크립트 자체 오류도 비치명적(데이터 보존)
"""
import json, os, sys, time, re
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scrapers'))
import requests
from bs4 import BeautifulSoup
from common import HEADERS, guess_process

ROOT       = os.path.join(os.path.dirname(__file__), '..')
JSON_FILE  = os.path.join(ROOT, 'data', 'products.json')
DATES_FILE = os.path.join(ROOT, 'data', 'product_dates.json')
REPORT     = os.path.join(ROOT, 'data', 'process_enrich.json')

TIMEOUT          = 15
PER_DOMAIN_DELAY = 0.4
STORE_DEAD_GUARD = 0.30   # store 미상 중 dead 비율이 이 값 초과면 제거 보류(URL 스킴 변경 의심)
DEAD_CODES       = {404, 410}
LABEL_RE = re.compile(r'(가공\s*방식|가공|프로세스|process(?:ing)?)\s*[:：\-]?\s*(.{0,40})', re.I)


def extract_process(html):
    """상세페이지 HTML에서 가공방식 추출. 못 찾으면 '알수없음'."""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    text = re.sub(r'\s+', ' ', soup.get_text(' '))

    # 1) 라벨 주변 우선
    for m in LABEL_RE.finditer(text):
        proc = guess_process(m.group(2))
        if proc != '알수없음':
            return proc
    # 2) 본문 전체 폴백
    return guess_process(text)


def enrich_domain(dom, items, results, dead, dom_time, dom_cnt):
    """도메인 하나를 순차 조회. GET 한 번으로 (a) 가공방식 추출 (b) 죽은 링크 판정."""
    t0 = time.monotonic()
    session = requests.Session(); session.headers.update(HEADERS)
    for p in items:
        url = p.get('url', '')
        try:
            r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code in DEAD_CODES:
                dead.add(p['id'])              # 404/410 → 죽은 링크 (check_links 대신 여기서 판정)
            elif r.status_code < 400 and r.text:
                proc = extract_process(r.text)
                if proc != '알수없음':
                    results[p['id']] = proc
        except requests.RequestException:
            pass
        time.sleep(PER_DOMAIN_DELAY)
    dom_time[dom] = time.monotonic() - t0
    dom_cnt[dom] = len(items)


def main():
    with open(JSON_FILE, encoding='utf-8') as f:
        data = json.load(f)
    targets = [p for p in data['products'] if p.get('process') == '알수없음']
    print(f"🔎 가공방식 보강 — '알수없음' {len(targets)}개 상세페이지 조회")
    if not targets:
        print("대상 없음 — 종료")
        return

    by_domain = defaultdict(list)
    for p in targets:
        by_domain[urlparse(p.get('url', '')).netloc or '_x'].append(p)

    results = {}       # id → 추출된 process
    dead = set()       # id → 죽은 링크(404/410)
    dom_time, dom_cnt = {}, {}

    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=min(16, len(by_domain) or 1)) as ex:
        list(ex.map(lambda kv: enrich_domain(kv[0], kv[1], results, dead, dom_time, dom_cnt),
                    by_domain.items()))
    elapsed = time.monotonic() - t0

    # 가공방식 적용
    filled_by = Counter()
    for p in data['products']:
        if p['id'] in results:
            p['process'] = results[p['id']]
            filled_by[p['process']] += 1

    # 죽은 링크 제거 (check_links가 '알수없음'을 스킵하므로 여기서 담당) — store 가드 유지
    by_store_dead = defaultdict(list)
    by_store_total = Counter(p['store'] for p in targets)
    for p in targets:
        if p['id'] in dead:
            by_store_dead[p['store']].append(p['id'])
    to_remove, held = set(), []
    for store, ids in by_store_dead.items():
        ratio = len(ids) / by_store_total[store] if by_store_total[store] else 0
        if ratio > STORE_DEAD_GUARD:
            held.append(f"{store}: 미상 중 dead {len(ids)}/{by_store_total[store]} ({ratio:.0%}) — 제거 보류")
        else:
            to_remove.update(ids)

    if to_remove:
        data['products'] = [p for p in data['products'] if p['id'] not in to_remove]
        if os.path.exists(DATES_FILE):
            with open(DATES_FILE, encoding='utf-8') as f:
                dates = json.load(f)
            for rid in to_remove:
                dates.pop(str(rid), None)
            with open(DATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(dates, f, ensure_ascii=False)

    if results or to_remove:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # 측정 출력
    print(f"⏱️  GET {len(targets)}건 / {elapsed:.0f}초  (도메인 오래 걸린 순):")
    for dom, sec in sorted(dom_time.items(), key=lambda x: -x[1])[:8]:
        n = dom_cnt.get(dom, 0)
        print(f"     {sec:6.0f}초  {n:4d}건  평균{sec/n if n else 0:4.1f}s  {dom}")
    print(f"✅ 가공방식 {len(results)}개 보강: {dict(filled_by)}  |  죽은 링크 {len(to_remove)}개 제거"
          f"  |  잔여 미상 {len(targets)-len(results)-len(to_remove)}개")
    if held:
        print("⚠️  제거 보류:", "; ".join(held))

    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump({
            'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'targets': len(targets), 'filled': len(results), 'removed_dead': len(to_remove),
            'filled_by': dict(filled_by), 'held_stores': held,
            'timing': {
                'elapsed_sec': round(elapsed, 1), 'requests': len(targets),
                'slowest_domains': sorted(
                    ({'domain': d, 'sec': round(s, 1), 'count': dom_cnt.get(d, 0)}
                     for d, s in dom_time.items()), key=lambda x: -x['sec'])[:8],
            },
        }, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"⚠️  가공방식 보강 오류({e}) — 데이터 보존하고 통과")
        sys.exit(0)
