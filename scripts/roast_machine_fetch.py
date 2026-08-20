#!/usr/bin/env python3
"""로스터기 자료 수집 — 리서치 주기에 함께 도는 로스팅 AI 학습용 원본 수집기.

**왜 이 파일이 있는가**
로스팅 AI(`supabase/functions/analyze-roast`)는 파인튜닝 모델이 아니라
**판독 규칙 프롬프트**다. 그래서 "기기 지식을 글로 적어 프롬프트에 넣는 것"이 곧 학습이다.
그 글을 쓰려면 근거 자료가 필요한데, Claude Code 세션은 허용목록 정책 때문에
제조사·문서 사이트가 403으로 막힌다. GitHub Actions 러너는 인터넷이 열려 있으므로
여기서 원본을 받아 `vault/raw/roast-profiles/sources/` 에 쌓는다.

이후 `roast-profile-collector` 가 그 원본을 읽고
`vault/raw/roast-profiles/machines/<기기>.md` 의 판독 규칙으로 옮기면,
`build_roast_knowledge.py` 가 프롬프트에 주입하고 `deploy-functions.yml` 이 배포한다.

논문 수집(`paper_fetch.py`)과 같은 대기열 방식이다 — 리서치 팀이 프로파일을 조사하다
필요한 기기 자료를 발견하면 대기열에 한 줄 적어두고, 다음 리서치 실행이 받아온다.

대기열: `vault/raw/roast-profiles/_수집대기.md`
    - [ ] <기기키> <URL>  <메모>
  예) - [ ] giesen https://giesencoffeeroasters.com/...  W6A 사양표

사용법:
    python3 scripts/roast_machine_fetch.py --queue
    python3 scripts/roast_machine_fetch.py --machine giesen --url https://...
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / 'vault' / 'raw' / 'roast-profiles'
SOURCES = BASE / 'sources'
MACHINES = BASE / 'machines'
QUEUE = BASE / '_수집대기.md'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8',
}
# 본문이 아닌 것들 — 남겨두면 규칙을 쓸 때 잡음이 된다
DROP_TAGS = ('script', 'style', 'nav', 'header', 'footer', 'noscript', 'form', 'iframe')


def kst_today() -> str:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')


def slugify(s: str) -> str:
    s = re.sub(r'https?://', '', s)
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s[:70] or 'source'


def extract(html: str) -> tuple[str, str]:
    """제목과 본문 텍스트를 뽑는다. 표는 마크다운으로 살린다(사양표가 핵심 자료다)."""
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title.get_text(strip=True) if soup.title else ''
    for t in soup(DROP_TAGS):
        t.decompose()

    parts = []
    for tbl in soup.find_all('table'):
        rows = []
        for tr in tbl.find_all('tr'):
            cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]
            if any(cells):
                rows.append('| ' + ' | '.join(cells) + ' |')
        if len(rows) >= 2:
            head, rest = rows[0], rows[1:]
            sep = '|' + '---|' * (head.count('|') - 1)
            parts.append('\n'.join([head, sep] + rest))
        tbl.decompose()

    body = soup.get_text('\n', strip=True)
    body = re.sub(r'\n{3,}', '\n\n', body)

    out = body
    if parts:
        out += '\n\n## 표\n\n' + '\n\n'.join(parts)
    return title, out


def fetch_one(machine: str, url: str, note: str = '') -> pathlib.Path | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f'   ✗ {machine} · {url[:70]} — {type(e).__name__}: {e}')
        return None

    title, body = extract(r.text)
    SOURCES.mkdir(parents=True, exist_ok=True)
    path = SOURCES / f'{machine}-{slugify(url)}.md'
    path.write_text(
        f'# {title or machine}\n\n'
        f'- machine: {machine}\n'
        f'- source_url: {url}\n'
        f'- fetched_at: {kst_today()}\n'
        f'- note: {note or "-"}\n\n'
        f'> 이 파일은 자동 수집된 **원본**이다. 수정하지 않는다.\n'
        f'> 여기서 읽은 내용을 `machines/{machine}.md` 의 판독 규칙으로 옮기면 학습이 된다.\n\n'
        f'---\n\n{body}\n',
        encoding='utf-8')
    print(f'   ✓ {machine} · {len(body):,}자 → {path.relative_to(ROOT)}')
    return path


def read_queue() -> list[tuple[str, str, str]]:
    if not QUEUE.exists():
        return []
    items = []
    for line in QUEUE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\s*-\s*\[ \]\s*(\S+)\s+(https?://\S+)\s*(.*)', line)
        if m:
            items.append((m.group(1), m.group(2), m.group(3).strip()))
    return items


def unverified_machines() -> list[str]:
    """아직 실측 검증이 안 된 기기 목록 — 리서치 우선순위를 보고서에 띄운다."""
    out = []
    if not MACHINES.exists():
        return out
    for p in sorted(MACHINES.glob('*.md')):
        if p.name.startswith('_'):
            continue
        txt = p.read_text(encoding='utf-8')
        if re.search(r'verified:\s*no', txt):
            out.append(p.stem)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--queue', action='store_true', help='대기열 일괄 처리')
    ap.add_argument('--machine', help='기기 키 (machines/<키>.md 와 같게)')
    ap.add_argument('--url', help='받아올 자료 주소')
    a = ap.parse_args()

    targets: list[tuple[str, str, str]] = []
    if a.machine and a.url:
        targets.append((a.machine, a.url, ''))
    if a.queue:
        targets += read_queue()

    if not targets:
        print('수집 대기 중인 로스터기 자료가 없습니다.')
        pending = unverified_machines()
        if pending:
            print(f'\n검증 대기 기기 {len(pending)}대: {", ".join(pending)}')
            print(f'자료가 필요하면 {QUEUE.relative_to(ROOT)} 에 한 줄 추가하세요:')
            print('  - [ ] <기기키> <URL>  <메모>')
        return 0

    print(f'로스터기 자료 {len(targets)}건 수집')
    got = [p for m, u, n in targets if (p := fetch_one(m, u, n))]

    print(f'\n수집 완료 {len(got)}/{len(targets)}건')
    pending = unverified_machines()
    if pending:
        print(f'검증 대기 기기 {len(pending)}대: {", ".join(pending)}')
    # 한 건도 못 받으면 실패로 알린다 (대기열이 비어 있는 경우는 위에서 이미 종료).
    return 0 if got else 1


if __name__ == '__main__':
    sys.exit(main())
