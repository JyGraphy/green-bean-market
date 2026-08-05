#!/usr/bin/env python3
"""세계 커피 옥션 결과 수집 — GitHub Actions 전용. (구 coe_fetch.py 를 확장)

**왜 필요한가**: Claude Code 세션은 네트워크 허용목록 정책 때문에 옥션 사이트에
접근이 403으로 막힌다. GitHub Actions 러너는 인터넷이 열려 있어 실제 수신이 가능하다.

**무엇이 달라졌나 (사장님 피드백 반영)**:
- COE만이 아니라 **BOP(Best of Panama) 등 각국 옥션을 모두** 다룬다.
- 1위만이 아니라 **전체 랏 순위표를 통째로** 보존한다. 요약하지 않는다.
- **낙찰자(buyer)·낙찰가** 컬럼을 탐지해 별도로 표시한다. "어디가 낙찰받았는지"가 핵심이다.

사용법:
    python3 scripts/auction_fetch.py                    # 전체 소스
    python3 scripts/auction_fetch.py --source coe       # COE만
    python3 scripts/auction_fetch.py --source bop       # BOP만
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
OUT_DIR = ROOT / 'vault' / 'raw' / 'auctions'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
}
TIMEOUT = 25
DELAY = 2

ACE = 'https://allianceforcoffeeexcellence.org'
COE_COUNTRIES = [
    'nicaragua', 'el-salvador', 'costa-rica', 'honduras', 'guatemala', 'mexico',
    'thailand', 'indonesia', 'taiwan', 'peru', 'brazil', 'colombia', 'ethiopia', 'rwanda',
]

# 소스 정의: 이름 → 페이지 목록 {라벨: URL}
def coe_pages(year: int) -> dict[str, str]:
    pages = {
        'COE 예정 옥션': f'{ACE}/upcoming-auctions/',
        'COE 결과 아카이브': f'{ACE}/competition-auction-results/',
        'COE 옥션 플랫폼': 'https://auction.allianceforcoffeeexcellence.org/',
    }
    for c in COE_COUNTRIES:
        pages[f'COE {c} {year}'] = f'{ACE}/{c}-{year}/'
    return pages


def bop_pages(year: int) -> dict[str, str]:
    """Best of Panama — 게이샤 최고가 경신이 자주 나오는 옥션."""
    return {
        'BOP 공식': 'https://bestofpanama.org/',
        'BOP 결과': 'https://bestofpanama.org/results/',
        f'BOP {year} 결과': f'https://bestofpanama.org/{year}-results/',
        'BOP 옥션 플랫폼': 'https://auction.bestofpanama.org/',
        'SCAP(파나마 스페셜티커피협회)': 'https://scap.com.pa/',
    }


SOURCES = {'coe': coe_pages, 'bop': bop_pages}

# 낙찰자·낙찰가로 볼 만한 컬럼명 (표 안에 있으면 강조 표시)
BUYER_HINTS = ('buyer', 'winning', 'winner', 'bid', 'price', 'purchaser', 'sold',
               'usd', '$/lb', 'per lb', 'amount')


def fetch(url: str) -> tuple[int, str]:
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    return r.status_code, r.text


def table_to_md(table) -> tuple[str, bool]:
    """(마크다운, 낙찰자/낙찰가 컬럼 포함 여부)"""
    rows = []
    for tr in table.find_all('tr'):
        cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]
        if any(cells):
            rows.append(cells)
    if not rows:
        return '', False
    w = max(len(r) for r in rows)
    rows = [r + [''] * (w - len(r)) for r in rows]
    header_txt = ' '.join(rows[0]).lower()
    has_buyer = any(h in header_txt for h in BUYER_HINTS)
    md = '| ' + ' | '.join(rows[0]) + ' |\n' + '|' + '---|' * w + '\n'
    for r in rows[1:]:
        md += '| ' + ' | '.join(r) + ' |\n'
    return md, has_buyer


def scrape(label: str, url: str) -> dict:
    res = {'label': label, 'url': url, 'ok': False, 'status': None,
           'tables': [], 'buyer_tables': 0, 'text': '', 'error': ''}
    try:
        status, html = fetch(url)
        res['status'] = status
        if status != 200:
            res['error'] = f'HTTP {status}'
            return res
        soup = BeautifulSoup(html, 'lxml')
        for t in soup(['script', 'style', 'nav', 'header', 'footer']):
            t.decompose()
        for tbl in soup.find_all('table'):
            md, has_buyer = table_to_md(tbl)
            if md.strip():
                res['tables'].append({'md': md, 'buyer': has_buyer})
                if has_buyer:
                    res['buyer_tables'] += 1
        main = soup.find('main') or soup.find('article') or soup.body
        if main:
            lines = [l for l in main.get_text('\n', strip=True).splitlines() if l.strip()]
            res['text'] = '\n'.join(lines[:150])
        res['ok'] = True
    except requests.RequestException as e:
        res['error'] = f'{type(e).__name__}: {e}'
    return res


def write_report(source: str, pages: list[dict], today: str) -> pathlib.Path:
    ok = [p for p in pages if p['ok']]
    tabled = [p for p in ok if p['tables']]
    buyer_pages = [p for p in ok if p['buyer_tables']]
    failed = [p for p in pages if not p['ok']]
    total_tables = sum(len(p['tables']) for p in ok)

    name = {'coe': 'COE (Cup of Excellence)', 'bop': 'BOP (Best of Panama)'}.get(source, source.upper())

    L = [
        f'# {name} 옥션 결과 — 전체 랏 수집',
        '',
        f'**작성일**: {today} · **담당**: scripts/auction_fetch.py (GitHub Actions, 자동) · '
        f'**신뢰도**: {"상" if tabled else "하"} (주최측 공식 사이트 직접 수신)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. {len(pages)}개 페이지 시도 · 성공 {len(ok)} · 표 **{total_tables}개** 확보 · 실패 {len(failed)}',
        f'2. **낙찰자/낙찰가 컬럼이 있는 표: {sum(p["buyer_tables"] for p in ok)}개** '
        f'({len(buyer_pages)}개 페이지) — "어디가 낙찰받았는지"는 아래 💰 표시 표를 보세요.',
        '3. 표는 **원문 그대로 전량 보존**했습니다. 요약·발췌하지 않았습니다.',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
        '- 없음 (자동 수집)',
        '',
        '## 수집 결과',
        '',
        '| 페이지 | 상태 | 표 | 낙찰정보 |',
        '|---|---|---|---|',
    ]
    for p in pages:
        st = f'✅ {p["status"]}' if p['ok'] else f'❌ {p["error"][:40]}'
        L.append(f'| [{p["label"]}]({p["url"]}) | {st} | {len(p["tables"])}개 | '
                 f'{"💰 " + str(p["buyer_tables"]) + "개" if p["buyer_tables"] else "—"} |')

    if tabled:
        L += ['', '## 전체 랏 표 (원문 그대로 · 무편집)', '']
        for p in tabled:
            L += [f'### {p["label"]}', '', f'출처: {p["url"]}', '']
            for i, t in enumerate(p['tables'], 1):
                mark = ' 💰 **낙찰자/낙찰가 포함**' if t['buyer'] else ''
                L += [f'**표 {i}**{mark}', '', t['md'], '']

    no_table = [p for p in ok if not p['tables']]
    if no_table:
        L += ['', '## 표 미발견 페이지 — 본문 텍스트', '']
        for p in no_table:
            L += [f'### {p["label"]}', '', f'출처: {p["url"]}', '',
                  '```', p['text'][:2500], '```', '']

    if failed:
        L += ['', '## 접근 실패', '', '| 페이지 | 사유 |', '|---|---|']
        L += [f'| [{p["label"]}]({p["url"]}) | {p["error"][:100]} |' for p in failed]

    L += ['', '## 출처', '', f'- {name} 주최측 공식 사이트 — 1차 (직접 수신)', '']

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f'{today}-{source}-전체랏.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', nargs='*', default=list(SOURCES), choices=list(SOURCES))
    ap.add_argument('--year', type=int, default=datetime.date.today().year)
    a = ap.parse_args()

    today = datetime.date.today().isoformat()
    total_ok = 0
    for src in a.source:
        pages = SOURCES[src](a.year)
        print(f'\n=== {src.upper()} ({len(pages)}개 페이지) ===')
        results = []
        for label, url in pages.items():
            print(f'  {label} … ', end='', flush=True)
            r = scrape(label, url)
            print('OK' if r['ok'] else f'FAIL({r["error"][:40]})')
            results.append(r)
            time.sleep(DELAY)
        out = write_report(src, results, today)
        n_ok = sum(1 for r in results if r['ok'])
        n_tbl = sum(len(r['tables']) for r in results)
        n_buy = sum(r['buyer_tables'] for r in results)
        total_ok += n_ok
        print(f'  ✓ {out.relative_to(ROOT)} — {n_ok}/{len(results)} 성공, '
              f'표 {n_tbl}개(낙찰정보 {n_buy}개)')

    if total_ok == 0:
        print('\n⚠️ 전 소스 실패 — 사이트 구조 변경 또는 접근 차단 가능성.')
        sys.exit(1)


if __name__ == '__main__':
    main()
