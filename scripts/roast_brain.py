#!/usr/bin/env python3
"""로스팅 AI 누적 학습 ④ — 로스팅 판단 두뇌(자체 모델) 학습.

Claude 는 그래프를 읽고 설명하는 '눈과 입'이고, 맛 결과를 예측하는 '판단 두뇌'는 우리 기록으로
직접 학습한 이 모델이다. 매주 쌓인 기록 전체로 다시 학습하므로 기록이 늘수록 두뇌가 자란다.

학습 자료 (비공개 버킷 roast-learning):
  seed/firescope/features30.csv.gz    곡선 특징값 (총 시간·발달·배출·RoR …)
  seed/firescope/records.csv.gz       생두·투입량·감량·밀도·수분
  seed/firescope/memo_labels.json.gz  로스터 메모에서 AI가 정리한 맛 평가 (언더·오버·베이크드·떫은맛·산미·전체 평가)

예측 대상 (메모에 맛 평가가 있는 로스팅만 학습):
  under 언더·풋맛 · over 탄맛·오버 · baked 베이크드·플랫 · astringent 떫은맛 · sour 튀는 산미 · bad 전체 평가 나쁨

검증: 시간순으로 나눠 과거 80%로 학습하고 이후 20%(학습에 안 쓴 최근 기록)로 맞히는지 잰다 (AUC).
출력: data/roast-brain.json (사이트용 모델) · data/roast-brain-history.json (주차별 정확도) · 리포트

사용법:
    python3 scripts/roast_brain.py [--local DIR] [--eval-only]
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import math
import pathlib
import re
import statistics
import sys

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scrapers'))
from roast_learning_lib import Store  # noqa: E402
from common import guess_process  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL_OUT = ROOT / 'data' / 'roast-brain.json'
HISTORY = ROOT / 'data' / 'roast-brain-history.json'
REPORT_DIR = ROOT / 'vault' / 'raw' / 'roast-profiles'
TODAY = datetime.date.today().isoformat()

TARGETS = {          # 이름: (라벨 필드, 양성 값, 설명)
    'under': ('under', 'yes', '언더·풋맛'),
    'over': ('over', 'yes', '탄맛·오버'),
    'baked': ('baked', 'yes', '베이크드·플랫'),
    'astringent': ('astringent', 'yes', '떫은맛'),
    'sour': ('sour_harsh', 'yes', '튀는 산미'),
    'bad': ('overall', 'bad', '전체 평가 나쁨'),
}
PROCESSES = ['워시드', '내추럴', '허니', '무산소발효', '웻훌드', '펄프드내추럴', '디카페인']
# 그래프에서 바로 알 수 있는 값 — 사이트 roasting.js 가 같은 정의로 계산한다
CURVE = ['total_min', 'dtr', 'dry_pct', 'mai_pct', 'drop_bt', 'charge_bt', 'tp_t', 'tp_bt',
         'ror150', 'ror200', 'ror_drop', 'ror_peak', 'crash', 'flick']
CONTEXT = ['charge_g', 'weight_loss', 'density', 'moisture'] + [f'proc_{p}' for p in PROCESSES]
# 같은 생두의 이전 로스팅들(최근 10회 중앙값) 대비 차이 — 같은 콩끼리 비교해야 맛 차이가 보인다
RELATIVE_BASE = ['dtr', 'drop_bt', 'total_min', 'ror200', 'dry_pct']
RELATIVE = [f'd_{k}' for k in RELATIVE_BASE] + ['prior_roasts']
FEATURES = CURVE + CONTEXT + RELATIVE
MIN_PRIOR = 3


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else math.nan
    except (TypeError, ValueError):
        return math.nan


def bean_key(r):
    return re.sub(r'[\s\-_/()\[\]]+', '', (r.get('beanName') or '').lower())[:40]


def build_rows(store: Store):
    rec = {r['id']: r for r in csv.DictReader(io.StringIO(store.get_text('seed/firescope/records.csv.gz')))}
    labels = store.get_json('seed/firescope/memo_labels.json.gz')['labels']
    rows = []
    for f in csv.DictReader(io.StringIO(store.get_text('seed/firescope/features30.csv.gz'))):
        r = rec.get(f['id'])
        if not r:
            continue
        d, t1, t2 = num(f['dur']), num(f['t150']), num(f['t200'])
        if not (240 < d < 1500) or math.isnan(t1) or math.isnan(t2) or t2 <= t1:
            continue
        wl = num(r.get('weightLossPct'))
        ca, da = num(r.get('chargeAmount')), num(r.get('dropAmount'))
        if math.isnan(wl) and ca > 0 and da > 0 and ca > da:
            wl = (ca - da) / ca * 100
        proc = guess_process(f'{r.get("process") or ""} {r.get("beanName") or ""}')
        x = {'total_min': d / 60, 'dtr': (d - t2) / d * 100, 'dry_pct': t1 / d * 100, 'mai_pct': (t2 - t1) / d * 100,
             'drop_bt': num(f['drop_bt']), 'charge_bt': num(f['charge_bt']), 'tp_t': num(f['tp_t']),
             'tp_bt': num(f['tp_bt']), 'ror150': num(f['ror150']), 'ror200': num(f['ror200']),
             'ror_drop': num(f['ror_drop']), 'ror_peak': num(f['ror_peak']), 'crash': num(f['crash']),
             'flick': num(f['flick']), 'charge_g': ca, 'weight_loss': wl if 5 < wl < 30 else math.nan,
             'density': num(r.get('density')), 'moisture': num(r.get('moisture'))}
        for p in PROCESSES:
            x[f'proc_{p}'] = 1.0 if proc == p else 0.0
        rows.append({'id': f['id'], 'date': r.get('roastedAt_KST') or '', 'bean': bean_key(r), 'x': x,
                     'label': labels.get(f['id'])})
    # 같은 생두의 '이전' 로스팅만으로 차이를 낸다 (미래 정보가 섞이지 않게)
    rows.sort(key=lambda r: r['date'])
    hist: dict[str, list] = {}
    for r in rows:
        prev = hist.get(r['bean'], []) if r['bean'] else []
        r['x']['prior_roasts'] = float(len(prev))
        for k in RELATIVE_BASE:
            vals = [p[k] for p in prev[-10:] if not math.isnan(p[k])]
            r['x'][f'd_{k}'] = r['x'][k] - statistics.median(vals) if len(vals) >= MIN_PRIOR else math.nan
        if r['bean']:
            hist.setdefault(r['bean'], []).append(r['x'])
    return rows


def evaluated(rows):
    return [r for r in rows if r['label'] and r['label'].get('kind') in ('evaluation', 'mixed')]


def target(rows, name):
    field, pos, _ = TARGETS[name]
    return np.array([1 if r['label'][field] == pos else 0 for r in rows])


def matrix(rows, cols):
    return np.array([[r['x'][c] for c in cols] for r in rows], float)


def make_model():
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                          min_samples_leaf=40, l2_regularization=1.0, random_state=0)


def evaluate(ev):
    """시간순 80/20 검증 + 학습 데이터 양을 늘려 가며 성능 추이."""
    cut = int(len(ev) * 0.8)
    out = {'n_eval_roasts': len(ev), 'train_until': ev[cut - 1]['date'][:10], 'test_from': ev[cut]['date'][:10],
           'n_test': len(ev) - cut, 'targets': {}}
    sets = {'curve': CURVE, 'curve+context': CURVE + CONTEXT, 'full': FEATURES}
    for name in TARGETS:
        y = target(ev, name)
        if y[:cut].sum() < 30 or y[cut:].sum() < 10:
            continue
        t = {'positives': int(y.sum()), 'rate': round(float(y.mean()), 4)}
        for sname, cols in sets.items():
            X = matrix(ev, cols)
            m = make_model().fit(X[:cut], y[:cut])
            t[f'auc_{sname}'] = round(roc_auc_score(y[cut:], m.predict_proba(X[cut:])[:, 1]), 3)
        X = matrix(ev, FEATURES)
        curve = {}
        for frac in (0.25, 0.5, 1.0):
            s = int(cut * (1 - frac))
            if y[s:cut].sum() < 20:
                continue
            m = make_model().fit(X[s:cut], y[s:cut])
            curve[str(frac)] = round(roc_auc_score(y[cut:], m.predict_proba(X[cut:])[:, 1]), 3)
        t['learning_curve'] = curve
        out['targets'][name] = t
    return out


def export_tree_model(m, cols):
    """사이트(브라우저)에서 돌릴 수 있게 결정 트리를 JSON 으로. x <= 임계값이면 왼쪽, 값 없음은 missing 방향."""
    def thr(n):
        if n['is_leaf']:
            return 0
        v = float(n['num_threshold'])          # 결측값만 가르는 분할은 임계값이 ±inf — JSON 에 못 담으므로 큰 수로
        return 1e300 if v == math.inf else -1e300 if v == -math.inf else float(f'{v:.7g}')

    trees = []
    for it in m._predictors:
        nodes = it[0].nodes
        trees.append([[int(n['feature_idx']), thr(n), int(n['missing_go_to_left']),
                       int(n['left']), int(n['right']), int(n['is_leaf']), float(f'{float(n["value"]):.6g}')]
                      for n in nodes])
    return {'base': round(float(m._baseline_prediction.ravel()[0]), 6), 'trees': trees}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', help='버킷 대신 쓸 로컬 폴더')
    ap.add_argument('--eval-only', action='store_true', help='검증만 하고 파일은 쓰지 않음')
    args = ap.parse_args()
    store = Store(args.local)
    rows = build_rows(store)
    ev = evaluated(rows)
    print(f'곡선 {len(rows)}건 · 맛 평가가 있는 로스팅 {len(ev)}건')
    res = evaluate(ev)
    for name, t in res['targets'].items():
        print(f'  · {TARGETS[name][2]:10s} 양성 {t["positives"]:>5} ({t["rate"]*100:4.1f}%)  AUC 그래프만 {t["auc_curve"]} · '
              f'+생두·감량 {t["auc_curve+context"]} · +같은 생두 비교 {t["auc_full"]}  | 데이터 25/50/100%: {t["learning_curve"]}')
    if args.eval_only:
        return
    # 배포용: 맛 평가가 있는 전체 기록으로 다시 학습
    models = {}
    for name in res['targets']:
        y = target(ev, name)
        m = make_model().fit(matrix(ev, FEATURES), y)
        models[name] = export_tree_model(m, FEATURES) | {'label': TARGETS[name][2], 'rate': res['targets'][name]['rate'],
                                                         'auc': res['targets'][name]['auc_full']}
    MODEL_OUT.write_text(json.dumps({'generated': TODAY, 'features': FEATURES, 'processes': PROCESSES,
                                     'n_train': len(ev), 'models': models}, ensure_ascii=False, separators=(',', ':')))
    hist = json.loads(HISTORY.read_text(encoding='utf-8')) if HISTORY.exists() else {'runs': []}
    hist['runs'] = [r for r in hist['runs'] if r['date'] != TODAY] + [{'date': TODAY, **res}]
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'✓ {MODEL_OUT.relative_to(ROOT)} ({MODEL_OUT.stat().st_size // 1024}KB) · {HISTORY.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
