#!/usr/bin/env python3
"""매일 갱신 직후 사이트 문제를 스스로 찾아 보고한다 (토큰 0).

**왜 필요한가 — 2026-08-19 모모스 사건**
모모스커피가 cafe24 → 아임웹으로 이전하면서 상품 URL 115개가 전부 404가 됐다.
안전장치는 제대로 작동했다: 스크래퍼가 0개를 수집하자 가드가 덮어쓰기를 막았고,
`check_links.py` 는 dead 비율 100%를 "URL 구조 변경 의심"으로 보고 제거를 보류했다.
**그런데 그 뒤에 아무도 알아채지 못했다.** 데이터는 지켜졌지만 죽은 링크가 계속
사용자에게 노출됐다. 보류는 '나중에 사람이 본다'를 전제하는데, 그 사람이 없었다.

이 스크립트가 그 빈자리를 메운다. 매일 06시 갱신 파이프라인에서
`check_links.py` 가 남긴 `data/link_check.json` 을 읽어 **판정하고 시끄럽게 만든다.**
심각한 항목이 있으면 종료코드 1 → 워크플로 빨간 X → 저장소 소유자에게 알림 메일.

판정 기준
  🔴 store 전멸   : 살아있는 링크 0개 (플랫폼 이전/URL 구조 변경) → 실패
  🔴 제거 보류    : check_links 가 30% 초과 dead 로 보류한 store → 실패
  🟡 부분 dead    : 일부만 죽음 (품절/단종은 정상, 자동 제거됨) → 경고
  🟡 전부 모호    : 403/타임아웃만 (봇차단 의심, 데이터는 보존) → 경고

사용법: python3 scripts/site_selfcheck.py
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK_CHECK = ROOT / 'data' / 'link_check.json'
PRODUCTS = ROOT / 'data' / 'products.json'
QA_DIR = ROOT / 'vault' / 'raw' / 'qa'

# 부분 dead 를 경고로 올릴 기준. 이 아래는 품절/단종으로 보고 넘어간다
# (check_links 가 이미 제거했으므로 데이터에는 남아 있지 않다).
PARTIAL_DEAD_WARN = 0.10


def kst_today() -> str:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')


def load(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f'✗ {path.name} 읽기 실패: {e}')
        return None


def main() -> int:
    lc = load(LINK_CHECK)
    if lc is None:
        # 링크 검증이 아예 못 돌았다는 뜻. 데이터는 멀쩡할 수 있으니 경고로만 둔다.
        print('⚠️  link_check.json 이 없습니다 — 링크 검증이 실행되지 않았습니다.')
        return 0

    per_store = lc.get('per_store') or {}
    held = lc.get('held_stores') or []
    removed = lc.get('removed') or []

    critical, warns, healthy = [], [], []

    for store, s in sorted(per_store.items()):
        ok = s.get('ok', 0)
        dead = s.get('dead', 0)
        amb = s.get('ambiguous', 0)
        total = ok + dead + amb
        if total == 0:
            continue
        if dead and ok == 0 and amb == 0:
            critical.append(
                f'{store}: 살아있는 링크 0개 (dead {dead}/{total}) — '
                f'쇼핑몰이 URL 구조를 바꿨을 가능성이 높습니다')
        elif ok == 0 and amb == total:
            warns.append(
                f'{store}: 전부 모호 응답 {amb}건 (403/타임아웃) — '
                f'봇차단 의심. 데이터는 보존됨')
        elif dead and dead / total >= PARTIAL_DEAD_WARN:
            warns.append(f'{store}: dead {dead}/{total} ({dead / total:.0%}) — 부분 정리됨')
        else:
            healthy.append(store)

    # check_links 가 스스로 "보류"라고 표시한 것은 무조건 심각으로 올린다.
    # 이게 바로 모모스 사건에서 아무도 안 본 그 신호다.
    for h in held:
        critical.append(f'제거 보류: {h}')

    # 상품 수 — store가 통째로 사라졌는지 별도 확인 (validate_data 와 중복이지만
    # 여기서는 '사람이 읽는 보고서'에 함께 담기 위해 다시 센다)
    prods = load(PRODUCTS)
    counts = {}
    if prods:
        P = prods['products'] if isinstance(prods, dict) else prods
        for p in P:
            counts[p.get('store')] = counts.get(p.get('store'), 0) + 1

    # ── 보고서 작성 ────────────────────────────────────────────────
    lines = [f'# 사이트 자가 점검 — {kst_today()}', '']
    lines.append(f'검사 시각(link_check): {lc.get("checked_at", "-")} · 상품 {lc.get("total", "-")}개')
    lines.append('')
    if critical:
        lines += ['## 🔴 조치 필요', '']
        lines += [f'- {c}' for c in critical]
        lines += ['',
                  '**조치 방법** — `공급사 링크 진단` 워크플로를 해당 공급사로 실행한다',
                  '(Actions → 공급사 링크 진단 → Run workflow → store 입력).',
                  '스크래퍼가 새 구조에 맞게 고쳐지면 `rescrape=true` 로 링크를 교체한다.',
                  '취급 품목이 실제로 줄어 급감 가드에 걸리면, 감소가 사실임을 확인한 뒤에만',
                  '`force=true` 로 우회한다.', '']
    if warns:
        lines += ['## 🟡 경고 (조치 불필요, 관찰 대상)', '']
        lines += [f'- {w}' for w in warns]
        lines += ['']
    if removed:
        lines += ['## 🧹 이번에 자동 제거된 죽은 링크', '',
                  f'- {len(removed)}건']
        lines += [f'  - {r}' for r in removed[:20]]
        if len(removed) > 20:
            lines += [f'  - … 외 {len(removed) - 20}건']
        lines += ['']
    lines += ['## ✅ 정상 공급사', '',
              ', '.join(f'{s}({counts.get(s, "?")})' for s in healthy) or '(없음)', '']
    report = '\n'.join(lines)

    QA_DIR.mkdir(parents=True, exist_ok=True)
    out = QA_DIR / f'{kst_today()}-사이트점검.md'
    out.write_text(report, encoding='utf-8')

    # ── 콘솔 · GitHub 요약 ─────────────────────────────────────────
    print(report)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(report + '\n')

    for c in critical:
        print(f'::error::{c}')
    for w in warns:
        print(f'::warning::{w}')

    if critical:
        print(f'\n❌ 조치가 필요한 항목 {len(critical)}건 — 보고서: {out.relative_to(ROOT)}')
        return 1
    print(f'\n✅ 조치 필요 항목 없음 (경고 {len(warns)}건) — 보고서: {out.relative_to(ROOT)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
