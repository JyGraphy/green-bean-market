#!/usr/bin/env python3
"""세컨드 브레인 목차 생성 — AI 토큰 0.

vault/wiki/*.md 를 읽어 index.md 를 다시 만들고, raw 문서와의 연결 상태를 점검한다.
vault/CLAUDE.md 규칙 4("혼자 떠도는 파일 금지")를 기계적으로 강제하는 도구.

사용법:
    python3 scripts/build_wiki_index.py
    python3 scripts/build_wiki_index.py --check   # 고아 문서가 있으면 exit 1
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VAULT = ROOT / 'vault'
WIKI = VAULT / 'wiki'
RAW = VAULT / 'raw'
INDEX = WIKI / 'index.md'

RAW_LABELS = {
    'coe': ('🏆', 'COE 옥션'),
    'stores': ('🔎', '공급사 발굴'),
    'qa': ('🛡️', '검수 보고서'),
    'papers': ('📚', '논문'),
    'roast-profiles': ('🔥', '로스팅 프로파일'),
}
LINK_RE = re.compile(r'\[\[([^\]]+)\]\]')


def title_of(path: pathlib.Path) -> str:
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('# '):
            return line[2:].strip()
    return path.stem


def updated_of(path: pathlib.Path) -> str:
    m = re.search(r'\*\*최종 갱신\*\*:\s*(\d{4}-\d{2}-\d{2})', path.read_text(encoding='utf-8'))
    return m.group(1) if m else '—'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    wiki_docs = sorted(p for p in WIKI.glob('*.md') if p.name != 'index.md')
    raw_docs = sorted(RAW.rglob('*.md'))

    # wiki가 참조하는 raw 문서 이름 수집
    linked: set[str] = set()
    for w in wiki_docs:
        linked |= set(LINK_RE.findall(w.read_text(encoding='utf-8')))
    orphans = [r for r in raw_docs if r.stem not in linked]

    L = [
        '# 📚 생두마켓 세컨드 브레인',
        '',
        f'_이 목차는 `scripts/build_wiki_index.py`가 자동 생성합니다 (토큰 0) · '
        f'{datetime.date.today().isoformat()}_',
        '',
        f'정리된 주제 **{len(wiki_docs)}개** · 원본 문서 **{len(raw_docs)}건**',
        '',
        '---',
        '',
        '## 🧠 정리된 지식 (wiki)',
        '',
        '| 주제 | 최종 갱신 | 근거 문서 |',
        '|---|---|---|',
    ]
    for w in wiki_docs:
        n = len(set(LINK_RE.findall(w.read_text(encoding='utf-8'))))
        L.append(f'| [[{w.stem}]] — {title_of(w)} | {updated_of(w)} | {n}건 |')

    L += ['', '## 📥 원본 (raw — 수정 금지)', '']
    for folder in sorted(RAW.iterdir()):
        if not folder.is_dir():
            continue
        docs = sorted(folder.glob('*.md'))
        if not docs:
            continue
        icon, label = RAW_LABELS.get(folder.name, ('📄', folder.name))
        L += [f'### {icon} {label} `raw/{folder.name}/`', '']
        for d in docs:
            mark = '' if d.stem in linked else '  ⚠️ _wiki에서 참조되지 않음_'
            L.append(f'- [[{d.stem}]] — {title_of(d)}{mark}')
        L.append('')

    if orphans:
        L += ['---', '', '## ⚠️ 정리 대기',
              '', f'아래 {len(orphans)}건은 아직 wiki에 반영되지 않았습니다.',
              '정리하려면 Claude에게 다음처럼 지시하세요:', '',
              '```',
              'vault/raw의 아래 문서를 읽고 vault/CLAUDE.md 규칙대로 wiki로 정리해:',
              *[f'  - {o.relative_to(VAULT)}' for o in orphans],
              '```', '']

    INDEX.write_text('\n'.join(L) + '\n', encoding='utf-8')

    if a.check:
        print(f'wiki {len(wiki_docs)}개 · raw {len(raw_docs)}건 · 정리 대기 {len(orphans)}건')
        sys.exit(1 if orphans else 0)
    print(f'✓ {INDEX.relative_to(ROOT)} 생성 (토큰 0) — '
          f'주제 {len(wiki_docs)}개 · 원본 {len(raw_docs)}건 · 정리 대기 {len(orphans)}건')
    for o in orphans:
        print(f'   ⚠️ 미정리: {o.relative_to(VAULT)}')


if __name__ == '__main__':
    main()
