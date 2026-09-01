#!/usr/bin/env python3
"""기기 문서 무결성 검사 — 로스팅 AI 프롬프트에 들어갈 지식의 게이트 (토큰 0).

**왜 필요한가 (2026-09-01)**
상품 데이터에는 validate_data.py, 스크래퍼에는 qa_report.py 라는 게이트가 있는데
**기기 문서에는 아무 검사도 없었다.** 그래서 아래가 전부 그대로 통과해 프롬프트에
들어갔고, 실서비스 판독에 쓰였다:

  · 모델명을 출처 확인 없이 단정 (Stronghold "S7X" vs 사장님 실물 "S7X Pro")
  · 판매처 2차 설명을 제조사 사양처럼 서술 (드럼히터 유무로 모델 구분)
  · verified: yes 인데 문서 스스로 "어느 모델을 검증했는지 기록 없음"이라고 인정
  · 마크다운 백틱이 TS 템플릿 리터럴을 깨뜨려 배포 실패 (2026-08-31)

틀린 기기 지식은 없느니만 못하다 — AI가 확신을 갖고 잘못 읽는다.
그래서 프롬프트에 넣기 전에 여기서 막는다.

사용법:
    python3 scripts/verify_machines.py          # 검사 (문제 있으면 exit 1)
    python3 scripts/verify_machines.py --warn   # 경고만, 항상 exit 0
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MACHINES = ROOT / 'vault' / 'raw' / 'roast-profiles' / 'machines'
SOURCES = ROOT / 'vault' / 'raw' / 'roast-profiles' / 'sources'

REQUIRED_FIELDS = ['heat_source', 'temp_probe', 'typical_total_time', 'chart_app', 'verified']

# verified: yes 를 정당화하려면 문서에 '무엇으로 검증했는지'가 있어야 한다.
# 아래 표현 중 하나라도 있어야 통과 — 없으면 근거 없는 yes 로 본다.
EVIDENCE_PATTERNS = [
    r'실제.{0,12}(차트|CSV|파일|이미지).{0,12}(검증|확인)',
    r'##\s*검증\s*기록',
    r'verified[- ]by:',
]

# 2차 출처에 기대는 서술 — 그 자체로 실패는 아니지만 표시가 있어야 한다.
SECONDARY_HINTS = ['판매처', '보도', '리뷰', '블로그', '커뮤니티', '마케팅']


def field(text: str, name: str) -> str | None:
    m = re.search(rf'^-\s*{name}\s*:\s*(.+)$', text, re.M | re.I)
    return m.group(1).strip() if m else None


def model_tokens(title: str) -> list[str]:
    """제목에서 모델명처럼 보이는 토큰 (S7X, THCR-06, 800G, R-101 …)."""
    return re.findall(r'\b[A-Z]{1,5}[- ]?\d{1,4}[A-Za-z]*\b', title)


def source_text_for(stem: str) -> str:
    """이 기기로 수집된 원본들의 합본 (모델명 대조용)."""
    if not SOURCES.exists():
        return ''
    return '\n'.join(p.read_text(encoding='utf-8', errors='replace')
                     for p in SOURCES.glob(f'{stem}-*.md'))


def check(path: pathlib.Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding='utf-8')
    errs, warns = [], []
    title_m = re.search(r'^#\s+(.+)$', text, re.M)
    title = title_m.group(1).strip() if title_m else path.stem

    # ① 필수 필드
    for f in REQUIRED_FIELDS:
        if field(text, f) is None:
            errs.append(f'필수 필드 `- {f}:` 없음')

    # ② 판독 규칙 — 이게 없으면 프롬프트에 아무것도 안 들어간다
    if not re.search(r'^##\s*판독 규칙\s*$', text, re.M):
        errs.append('`## 판독 규칙` 섹션 없음 — 프롬프트에 주입될 내용이 없다')

    # ③ verified: yes 는 근거를 요구한다
    v = (field(text, 'verified') or '').lower()
    if v.startswith(('y', 'true', '검증')):
        if not any(re.search(p, text) for p in EVIDENCE_PATTERNS):
            errs.append('verified: yes 인데 무엇으로 검증했는지 기록이 없다 '
                        '(실제 차트/CSV 검증 문장 또는 `## 검증 기록` 필요)')

    # ④ 백틱 — 프롬프트가 TS 템플릿 리터럴이라 배포를 깨뜨린 전력이 있다
    if '`' in text:
        warns.append(f'백틱 {text.count("`")}개 — 주입 시 이스케이프되지만 쓰지 않는 편이 안전')

    # ⑤ 모델명 대조: 제목의 모델 토큰이 수집 원본에 실제로 나오는가
    src = source_text_for(path.stem)
    toks = model_tokens(title)
    if toks:
        if not src:
            warns.append(f'수집 원본 없음 — 모델명 {toks} 을 1차 자료로 대조하지 못함')
        else:
            missing = [t for t in toks if t.replace(' ', '').replace('-', '').lower()
                       not in src.replace(' ', '').replace('-', '').lower()]
            if missing:
                errs.append(f'제목의 모델명 {missing} 이 수집 원본에 없다 — '
                            f'출처 확인 없이 단정했을 가능성')

    # ⑥ 2차 출처 의존 표시
    for h in SECONDARY_HINTS:
        if h in text and '미확인' not in text and '추정' not in text:
            warns.append(f'2차 출처("{h}") 기반 서술이 있는데 미확인/추정 표기가 없다')
            break
    return errs, warns


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--warn', action='store_true', help='경고만 내고 항상 성공')
    a = ap.parse_args()

    files = sorted(p for p in MACHINES.glob('*.md') if not p.name.startswith('_'))
    if not files:
        print('기기 문서가 없습니다.')
        return 0

    total_e = total_w = 0
    print(f'🔍 기기 문서 무결성 검사 — {len(files)}대\n')
    for p in files:
        errs, warns = check(p)
        total_e += len(errs)
        total_w += len(warns)
        if not errs and not warns:
            print(f'  ✅ {p.stem}')
            continue
        print(f'  {"❌" if errs else "🟡"} {p.stem}')
        for e in errs:
            print(f'       ✗ {e}')
        for w in warns:
            print(f'       · {w}')

    print(f'\n오류 {total_e}건 · 경고 {total_w}건')
    if total_e and not a.warn:
        print('→ 오류를 고친 뒤 프롬프트에 주입하세요. 틀린 기기 지식은 없느니만 못합니다.')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
