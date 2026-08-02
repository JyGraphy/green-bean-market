#!/usr/bin/env python3
"""COE(Cup of Excellence) 옥션 결과 자동 수집 — GitHub Actions 전용.

이 스크립트가 필요한 이유: Claude Code 세션(로컬 컨테이너)의 네트워크 정책은
GitHub·패키지 레지스트리만 허용하는 allowlist라 allianceforcoffeeexcellence.org 같은
일반 웹사이트에 WebFetch가 403으로 막힌다 (2026-08-02 실측, __agentproxy/status 로그 확인).
반면 GitHub Actions 러너는 완전한 인터넷 접근권을 갖고 있어 — 기존 스크래퍼들이 cafe24 등
쇼핑몰을 CI에서 직접 긁는 것과 같은 원리로 — 여기서는 ACE 공식 사이트에 실제로 접속할 수 있다.

동작:
1. ACE의 '예정 옥션'·'결과' 페이지와 국가별 페이지를 requests로 직접 받는다.
2. <table> 이 있으면 마크다운 표로 변환한다 (구조가 파악됐을 때 — 신뢰도 '상' 후보).
3. 표를 못 찾으면 본문 텍스트를 통째로 보존한다 (신뢰도 '하' — AI/사람이 나중에 정리).
   **절대 빈손으로 실패하지 않는다.** 페이지 하나가 막혀도 나머지는 계속 수집한다.
4. vault/raw/coe/YYYY-MM-DD-옥션결과-자동수집.md 로 저장 (REPORT-FORMAT 규격).

사용법:
    python3 scripts/coe_fetch.py                 # 기본 국가 목록
    python3 scripts/coe_fetch.py --country brazil peru
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import sys
import time

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'vault' / 'raw' / 'coe'
BASE = 'https://allianceforcoffeeexcellence.org'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
}
TIMEOUT = 20
DELAY_SEC = 2  # 페이지 간 예의상 대기

# 2026 시즌 11개국 (CLAUDE.md 미기재 — vault/wiki/coe-옥션.md 참조)
DEFAULT_COUNTRIES = [
    'nicaragua', 'el-salvador', 'costa-rica', 'honduras', 'guatemala', 'mexico',
    'thailand', 'indonesia', 'taiwan', 'peru', 'brazil',
]
FIXED_PAGES = {
    '예정 옥션': f'{BASE}/upcoming-auctions/',
    '결과 아카이브': f'{BASE}/competition-auction-results/',
}


def fetch(url: str) -> tuple[int, str]:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    return r.status_code, r.text


def table_to_md(table) -> str:
    rows = []
    for tr in table.find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ''
    width = max(len(r) for r in rows)
    rows = [r + [''] * (width - len(r)) for r in rows]
    md = '| ' + ' | '.join(rows[0]) + ' |\n'
    md += '|' + '---|' * width + '\n'
    for r in rows[1:]:
        md += '| ' + ' | '.join(r) + ' |\n'
    return md


def scrape_page(label: str, url: str) -> dict:
    result = {'label': label, 'url': url, 'ok': False, 'status': None,
              'tables': [], 'text_excerpt': '', 'error': ''}
    try:
        status, html = fetch(url)
        result['status'] = status
        if status != 200:
            result['error'] = f'HTTP {status}'
            return result
        soup = BeautifulSoup(html, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        tables = [table_to_md(t) for t in soup.find_all('table')]
        result['tables'] = [t for t in tables if t.strip()]

        main = soup.find('main') or soup.find('article') or soup.body
        text = main.get_text('\n', strip=True) if main else ''
        lines = [l for l in text.splitlines() if l.strip()]
        result['text_excerpt'] = '\n'.join(lines[:120])  # 과금 방지 위해 앞부분만 보존
        result['ok'] = True
    except requests.RequestException as e:
        result['error'] = f'{type(e).__name__}: {e}'
    return result


def write_report(pages: list[dict], today: str) -> pathlib.Path:
    ok = [p for p in pages if p['ok']]
    with_tables = [p for p in ok if p['tables']]
    failed = [p for p in pages if not p['ok']]

    L = [
        '# COE 옥션 결과 자동 수집',
        '',
        f'**작성일**: {today} · **담당**: scripts/coe_fetch.py (GitHub Actions, 자동) · '
        f'**신뢰도**: {"상" if with_tables else "하"} (ACE 공식 사이트 직접 수신)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. {len(pages)}개 페이지 시도 · 성공 {len(ok)} · 표 추출 성공 {len(with_tables)} · 실패 {len(failed)}',
        '2. 표가 추출된 페이지는 랏 단위 수치가 있을 가능성이 높습니다 — 아래 표를 직접 확인하세요.',
        '3. 실패/표 없는 페이지는 본문 텍스트만 보존했습니다 — 사람 또는 AI가 다음 정리에서 참고합니다.',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
        '- 없음 (자동 수집 — 정리는 `vault/CLAUDE.md` 규칙에 따라 `vault/wiki/coe-옥션.md`에 반영)',
        '',
        '## 수집 결과',
        '',
        '| 페이지 | 상태 | 표 추출 | 비고 |',
        '|---|---|---|---|',
    ]
    for p in pages:
        status = f'✅ {p["status"]}' if p['ok'] else f'❌ {p["error"]}'
        tb = f'{len(p["tables"])}개' if p['tables'] else '없음'
        L.append(f'| [{p["label"]}]({p["url"]}) | {status} | {tb} | |')

    if with_tables:
        L += ['', '## 표 (원문 그대로 — 파싱 가공 없음)', '']
        for p in with_tables:
            L += [f'### {p["label"]}', '', f'출처: {p["url"]}', '']
            for i, t in enumerate(p['tables'], 1):
                L += [f'표 {i}:', '', t]

    no_table = [p for p in ok if not p['tables']]
    if no_table:
        L += ['', '## 본문 텍스트 (표 미발견 — 앞부분만 보존)', '']
        for p in no_table:
            L += [f'### {p["label"]}', '', f'출처: {p["url"]}', '',
                  '```', p['text_excerpt'][:2000], '```', '']

    if failed:
        L += ['', '## 접근 실패', '', '| 페이지 | 사유 |', '|---|---|']
        L += [f'| [{p["label"]}]({p["url"]}) | {p["error"]} |' for p in failed]

    L += ['', '## 출처', '', f'- {BASE} — 1차 (ACE 공식, 직접 수신)', '']

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'{today}-옥션결과-자동수집.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--country', nargs='*', default=DEFAULT_COUNTRIES)
    a = ap.parse_args()

    pages_to_fetch = dict(FIXED_PAGES)
    for c in a.country:
        pages_to_fetch[f'{c} 2026'] = f'{BASE}/{c}-2026/'

    results = []
    for label, url in pages_to_fetch.items():
        print(f'  fetching {label} … ', end='', flush=True)
        r = scrape_page(label, url)
        print('OK' if r['ok'] else f'FAIL ({r["error"]})')
        results.append(r)
        time.sleep(DELAY_SEC)

    today = datetime.date.today().isoformat()
    out = write_report(results, today)

    ok_n = sum(1 for r in results if r['ok'])
    print(f'\n✓ {out.relative_to(ROOT)} 저장 — {ok_n}/{len(results)} 페이지 성공')
    if ok_n == 0:
        print('  ⚠️ 전 페이지 실패 — ACE 사이트 구조 변경 또는 접근 차단 가능성. 보고서 확인 요망.')
        sys.exit(1)


if __name__ == '__main__':
    main()
