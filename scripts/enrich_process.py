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
REPORT     = os.path.join(ROOT, 'data', 'process_enrich.json')

TIMEOUT          = 15
PER_DOMAIN_DELAY = 0.4
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


def enrich_domain(session_items, results):
    session, items = session_items
    for p in items:
        url = p.get('url', '')
        try:
            r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code < 400 and r.text:
                proc = extract_process(r.text)
                if proc != '알수없음':
                    results[p['id']] = proc
        except requests.RequestException:
            pass
        time.sleep(PER_DOMAIN_DELAY)


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

    results = {}

    def make(items):
        s = requests.Session(); s.headers.update(HEADERS)
        return (s, items)

    with ThreadPoolExecutor(max_workers=min(16, len(by_domain) or 1)) as ex:
        list(ex.map(lambda items: enrich_domain(make(items), results), by_domain.values()))

    # 적용
    filled_by = Counter()
    for p in data['products']:
        if p['id'] in results:
            p['process'] = results[p['id']]
            filled_by[p['process']] += 1

    if results:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(results)}개 가공방식 보강 완료: {dict(filled_by)}  (잔여 미상 {len(targets)-len(results)}개)")

    with open(REPORT, 'w', encoding='utf-8') as f:
        json.dump({
            'checked_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'targets': len(targets), 'filled': len(results),
            'filled_by': dict(filled_by),
        }, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"⚠️  가공방식 보강 오류({e}) — 데이터 보존하고 통과")
        sys.exit(0)
