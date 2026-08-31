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

# ── 저장 정책 (2026-08-31) ─────────────────────────────────────────
# 처음엔 받아온 페이지의 **본문 전체**를 저장소에 커밋했다. 두 가지가 잘못됐다.
#  ① 남의 매뉴얼·블로그 전문을 그대로 복사해 저장소에 넣는 것은 재배포에 해당한다.
#  ② PDF 를 HTML 로 착각해 파싱하는 바람에 바이너리 1MB 가 그대로 커밋됐다
#     (fuji-royal PXG4 매뉴얼, 내용이 '%PD…' 로 시작하는 읽을 수 없는 파일).
#
# 학습에 필요한 건 "PT100 프로브가 3mm/6mm 여러 종류"라는 **사실**이지 원문이 아니다.
# 그래서 이렇게 바꾼다:
#  - 표(사양표)는 전량 보존한다 — 열원·프로브·용량 수치가 규칙의 근거다.
#  - 산문은 EXCERPT_LIMIT 까지만 발췌하고 나머지는 출처 URL 로 넘긴다.
#  - HTML 이 아닌 응답(PDF 등)은 본문을 저장하지 않고 메타데이터만 남긴다.
EXCERPT_LIMIT = 2000
HTML_TYPES = ('text/html', 'application/xhtml')


def kst_today() -> str:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')


def slugify(s: str) -> str:
    s = re.sub(r'https?://', '', s)
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return s[:70] or 'source'


def extract(html: str) -> tuple[str, str]:
    """제목과 (표 전량 + 산문 발췌)를 뽑는다. 표가 사양의 근거라 표는 자르지 않는다."""
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

    # 산문은 발췌만 — 전문 복사를 피한다(저장 정책 참조)
    clipped = len(body) > EXCERPT_LIMIT
    out = body[:EXCERPT_LIMIT]
    if clipped:
        out += f'\n\n…(발췌 {EXCERPT_LIMIT}자. 전문은 위 source_url 에서 확인)'
    if parts:
        out += '\n\n## 표 (사양 — 전량 보존)\n\n' + '\n\n'.join(parts)
    return title, out


def fetch_one(machine: str, url: str, note: str = '') -> pathlib.Path | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f'   ✗ {machine} · {url[:70]} — {type(e).__name__}: {e}')
        return None

    ctype = r.headers.get('content-type', '').lower()
    if not any(h in ctype for h in HTML_TYPES):
        # PDF·이미지 등은 파싱하면 바이너리가 그대로 텍스트로 들어간다.
        # 본문은 남기지 않고 "여기에 이런 자료가 있다"는 사실만 기록한다.
        title = machine
        body = (f'> 이 주소는 HTML 이 아니라 `{ctype or "형식 미상"}` 이라 본문을 저장하지 않았다.\n'
                f'> 내용 확인이 필요하면 source_url 을 직접 열어야 한다.')
        print(f'   ⏭️  {machine} · 비-HTML({ctype or "?"}) — 메타데이터만 기록')
    else:
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


def mark_done(done_urls: set[str]) -> int:
    """수집에 성공한 줄을 `- [x]` 로 체크한다.

    **왜 필요한가** — 예전엔 대기열을 읽기만 하고 체크하지 않아서, 매주 월요일마다
    같은 URL 을 다시 받았다(2026-08-31 확인: 완료 0건, 대기 14건 그대로).
    낭비일 뿐 아니라 남의 사이트를 매주 불필요하게 두드리는 일이다.
    """
    if not QUEUE.exists() or not done_urls:
        return 0
    out, n = [], 0
    for line in QUEUE.read_text(encoding='utf-8').splitlines():
        m = re.match(r'(\s*-\s*)\[ \](\s*\S+\s+)(https?://\S+)(.*)', line)
        if m and m.group(3) in done_urls:
            line = f'{m.group(1)}[x]{m.group(2)}{m.group(3)}{m.group(4)}'
            n += 1
        out.append(line)
    QUEUE.write_text('\n'.join(out) + '\n', encoding='utf-8')
    return n


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
    got, done_urls = [], set()
    for m, u, n in targets:
        path = fetch_one(m, u, n)
        if path:
            got.append(path)
            done_urls.add(u)

    # 성공한 것만 체크한다 — 실패한 URL 은 대기열에 남아 다음 실행이 다시 시도한다.
    marked = mark_done(done_urls)
    print(f'\n수집 완료 {len(got)}/{len(targets)}건 · 대기열 체크 {marked}건')
    pending = unverified_machines()
    if pending:
        print(f'검증 대기 기기 {len(pending)}대: {", ".join(pending)}')
    # 한 건도 못 받으면 실패로 알린다 (대기열이 비어 있는 경우는 위에서 이미 종료).
    return 0 if got else 1


if __name__ == '__main__':
    sys.exit(main())
