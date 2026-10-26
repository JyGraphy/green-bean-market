#!/usr/bin/env python3
"""품절·신상 '조용한 오작동' 감지 — 매일 갱신 파이프라인용 (재발 방지).

**왜 필요한가**
기존 자동 검사(healthcheck / site_selfcheck / validate_data)는 '터진 것'만 잡는다:
사이트 다운, store 소멸, 급감, 죽은 링크, 상대경로 URL, 백엔드 다운. 그런데 품절·신상의
'조용한 오작동' — 스크래퍼가 품절 템플릿을 오독해 전 상품을 품절로 올리거나(모모스·
오월의숲 유형), 품절 감지가 어느 날 통째로 멈추거나, 목록이 캐시로 굳어 신상이 몇 주째
0이거나 — 는 어디에도 안 걸려서, 지금까지 사람이 눈으로 봐야만 발견했다.

이 스크립트가 그 빈자리를 메운다. 심각 항목이 있으면 종료코드 1 → 워크플로 빨간 X →
저장소 소유자에게 알림 메일. 사용자가 사이트에서 직접 발견하기 전에 자동으로 잡는다.

검사 항목
  🔴 전량 품절      : 한 store 가 품절률 ≥95% (상품 ≥8개) — 품절 오버레이 템플릿 오탐 전형
  🔴 품절감지 중단  : 직전엔 품절이 있었는데 오늘 0개 (상품 ≥5개) — 감지 로직이 깨진 신호
  🟡 품절 급증      : 직전 대비 품절률이 40%p 이상 급등
  🟡 신상 정체      : 어떤 store 도 N일(기본 14일)째 신규 상품 0 — 스크래퍼 캐시/정체 의심

과거값 비교를 위해 data/soldout_history.json 에 매 실행의 store별 (상품수, 품절수)을
append 하고 최근 30회만 보관한다. 품절감지 중단/급증은 '직전 기록'과 비교한다.

사용법: python3 scripts/anomaly_check.py
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCTS = ROOT / 'data' / 'products.json'
DATES = ROOT / 'data' / 'product_dates.json'
HISTORY = ROOT / 'data' / 'soldout_history.json'

# ── 임계값 (오탐을 줄이려 보수적으로) ─────────────────────────────
FULL_SOLDOUT_RATIO = 0.95   # 이 비율 이상이면 '전량 품절' 의심
FULL_SOLDOUT_MIN   = 8      # 단, 상품이 이 수 이상일 때만 (소수 store 오탐 방지)
VANISH_MIN         = 5      # 품절감지 중단 판정 최소 상품 수
SPIKE_PP           = 0.40   # 품절률 급등 경고 기준 (percentage point)
STALE_NEW_DAYS     = 14     # 신상 정체 경고 기준 (일)
HISTORY_KEEP       = 30     # 이력 보관 회수


def kst_today() -> str:
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).strftime('%Y-%m-%d')


def load_json(path: pathlib.Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def store_stats(products) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for p in products:
        s = p.get('store')
        st = stats.setdefault(s, {'total': 0, 'soldout': 0})
        st['total'] += 1
        if p.get('is_soldout'):
            st['soldout'] += 1
    return stats


def newest_added_days_ago(dates: dict) -> int | None:
    """product_dates 의 최신 등록일이 며칠 전인지. 날짜 값이 하나도 없으면 None."""
    vals = [v for v in dates.values() if v]
    if not vals:
        return None
    newest = max(vals)
    try:
        d = datetime.date.fromisoformat(newest)
    except ValueError:
        return None
    today = (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()
    return (today - d).days


def main() -> int:
    data = load_json(PRODUCTS, None)
    if data is None:
        print('⚠️  products.json 을 읽지 못했습니다 — 건너뜀(데이터 보존)')
        return 0
    products = data['products'] if isinstance(data, dict) else data
    stats = store_stats(products)

    history = load_json(HISTORY, [])
    prev = history[-1]['stores'] if history else {}

    critical, warns = [], []

    for store, st in sorted(stats.items()):
        total, sold = st['total'], st['soldout']
        ratio = sold / total if total else 0

        # 🔴 전량 품절 (오버레이 템플릿 오탐 전형)
        if total >= FULL_SOLDOUT_MIN and ratio >= FULL_SOLDOUT_RATIO:
            critical.append(
                f'{store}: 품절 {sold}/{total} ({ratio:.0%}) — 거의 전량 품절. '
                f'품절 이미지가 전 상품에 템플릿으로 깔린 오탐일 가능성이 높습니다 '
                f'(공급사 링크 진단 → {store} 로 상세 availability 교차검증).')

        # 🔴 품절감지 중단: 직전엔 있었는데 오늘 0
        pv = prev.get(store)
        if pv and total >= VANISH_MIN and sold == 0 and pv.get('soldout', 0) > 0:
            critical.append(
                f'{store}: 어제 품절 {pv["soldout"]}개 → 오늘 0개. '
                f'품절 감지 로직이 멈췄을 수 있습니다(쇼핑몰 마크업 변경 의심).')

        # 🟡 품절률 급등
        if pv and total >= FULL_SOLDOUT_MIN:
            pv_ratio = pv['soldout'] / pv['total'] if pv.get('total') else 0
            if ratio - pv_ratio >= SPIKE_PP:
                warns.append(
                    f'{store}: 품절률 {pv_ratio:.0%} → {ratio:.0%} 급등 '
                    f'({sold}/{total}) — 확인 권장.')

    # 🟡 신상 정체 — 어떤 store 도 N일째 신규 0
    dates = load_json(DATES, {})
    days = newest_added_days_ago(dates)
    if days is not None and days >= STALE_NEW_DAYS:
        warns.append(
            f'신규 입고 정체: 마지막 신규 상품이 {days}일 전입니다 '
            f'(전 공급사 통틀어). 스크래퍼가 옛 목록을 캐시로 돌려주는 정체 의심.')

    # ── 이력 기록 (최근 HISTORY_KEEP 회만 보관) ──────────────────
    history.append({'date': kst_today(), 'stores': stats})
    history = history[-HISTORY_KEEP:]
    try:
        HISTORY.write_text(json.dumps(history, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        print(f'⚠️  이력 저장 실패({e}) — 판정은 계속')

    # ── 보고 ─────────────────────────────────────────────────────
    print('=' * 55)
    print(f'🔎 품절·신상 이상 감지 — {kst_today()}')
    total_sold = sum(s['soldout'] for s in stats.values())
    print(f'   상품 {sum(s["total"] for s in stats.values())}개 · 품절 {total_sold}개 · '
          f'마지막 신규 {days if days is not None else "?"}일 전')
    if warns:
        print('⚠️  경고:')
        for w in warns:
            print(f'   - {w}')
            print(f'::warning::{w}')
    if critical:
        print('❌ 조치 필요:')
        for c in critical:
            print(f'   - {c}')
            print(f'::error::{c}')

    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as f:
            f.write(f'\n### 품절·신상 이상 감지 ({kst_today()})\n')
            for c in critical:
                f.write(f'- 🔴 {c}\n')
            for w in warns:
                f.write(f'- 🟡 {w}\n')
            if not critical and not warns:
                f.write('- ✅ 이상 없음\n')

    if critical:
        print(f'\n❌ 조치 필요 {len(critical)}건 — 위 항목 확인')
        return 1
    print(f'\n✅ 심각 이상 없음 (경고 {len(warns)}건)')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        # 감지기 자체 오류는 비치명적 — 데이터 보존하고 통과
        print(f'⚠️  이상 감지 중 오류({e}) — 통과')
        sys.exit(0)
