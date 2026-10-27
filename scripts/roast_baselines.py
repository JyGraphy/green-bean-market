#!/usr/bin/env python3
"""로스팅 AI 누적 학습 ① — 로스터리 실측 기준선 재계산.

매주 지금까지 쌓인 모든 로스팅 기록으로 기기·배치별 기준선(P5·중앙값·P95)을 다시 계산해
data/roast-baselines.json 에 쓴다. 사이트(roasting.js)는 이 파일을 읽어 피드백 기준으로 쓴다.
→ 기록이 늘어날수록 기준선이 자동으로 정교해진다 (코드에 숫자를 박아 두지 않는다).

원천 (비공개 버킷 roast-learning):
  seed/firescope/features30.csv.gz + profiles_index.csv.gz   드럼 곡선 특징값 (2020-06~2026-10)
  seed/boost/all_profiles.json.gz, corpus/boost/list/*.json  S7X 기록 메타 (총 시간·배출·DTR)
  seed/boost/details.tar.gz, corpus/boost/details/*.json     S7X 상세 곡선 (터닝포인트·구간·RoR)
  readings/**.json                                            사이트 분석 기록 중 곡선을 믿을 수 있는 것
                                                              (데이터 파일 또는 앵커 검증된 픽셀 추출)

공개 저장소에는 집계값만 쓴다. 개별 로스팅 기록은 커밋하지 않는다.

사용법:
    python3 scripts/roast_baselines.py                 # 버킷 → data/roast-baselines.json
    python3 scripts/roast_baselines.py --local DIR     # DIR 을 버킷 대신 사용 (시험용)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import io
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from roast_learning_lib import (Store, curve_features, detail_id, group_for, percentile,  # noqa: E402
                                tar_members)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'data' / 'roast-baselines.json'
METRICS = ['total', 'tpT', 'tpBt', 'dry', 'mai', 'ror200', 'drop', 'dtr']
MIN_N = 30          # 이보다 적은 그룹은 기준선을 내지 않는다 (사이트는 기본값 유지)


def firescope(store, rows_by_group, counts):
    idx = {}
    for r in csv.DictReader(io.StringIO(store.get_text('seed/firescope/profiles_index.csv.gz'))):
        idx[r['id']] = r
    n = 0
    for r in csv.DictReader(io.StringIO(store.get_text('seed/firescope/features30.csv.gz'))):
        f = lambda k: float(r[k]) if r.get(k) not in ('', None) else None  # noqa: E731
        d, db, t2, t1 = f('dur'), f('drop_bt'), f('t200'), f('t150')
        if not d or d < 240 or d > 1500 or not db or db < 190 or db > 250 or not t2:
            continue
        ch = idx.get(r['id'], {}).get('chargeAmount')
        try:
            ch = float(ch)
        except (TypeError, ValueError):
            ch = None
        if ch is None:          # 투입량 모르는 기록은 배치 구분이 안 되므로 뺀다
            continue
        if ch <= 300:
            g = 'drumSmall'
        elif ch >= 800:
            g = 'drumLarge'
        elif 400 <= ch <= 700:
            g = 'drum'
        else:
            continue
        rows_by_group.setdefault(g, []).append({
            'total': d / 60, 'tpT': f('tp_t'), 'tpBt': f('tp_bt'), 'dry': t1 / d * 100 if t1 else None,
            'mai': (t2 - t1) / d * 100 if t1 else None, 'ror200': f('ror200'), 'drop': db,
            'dtr': (d - t2) / d * 100})
        n += 1
    counts['firescope_seed'] = n


def boost(store, rows_by_group, counts):
    """메타(총 시간·배출·DTR)는 전체 기록, 곡선 지표는 상세 곡선에서."""
    meta = {r['prflMCd']: r for r in store.get_json('seed/boost/all_profiles.json.gz')}
    for p in store.list('corpus/boost/list'):
        for r in store.get_json(p):
            meta[r['prflMCd']] = r
    curves = {}
    for name, raw in tar_members(store.get('seed/boost/details.tar.gz')):
        if name.endswith('.json'):
            curves[detail_id(name)] = json.loads(raw)
    for p in store.list('corpus/boost/details'):
        curves[detail_id(p)] = store.get_json(p)
    s7x_meta, s7x_curve = [], []
    for r in meta.values():
        if (r.get('totalRstTime') or 0) > 0:
            s7x_meta.append({'total': r['totalRstTime'] / 60,
                             'drop': r.get('dschgIrCTemp') if (r.get('dschgIrCTemp') or 0) > 0 else None,
                             'dtr': r.get('dtr') if (r.get('dtr') or 0) > 0 else None})
    for d in curves.values():
        if d.get('resultCd') != 'COMM_0000':
            continue
        T = [t for t in d.get('temps') or [] if t.get('irCTemp') and t.get('internalCTemp')]
        dur = (d.get('prflM') or {}).get('totalRstTime') or (T[-1]['rstTime'] if T else 0)
        if not T or dur < 300 or dur > 900:
            continue
        f = curve_features([(t['rstTime'], t['irCTemp']) for t in T], dur,
                           [(t['rstTime'], t['internalCTemp']) for t in T], tp_on='et')
        if f:
            s7x_curve.append(f)
    rows_by_group['s7x'] = rows_by_group.get('s7x', []) + [{'_meta': m} for m in s7x_meta] + \
        [{'_curve': c} for c in s7x_curve]
    counts['boost_meta'] = len(s7x_meta)
    counts['boost_curves'] = len(s7x_curve)


def site_readings(store, rows_by_group, counts):
    """사이트 분석 기록: 데이터 파일 곡선(정답) 또는 앵커 검증된 픽셀 곡선만 쓴다. 같은 로스팅의 중복 분석은 하나로."""
    seen, n = set(), 0
    for p in store.list('readings'):
        if not p.endswith('.json'):
            continue
        try:
            r = store.get_json(p)
        except Exception:  # noqa: BLE001
            continue
        res = r.get('result') or {}
        truth = r.get('truth') or {}
        pix = r.get('pixel') or {}
        if truth.get('bt'):
            bt, et, dur = truth['bt'], truth.get('et'), truth.get('drop_t') or res.get('total_time')
        elif pix.get('ok') and (pix.get('max_res') or 9) <= 2 and res.get('bt_series'):
            bt = list(zip(res['time_series'], res['bt_series']))
            et = list(zip(res['time_series'], res['et_series'])) if res.get('et_series') else None
            dur = res.get('total_time')
        else:
            continue
        g = group_for(r.get('machine'), r.get('charge_weight'), res.get('fluid_bed'))
        key = hashlib.md5(json.dumps([g, round(dur or 0), [round(v, 1) for _, v in bt[::12]]]).encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        f = curve_features(bt, dur, et, tp_on='et' if g == 's7x' else 'bt')
        if not f:
            continue
        f['drop'] = res.get('drop_temp')
        f['dtr'] = res.get('dtr') if res.get('dtr') is not None else f.get('dtr200')
        rows_by_group.setdefault(g, []).append(f if g != 's7x' else {'_meta': f, '_curve': f})
        n += 1
    counts['site_readings'] = n


def summarize(rows_by_group):
    out = {}
    for g, rows in rows_by_group.items():
        if g == 's7x':
            meta = [r['_meta'] for r in rows if '_meta' in r]
            curve = [r['_curve'] for r in rows if '_curve' in r]
            src = {'total': meta, 'drop': meta, 'dtr': meta,
                   'tpT': curve, 'tpBt': curve, 'dry': curve, 'mai': curve, 'ror200': curve}
            n = len(meta)
        else:
            src = {m: rows for m in METRICS}
            n = len(rows)
        if n < MIN_N:
            continue
        gb = {'n': n}
        for m in METRICS:
            vals = [r.get(m) for r in src[m] if r.get(m) is not None]
            if len(vals) < MIN_N:
                continue
            nd = 0 if m in ('tpT',) else 1
            gb[m] = [round(percentile(vals, p), nd) for p in (0.05, 0.5, 0.95)]
        out[g] = gb
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', help='버킷 대신 쓸 로컬 폴더')
    args = ap.parse_args()
    store = Store(args.local)
    rows, counts = {}, {}
    for step in (firescope, boost, site_readings):
        try:
            step(store, rows, counts)
        except Exception as e:  # noqa: BLE001 — 원천 하나 실패가 전체를 막지 않는다
            print(f'⚠️ {step.__name__} 건너뜀: {type(e).__name__}: {e}')
    groups = summarize(rows)
    data = {
        'generated': datetime.date.today().isoformat(),
        'method': 'P5·중앙값·P95. 5초 리샘플·RoR 30초 창. 드럼 건조=150°C 도달, 발달=200°C 도달~배출. '
                  'S7X 터닝포인트는 내부 온도 기준. scripts/roast_baselines.py 가 매주 재계산.',
        'sources': counts,
        'groups': groups,
    }
    OUT.parent.mkdir(exist_ok=True)
    old = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'✓ {OUT.relative_to(ROOT)} — 원천 {counts}')
    for g, b in groups.items():
        prev = (old.get('groups') or {}).get(g, {})
        print(f'   · {g:10s} n={b["n"]:>6} (지난번 {prev.get("n", "-")}) dtr={b.get("dtr")} drop={b.get("drop")}')


if __name__ == '__main__':
    main()
