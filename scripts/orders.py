#!/usr/bin/env python3
"""지시함 처리 — 토큰 0.

`vault/지시함.md`의 체크박스를 읽어 담당 직원·모델·처리 방식을 결정한다.
AI가 지시함을 통째로 읽고 "누가 할까" 고민하는 데 토큰을 쓰지 않도록,
그 판단을 스크립트가 대신해 실행 계획만 넘긴다.

사용법:
    python3 scripts/orders.py              # 대기 목록
    python3 scripts/orders.py --dispatch   # 실행 계획 (Claude가 이대로만 수행)
    python3 scripts/orders.py --done "커피시스" --result "[[2026-08-03-실사]]"
    python3 scripts/orders.py --check      # 대기 건이 있으면 exit 1
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INBOX = ROOT / 'vault' / '지시함.md'

# 태그 → (담당, 모델, 산출물 경로, 스크립트 선처리 여부)
ROUTES = {
    'coe':      ('coe-auction-reporter',      'sonnet', 'vault/raw/coe/',            None),
    '발굴':      ('store-scout',               'haiku',  'vault/raw/stores/',         None),
    '온보딩':    ('new-store-onboarder',       'sonnet', '(코드 수정)',                None),
    '논문':      ('coffee-research-translator','sonnet', 'vault/raw/papers/',         None),
    '프로파일':  ('roast-profile-collector',   'haiku',  'vault/raw/roast-profiles/', None),
    '데이터':    ('data-validator',            'haiku',  'vault/raw/qa/',             'python3 scripts/qa_report.py'),
    '스크래퍼':  ('scraper-checker',           'sonnet', 'vault/raw/qa/',             'python3 scripts/qa_report.py'),
    '프론트':    ('frontend-reviewer',         'haiku',  'vault/raw/qa/',             None),
    '정리':      ('(메인 세션)',                '-',      'vault/wiki/',               'python3 scripts/build_wiki_index.py'),
}
ALIAS = {'scout': '발굴', 'store': '발굴', 'paper': '논문', 'profile': '프로파일',
         'data': '데이터', 'scraper': '스크래퍼', 'front': '프론트', 'wiki': '정리'}

PENDING_RE = re.compile(r'^-\s*\[ \]\s*@(\S+)\s+(.*)$')


def parse():
    if not INBOX.exists():
        return []
    orders = []
    in_pending = False
    for n, line in enumerate(INBOX.read_text(encoding='utf-8').splitlines(), 1):
        if line.startswith('## '):
            in_pending = '대기' in line
            continue
        if not in_pending:
            continue
        m = PENDING_RE.match(line.strip())
        if not m:
            continue
        tag = ALIAS.get(m.group(1).lower(), m.group(1))
        text = m.group(2)
        urgent = '!급함' in text
        text = text.replace('!급함', '').strip()
        agent, model, out, pre = ROUTES.get(tag, ('(미지정)', '-', '-', None))
        orders.append(dict(line_no=n, tag=tag, text=text, urgent=urgent,
                           agent=agent, model=model, out=out, pre=pre))
    orders.sort(key=lambda o: not o['urgent'])
    return orders


def show(orders):
    if not orders:
        print('📮 대기 중인 지시 없음')
        return
    print(f'📮 대기 중인 지시 {len(orders)}건\n')
    for i, o in enumerate(orders, 1):
        flag = '🔥급함 ' if o['urgent'] else ''
        print(f'{i}. {flag}@{o["tag"]} → {o["agent"]} ({o["model"]})')
        print(f'   {o["text"]}')
        if o['pre']:
            print(f'   ↳ 먼저 실행: {o["pre"]}  (토큰 0)')
        print()


def dispatch(orders):
    if not orders:
        print('실행할 지시가 없습니다. AI 호출 불필요.')
        return
    print('=== 실행 계획 ===\n')
    print('아래 순서대로만 수행하고, 끝나면 각 건을 --done 으로 닫으세요.\n')
    pres = [o['pre'] for o in orders if o['pre']]
    if pres:
        print('① 스크립트 선처리 (토큰 0)')
        for c in dict.fromkeys(pres):
            print(f'   {c}')
        print('   → 결과에 문제가 없으면 해당 지시는 AI 호출 없이 완료 처리\n')
    print('② 에이전트 호출')
    for o in orders:
        if o['agent'] == '(미지정)':
            print(f'   ⚠️ 태그 @{o["tag"]} 는 담당이 없습니다 — 사장님께 확인 요청')
            continue
        print(f'   - {o["agent"]} (model={o["model"]})')
        print(f'     지시: {o["text"]}')
        print(f'     산출물: {o["out"]}YYYY-MM-DD-*.md  (REPORT-FORMAT 규격)')
    print('\n③ 마무리')
    print('   python3 scripts/build_wiki_index.py   # 목차 갱신 (토큰 0)')
    print('   python3 scripts/orders.py --done "<지시 일부>" --result "[[산출물]]"')


def done(keyword, result):
    text = INBOX.read_text(encoding='utf-8')
    lines = text.splitlines()
    today = datetime.date.today().isoformat()
    hit = None
    for i, line in enumerate(lines):
        m = PENDING_RE.match(line.strip())
        if m and keyword in line:
            hit = i
            break
    if hit is None:
        print(f'✗ "{keyword}" 를 포함한 대기 지시를 찾지 못했습니다.')
        sys.exit(1)
    m = PENDING_RE.match(lines[hit].strip())
    entry = f'- [x] {today} @{m.group(1)} {m.group(2).replace("!급함","").strip()}'
    if result:
        entry += f' → {result}'
    del lines[hit]
    for i, line in enumerate(lines):
        if line.startswith('## ') and '완료' in line:
            lines.insert(i + 2, entry)
            break
    else:
        lines += ['', '## ✅ 완료', '', entry]
    INBOX.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'✓ 완료 처리: {m.group(2)[:40]}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dispatch', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--done', metavar='KEYWORD')
    ap.add_argument('--result', default='')
    a = ap.parse_args()

    if a.done:
        done(a.done, a.result)
        return
    orders = parse()
    if a.check:
        print(f'대기 {len(orders)}건')
        sys.exit(1 if orders else 0)
    if a.dispatch:
        dispatch(orders)
        return
    show(orders)


if __name__ == '__main__':
    main()
