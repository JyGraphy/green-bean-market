#!/usr/bin/env python3
"""로스팅 AI 누적 학습 ④ — 로스팅 판단 두뇌(자체 모델) 학습.

Claude 는 그래프를 읽고 설명하는 '눈과 입'이고, 맛 결과를 예측하는 '판단 두뇌'는 우리 기록으로
직접 학습한 이 모델이다. 매주 쌓인 기록 전체로 다시 학습하므로 기록이 늘수록 두뇌가 자란다.

학습 자료 (비공개 버킷 roast-learning):
  seed/firescope/features30.csv.gz    곡선 특징값 (총 시간·발달·배출·RoR …)
  seed/firescope/records.csv.gz       생두·투입량·감량·밀도·수분
  seed/firescope/memo_labels.json.gz  로스터 메모에서 AI가 정리한 맛 평가 (언더·오버·베이크드·떫은맛·산미·전체 평가)
  cupping/<사용자>.json               사이트에서 커핑 후 남긴 정해진 형식의 평가 + 그 프로파일 곡선 (roast-learn 함수)

예측 대상 (메모에 맛 평가가 있는 로스팅만 학습):
  under 언더·풋맛 · over 탄맛·오버 · baked 베이크드·플랫 · astringent 떫은맛 · sour 튀는 산미 · bad 전체 평가 나쁨

검증: 시간순으로 나눠 과거 80%로 학습하고 이후 20%(학습에 안 쓴 최근 기록)로 맞히는지 잰다 (AUC).
출력: data/roast-brain.json — 사이트가 읽는다
        rules  : 같은 생두를 같은 날 볶아 결과가 갈린 배치 쌍에서 확인된 차이 (피드백 근거)
        models : AUC 가 MIN_AUC 이상인 예측 모델만. 기준 미달이면 사이트에 예측을 띄우지 않는다
      data/roast-brain-history.json (주차별 정확도) · vault 리포트

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
MIN_AUC = 0.70          # 이보다 못 맞히는 모델은 사이트에 내보내지 않는다 (틀린 숫자는 잘못된 조언이 된다)
RULE_METRICS = {'drop_bt': '배출 온도', 'dtr': 'DTR', 'total_min': '총 시간', 'ror200': 'RoR@200', 'dry_pct': '건조 비율'}
RULE_MIN_PAIRS, RULE_MIN_SHARE = 100, 0.60


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else math.nan
    except (TypeError, ValueError):
        return math.nan


def bean_key(r):
    return re.sub(r'[\s\-_/()\[\]]+', '', (r.get('beanName') or '').lower())[:40]


def context_x(x, charge_g, weight_loss, density, moisture, proc_text):
    x.update({'charge_g': charge_g, 'weight_loss': weight_loss if 5 < weight_loss < 30 else math.nan,
              'density': density, 'moisture': moisture})
    proc = guess_process(proc_text)
    for p in PROCESSES:
        x[f'proc_{p}'] = 1.0 if proc == p else 0.0
    return x


def curve_features_1s(times, bts):
    """사이트 프로파일 곡선 → 특징값. roast-brain.js curveFeatures 와 줄 단위로 같다 (fs_feat 정의)."""
    if not times or len(times) < 2 or len(times) != len(bts) or any(v is None for v in bts):
        return None
    t0, end = math.ceil(times[0]), math.floor(times[-1])
    B = list(np.interp(np.arange(t0, end + 1), np.asarray(times, float), np.asarray(bts, float)))
    n = len(B)
    if n < 120:
        return None
    tp = min(range(min(n, 150)), key=lambda i: (B[i], i))
    m = max(range(tp, n), key=lambda i: (B[i], -i))
    if m < n - 1:
        B = B[:m + 1]
        n = len(B)
    first = lambda th: next((i for i in range(tp, n) if B[i] >= th), None)  # noqa: E731
    i150, i200 = first(150), first(200)
    R = [(B[i] - B[max(0, i - 30)]) * 60 / (i - max(0, i - 30)) if i > 0 else None for i in range(n)]
    post = [r for r in R[max(tp + 60, 0):] if r is not None]
    crash = flick = 0
    if i200:
        seg = [r for r in R[i200:] if r is not None]
        crash = int(any(seg[a] - seg[a + 30] >= 5 for a in range(0, len(seg) - 30, 5)))
        mn = math.inf
        for v in seg:
            mn = min(mn, v)
            if v - mn >= 1.5:
                flick = 1
                break
    T = lambda i: t0 + i  # noqa: E731
    dur = T(n - 1)
    if not (240 < dur < 1500) or not i150 or not i200 or i200 <= i150:
        return None
    r2 = lambda v: round(v, 2) if v is not None else math.nan  # noqa: E731
    return {'total_min': dur / 60, 'dtr': (dur - T(i200)) / dur * 100, 'dry_pct': T(i150) / dur * 100,
            'mai_pct': (T(i200) - T(i150)) / dur * 100, 'drop_bt': B[n - 1], 'charge_bt': B[0], 'tp_t': float(T(tp)),
            'tp_bt': B[tp], 'ror150': r2(R[i150]), 'ror200': r2(R[i200]), 'ror_drop': r2(R[n - 1]),
            'ror_peak': round(max(post), 2) if post else math.nan, 'crash': float(crash), 'flick': float(flick)}


def site_rows(store: Store):
    """사이트 커핑 결과 → 학습 행. 같은 생두 비교는 사용자별로 (다른 사람 기록과 섞지 않는다)."""
    rows = []
    for path in store.list('cupping'):
        if not path.endswith('.json'):
            continue
        try:
            doc = store.get_json(path)
        except Exception:  # noqa: BLE001
            continue
        for pid, it in (doc.get('items') or {}).items():
            p, c = it.get('profile') or {}, it.get('cupping') or {}
            f = curve_features_1s(p.get('time_series'), p.get('bt_series'))
            if not f:
                continue
            ov = c.get('overall')
            label = {'kind': 'evaluation', 'under': 'yes' if c.get('under') else 'unknown',
                     'over': 'yes' if c.get('over') else 'unknown', 'baked': 'yes' if c.get('baked') else 'unknown',
                     'astringent': 'yes' if c.get('astringent') else 'unknown',
                     'sour_harsh': 'yes' if c.get('sour') else 'unknown',
                     'overall': 'unknown' if ov is None else 'bad' if ov <= 2 else 'ok' if ov == 3 else 'good'}
            x = context_x(f, num(p.get('charge_weight')), num(p.get('weight_loss')), math.nan, math.nan,
                          p.get('bean_name') or '')
            rows.append({'id': f'site:{pid}', 'source': 'site', 'date': p.get('roast_date') or p.get('created_at') or '',
                         'bean': f'{doc.get("user_id", path)}:{bean_key({"beanName": p.get("bean_name")})}',
                         'x': x, 'label': label})
    return rows


def firescope_rows(store: Store):
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
        x = {'total_min': d / 60, 'dtr': (d - t2) / d * 100, 'dry_pct': t1 / d * 100, 'mai_pct': (t2 - t1) / d * 100,
             'drop_bt': num(f['drop_bt']), 'charge_bt': num(f['charge_bt']), 'tp_t': num(f['tp_t']),
             'tp_bt': num(f['tp_bt']), 'ror150': num(f['ror150']), 'ror200': num(f['ror200']),
             'ror_drop': num(f['ror_drop']), 'ror_peak': num(f['ror_peak']), 'crash': num(f['crash']),
             'flick': num(f['flick'])}
        context_x(x, ca, wl, num(r.get('density')), num(r.get('moisture')),
                  f'{r.get("process") or ""} {r.get("beanName") or ""}')
        rows.append({'id': f['id'], 'source': 'firescope', 'date': r.get('roastedAt_KST') or '', 'bean': bean_key(r),
                     'x': x, 'label': labels.get(f['id'])})
    return rows


def build_rows(store: Store):
    rows = firescope_rows(store) + site_rows(store)
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


def pair_rules(ev):
    """같은 생두를 같은 날 볶아 결과가 갈린 배치 쌍: 나쁜 쪽 배치가 어느 방향으로 달랐나.
    같은 방향 비율이 RULE_MIN_SHARE 이상이고 쌍이 RULE_MIN_PAIRS 이상인 지표만 규칙으로 남긴다."""
    groups: dict = {}
    for r in ev:
        if r['bean']:
            groups.setdefault((r['bean'], r['date'][:10]), []).append(r)
    rules = {}
    for name, (field, pos, label) in TARGETS.items():
        diffs = {k: [] for k in RULE_METRICS}
        for g in groups.values():
            P = [r for r in g if r['label'][field] == pos]
            N = [r for r in g if r['label'][field] != pos]
            for a in P:
                for b in N:
                    for k in RULE_METRICS:
                        va, vb = a['x'][k], b['x'][k]
                        if not (math.isnan(va) or math.isnan(vb)) and va != vb:
                            diffs[k].append(va - vb)
        metrics = {}
        for k, v in diffs.items():
            if len(v) < RULE_MIN_PAIRS:
                continue
            mean = statistics.mean(v)
            share = sum(1 for x in v if (x > 0) == (mean > 0)) / len(v)
            if share >= RULE_MIN_SHARE:
                metrics[k] = {'name': RULE_METRICS[k], 'mean': round(mean, 2), 'share': round(share, 2), 'pairs': len(v)}
        if metrics:
            rules[name] = {'label': label, 'metrics': metrics}
    return rules


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


def write_report(res, rules, shipped, n_rows, n_site):
    names = {k: v[2] for k, v in TARGETS.items()}
    L = ['# 로스팅 판단 두뇌 주간 학습', '',
         f'**작성일**: {TODAY} · **담당**: scripts/roast_brain.py (매주 자동) · **신뢰도**: 상 (학습에 안 쓴 최근 기록으로 검증)', '',
         '## 📌 결론 3줄', '',
         f'1. 맛 평가가 있는 로스팅 **{res["n_eval_roasts"]}건** (그중 사이트 커핑 기록 **{n_site}건**) 으로 다시 학습',
         f'2. 사이트에 켜진 예측: **{", ".join(names[k] for k in shipped) or "없음"}** — 정확도(AUC) {MIN_AUC} 이상만 켠다',
         f'3. 같은 생두 비교 근거 규칙 **{len(rules)}개** 를 피드백에 사용', '',
         '## 예측 정확도 (AUC, 0.5 = 동전 던지기)', '',
         '| 맛 결과 | 평가 수 | 그래프만 | + 생두·감량 | + 같은 생두 비교 | 사이트 |', '|---|---|---|---|---|---|']
    for k, t in res['targets'].items():
        L.append(f'| {names[k]} | {t["positives"]} | {t["auc_curve"]} | {t["auc_curve+context"]} | {t["auc_full"]} | '
                 f'{"켜짐" if k in shipped else "기준 미달"} |')
    L += ['', f'학습 {res["train_until"]} 까지 · 시험 {res["test_from"]} 부터 {res["n_test"]}건.', '',
          '## 같은 생두·같은 날 배치 비교 규칙', '', '| 나쁜 결과 | 지표 | 나쁜 쪽 평균 차이 | 같은 방향 | 쌍 |', '|---|---|---|---|---|']
    for k, r in rules.items():
        for m in r['metrics'].values():
            L.append(f'| {r["label"]} | {m["name"]} | {m["mean"]:+} | {round(m["share"] * 100)}% | {m["pairs"]} |')
    L += ['', '## 두뇌가 자라는 방식', '',
          '사이트에서 커핑 결과(정해진 형식)와 1차 크랙을 기록할수록 학습 정답이 늘어난다. 매주 다시 학습해 정확도가 '
          f'{MIN_AUC} 를 넘는 항목부터 사이트 예측이 자동으로 켜진다. 곡선 {n_rows}건 중 맛 평가가 붙은 것만 학습에 쓴다.',
          '', '## 출처', '', '- 비공개 버킷 `roast-learning` (seed/firescope · cupping) — 1차', '']
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f'{TODAY}-판단두뇌.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', help='버킷 대신 쓸 로컬 폴더')
    ap.add_argument('--eval-only', action='store_true', help='검증만 하고 파일은 쓰지 않음')
    args = ap.parse_args()
    store = Store(args.local)
    rows = build_rows(store)
    ev = evaluated(rows)
    n_site = sum(1 for r in ev if r['source'] == 'site')
    print(f'곡선 {len(rows)}건 · 맛 평가가 있는 로스팅 {len(ev)}건 (사이트 커핑 {n_site}건)')
    res = evaluate(ev)
    for name, t in res['targets'].items():
        print(f'  · {TARGETS[name][2]:10s} 양성 {t["positives"]:>5} ({t["rate"]*100:4.1f}%)  AUC 그래프만 {t["auc_curve"]} · '
              f'+생두·감량 {t["auc_curve+context"]} · +같은 생두 비교 {t["auc_full"]}  | 데이터 25/50/100%: {t["learning_curve"]}')
    rules = pair_rules(ev)
    for k, r in rules.items():
        print(f'  규칙 {r["label"]}: ' + ', '.join(f'{m["name"]} {m["mean"]:+} ({round(m["share"]*100)}%, {m["pairs"]}쌍)'
                                                 for m in r['metrics'].values()))
    if args.eval_only:
        return
    # 배포용: 기준을 넘은 항목만 전체 기록으로 다시 학습해 내보낸다
    shipped, models = [], {}
    for name, t in res['targets'].items():
        if t['auc_full'] < MIN_AUC:
            continue
        m = make_model().fit(matrix(ev, FEATURES), target(ev, name))
        models[name] = export_tree_model(m, FEATURES) | {'label': TARGETS[name][2], 'rate': t['rate'], 'auc': t['auc_full']}
        shipped.append(name)
    accuracy = {k: {'label': TARGETS[k][2], 'auc': t['auc_full'], 'rate': t['rate']} for k, t in res['targets'].items()}
    MODEL_OUT.write_text(json.dumps({
        'generated': TODAY, 'n_train': len(ev), 'n_site': n_site, 'min_auc': MIN_AUC,
        'features': FEATURES, 'processes': PROCESSES, 'accuracy': accuracy, 'rules': rules, 'models': models,
    }, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    hist = json.loads(HISTORY.read_text(encoding='utf-8')) if HISTORY.exists() else {'runs': []}
    hist['runs'] = [r for r in hist['runs'] if r['date'] != TODAY] + [
        {'date': TODAY, 'n_site': n_site, 'shipped': shipped, **res}]
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    report = write_report(res, rules, shipped, len(rows), n_site)
    print(f'✓ {MODEL_OUT.relative_to(ROOT)} ({MODEL_OUT.stat().st_size // 1024}KB, 켜진 예측 {shipped or "없음"}) · '
          f'{HISTORY.relative_to(ROOT)} · {report.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
