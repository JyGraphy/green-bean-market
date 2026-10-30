#!/usr/bin/env python3
"""로스팅 AI 누적 학습 ③ — 판독 정확도 재측정 (벤치마크).

정답이 있는 판독 사례를 매주 **지금의 사이트 코드**로 다시 판독해 정확도를 잰다.
사례는 계속 늘어난다:
  seed/benchmark/manifest.json   처음 만든 검증 사례 (Boost 화면 + Boost 초 단위 데이터, IKAWA 화면 표시값)
  readings/**.json               사이트에서 사진과 데이터 파일을 함께 올린 분석 (데이터 파일 = 정답, 사진 동의 시)

  --reanalyze N   현재 프롬프트로 아직 판독하지 않은 사례를 N건까지 analyze-roast 로 새로 판독한다.
                  규칙을 고친 효과가 실제 AI 판독에 나타났는지 이것으로 확인한다.
                  판독 결과는 버킷 benchmark/ai/<프롬프트 버전>/ 에 저장하고 다시 쓴다 —
                  프롬프트(analyze-roast 소스)가 바뀌지 않은 주에는 AI 호출이 0건이다.

출력 (공개 저장소에는 집계만):
  data/roast-benchmark-history.json                 주차별 정확도 추이
  vault/raw/roast-profiles/<날짜>-판독벤치마크.md     리포트
  --feedback-out FILE                               정답 있는 사이트 사례의 'AI 판독 vs 정답' 행
                                                    (roast_feedback.py --extra 로 넘겨 기기 규칙에 반영)

사용법:
    python3 scripts/roast_benchmark.py [--reanalyze 20] [--feedback-out rows.json] [--local DIR]
"""
from __future__ import annotations

import argparse
import base64
import datetime
import hashlib
import io
import json
import os
import pathlib
import re
import statistics
import subprocess
import sys
import tempfile
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from roast_learning_lib import Store  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
HISTORY = ROOT / 'data' / 'roast-benchmark-history.json'
REPORT_DIR = ROOT / 'vault' / 'raw' / 'roast-profiles'
EVAL_JS = ROOT / 'scripts' / 'roast_pixel_eval.js'
ANALYZE_FN = ROOT / 'supabase' / 'functions' / 'analyze-roast' / 'index.ts'
MAX_SIDE = 2600            # roasting.js imageDataFromUrl 과 같은 축소 기준
SUPABASE_URL = os.environ.get('SUPABASE_URL') or 'https://txnpbzukavajwbmggpfk.supabase.co'
SUPABASE_ANON = 'sb_publishable_KeqUfylPUoX8YSCbKGjqEQ_pQCzFFBF'   # 공개 키 (supabase.config.js 와 같음)
TODAY = datetime.date.today().isoformat()


def prompt_version() -> str:
    """analyze-roast 소스(프롬프트·모델 포함)의 해시. 이게 같으면 AI 판독도 같으므로 다시 부르지 않는다."""
    return hashlib.sha256(ANALYZE_FN.read_bytes()).hexdigest()[:12]


def case_key(case_id: str) -> str:
    return re.sub(r'[^0-9A-Za-z_-]+', '_', case_id)


def media_type(path: str) -> str:
    ext = path.rsplit('.', 1)[-1].lower()
    return {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'image/png')


def load_cases(store: Store) -> list[dict]:
    cases = []
    man = store.get_json('seed/benchmark/manifest.json')
    for c in man['cases']:
        cases.append({'id': c['id'], 'set': c.get('set', 'seed'), 'screen_type': c.get('screen_type'),
                      'roaster': c.get('machine') or '', 'image': c['image'],
                      'ai': store.get_json(c['ai']), 'truth': store.get_json(c['truth'])})
    for p in store.list('readings'):
        if not p.endswith('.json'):
            continue
        try:
            r = store.get_json(p)
        except Exception:  # noqa: BLE001
            continue
        t = r.get('truth') or {}
        if not (t.get('bt') and r.get('images') and r.get('ai_raw')):
            continue
        cases.append({'id': f'site/{r["id"]}', 'set': 'site', 'screen_type': r.get('screen_type'),
                      'roaster': r.get('roaster_input') or r.get('machine') or '', 'image': r['images'][0],
                      'ai': r['ai_raw'], 'truth': t, 'reading': r})
    return cases


def reanalyze(store: Store, case: dict, img: bytes, ver: str) -> dict | None:
    body = json.dumps({'images': [{'base64': base64.b64encode(img).decode(),
                                   'media_type': media_type(case['image'])}]}).encode()
    req = urllib.request.Request(f'{SUPABASE_URL.rstrip("/")}/functions/v1/analyze-roast', data=body, method='POST',
                                 headers={'Content-Type': 'application/json', 'apikey': SUPABASE_ANON,
                                          'Authorization': f'Bearer {SUPABASE_ANON}'})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            ai = json.loads(r.read().decode('utf-8'))
    except Exception as e:  # noqa: BLE001
        print(f'  ⚠️ 재판독 실패 {case["id"]}: {e}')
        return None
    if ai.get('error'):
        print(f'  ⚠️ 재판독 오류 {case["id"]}: {ai["error"]}')
        return None
    store.put(f'benchmark/ai/{ver}/{case_key(case["id"])}.ai.json', json.dumps(ai, ensure_ascii=False).encode('utf-8'))
    return ai


def to_rgba(img: bytes, out: pathlib.Path):
    from PIL import Image
    im = Image.open(io.BytesIO(img)).convert('RGBA')
    k = min(1.0, MAX_SIDE / max(im.size))
    if k < 1:
        im = im.resize((round(im.width * k), round(im.height * k)), Image.BILINEAR)
    out.write_bytes(im.tobytes())
    return im.width, im.height


def med(vals):
    v = [x for x in vals if isinstance(x, (int, float))]
    return round(statistics.median(v), 2) if v else None


def summarize(results: list[dict]) -> dict:
    groups = {}
    for r in results:
        if r.get('error'):
            continue
        key = f'{r["set"]}:{r.get("screen_type") or "other"}'      # tuned(규칙 만들 때 본 사례)·holdout(안 본 사례)·site
        groups.setdefault(key, []).append(r)
    out = {}
    for key, rs in sorted(groups.items()):
        out[key] = {
            'n': len(rs),
            'pixel_ok': sum(1 for r in rs if r['pixel']['ok']),
            'bt_mae': med(r['site'].get('bt_mae') for r in rs),
            'bt_max': med(r['site'].get('bt_max') for r in rs),
            'et_mae': med(r['site'].get('et_mae') for r in rs),
            'ror_mae': med(r['site'].get('ror_mae') for r in rs),
            'agit_match': med(r['site'].get('agit_match') for r in rs),
            'anchor_mae': med(r['site'].get('anchor_mae') for r in rs),
            'ai_bt_mae': med(r['ai'].get('bt_mae') for r in rs),
            'ai_ror_mae': med(r['ai'].get('ror_mae') for r in rs),
            'drop_t_err': med(r.get('drop_t_err') for r in rs),
            'drop_temp_err': med(r.get('drop_temp_err') for r in rs),
            'tp_err': med(r.get('tp_err') for r in rs),
        }
    return out


def git_rev() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
    except Exception:  # noqa: BLE001
        return ''


# 커질수록 나쁜 지표 / 커질수록 좋은 지표 — 퇴보 판정용 (이보다 작게 변하면 잡음으로 본다)
WORSE_IF_UP = {'bt_mae': 0.5, 'et_mae': 0.5, 'ror_mae': 0.5, 'anchor_mae': 0.5,
               'drop_t_err': 3, 'drop_temp_err': 0.5, 'tp_err': 3}
WORSE_IF_DOWN = {'agit_match': 5}


def regressions(cur: dict, prev: dict) -> list[str]:
    out = []
    for g, c in cur.items():
        p = prev.get(g)
        if not p or p.get('n') != c.get('n'):      # 사례 수가 바뀌면 직접 비교하지 않는다
            continue
        if c['pixel_ok'] < p['pixel_ok']:
            out.append(f'{g}: 픽셀 추출 성공 {p["pixel_ok"]} → {c["pixel_ok"]}/{c["n"]}')
        for m, tol in WORSE_IF_UP.items():
            if c.get(m) is not None and p.get(m) is not None and c[m] - p[m] > tol:
                out.append(f'{g}: {m} {p[m]} → {c[m]}')
        for m, tol in WORSE_IF_DOWN.items():
            if c.get(m) is not None and p.get(m) is not None and p[m] - c[m] > tol:
                out.append(f'{g}: {m} {p[m]} → {c[m]}')
    return out


def feedback_rows(cases: list[dict], results: list[dict]) -> list[dict]:
    """정답이 있는 사이트 사례 → roast_feedback.py 가 읽는 roasting_profiles 행 모양.
    '사용자 수정값' 자리에 데이터 파일 정답을 넣는다. 투입 온도는 데이터 파일의 첫 샘플이
    투입 전일 수 있어 비교하지 않는다."""
    rows = []
    for c in cases:
        if c['set'] != 'site':
            continue
        t, ai = c['truth'], c['ai']
        m = re.search(r'machine\s*:\s*([^.,;\n]+)', ai.get('notes') or '', re.I)
        drop_t = (t.get('events') or {}).get('drop') or t.get('drop_t')
        drop_temp = None
        if drop_t and t.get('bt'):
            drop_temp = min(t['bt'], key=lambda p: abs(p[0] - drop_t))[1]
        rows.append({'roaster': c['roaster'], 'ai_raw': ai, 'ai_confidence': ai.get('confidence'),
                     'ai_machine': m.group(1).strip() if m else None, 'ai_input_kind': 'photo+datafile',
                     'charge_temp': None, 'drop_temp': drop_temp, 'total_time': drop_t,
                     'events': t.get('events') or {}})
    return rows


def fmt(v, unit=''):
    return '—' if v is None else f'{v}{unit}'


def write_report(summary: dict, prev_run: dict | None, results: list[dict], regs: list[str], ai_stat: dict):
    names = {'tuned:boost_web': 'Boost 웹 · 조정용', 'holdout:boost_web': 'Boost 웹 · 미사용(holdout)',
             'tuned:ikawa_app': 'IKAWA 앱 · 조정용', 'site:boost_web': 'Boost 웹 · 사이트 실사용',
             'site:ikawa_app': 'IKAWA 앱 · 사이트 실사용'}
    L = ['# 로스팅 AI 판독 벤치마크', '',
         f'**작성일**: {TODAY} · **담당**: scripts/roast_benchmark.py (매주 자동) · **신뢰도**: 상 (정답 데이터와 직접 비교)', '',
         '## 📌 결론 3줄', '']
    total = sum(g['n'] for g in summary.values())
    site_n = sum(g['n'] for k, g in summary.items() if k.startswith('site:'))
    ok = sum(g['pixel_ok'] for g in summary.values())
    L += [f'1. 정답 있는 판독 사례 **{total}건** (그중 사이트 실사용에서 쌓인 사례 **{site_n}건**) 을 현재 코드로 다시 판독',
          f'2. 사진에서 곡선을 픽셀로 직접 뽑은 경우 **{ok}/{total}건**'
          + (' — 나머지는 AI 판독 곡선을 앵커로 보정해 사용' if ok < total else ''),
          ('3. ⚠️ 지난번보다 나빠진 지표: ' + '; '.join(regs)) if regs else
          '3. 지난번 대비 퇴보한 지표 없음' + ('' if prev_run else ' (첫 측정)'), '']
    L += ['## 화면 종류별 정확도 (중앙값)', '',
          '| 구분 | 사례 | 픽셀 추출 | BT 오차 | ET 오차 | RoR 오차 | 교반 일치 | 앵커 오차 | AI 곡선만 BT 오차 | 배출 시점 | 배출 온도 |',
          '|---|---|---|---|---|---|---|---|---|---|---|']
    for k, g in summary.items():
        L.append(f'| {names.get(k, k)} | {g["n"]} | {g["pixel_ok"]}/{g["n"]} | {fmt(g["bt_mae"], "°C")} | '
                 f'{fmt(g["et_mae"], "°C")} | {fmt(g["ror_mae"], "°C/분")} | {fmt(g["agit_match"], "%")} | '
                 f'{fmt(g["anchor_mae"], "°C")} | {fmt(g["ai_bt_mae"], "°C")} | {fmt(g["drop_t_err"], "초")} | '
                 f'{fmt(g["drop_temp_err"], "°C")} |')
    L += ['', '- **조정용**은 판독 규칙을 만들 때 본 사례, **holdout**은 한 번도 보지 않은 사례 — 실제 성능은 holdout·실사용 쪽을 본다.',
          '- **BT/ET 오차**: 정답 곡선과 5초 간격 평균 절대 오차. **RoR 오차**: 30초 창 RoR, 투입 90초 이후.',
          '- **앵커 오차**: 곡선 정답이 없는 사례(IKAWA 화면)에서 화면에 적힌 값과의 차이.',
          '- **AI 곡선만**: 픽셀 추출을 쓰지 않았을 때(예전 방식)의 오차 — 하이브리드 판독의 효과 비교용.',
          f'- AI 판독 (프롬프트 버전 `{ai_stat["prompt"]}`): 이 버전으로 저장해 둔 판독 재사용 {ai_stat["cached"]}건 · '
          f'새로 판독 {ai_stat["new"]}건 · 예전 판독 사용 {ai_stat["old"]}건. 프롬프트가 바뀌지 않으면 AI를 다시 부르지 않는다.',
          '']
    if prev_run:
        L += [f'## 지난번({prev_run["date"]}) 대비', '', '| 구분 | 지표 | 지난번 | 이번 |', '|---|---|---|---|']
        for k, g in summary.items():
            p = (prev_run.get('groups') or {}).get(k) or {}
            for m in ('bt_mae', 'ror_mae', 'agit_match', 'anchor_mae', 'drop_t_err'):
                if g.get(m) is not None or p.get(m) is not None:
                    L.append(f'| {names.get(k, k)} | {m} | {fmt(p.get(m))} | {fmt(g.get(m))} |')
        L.append('')
    fails = [r for r in results if not r.get('error') and not r['pixel']['ok']]
    if fails:
        L += ['## 픽셀 추출이 안 된 사례', '']
        for r in fails:
            label = r['id'] if r['set'] != 'site' else f'사이트 사례 ({r.get("screen_type") or "기타"})'
            L.append(f'- {label}: {r["pixel"]["reason"]}')
        L.append('')
    errs = [r for r in results if r.get('error')]
    if errs:
        L += ['## 평가 오류', ''] + [f'- {r["id"] if r["set"] != "site" else "사이트 사례"}: {r["error"]}' for r in errs] + ['']
    L += ['## 이 단계의 위치', '',
          '매주 `roast-learning.yml`: Boost 신규 기록 동기화 → 기준선 재계산(`roast_baselines.py`) → '
          '**판독 재측정(이 리포트)** → 오차 패턴을 기기 규칙에 반영(`roast_feedback.py`) → 프롬프트 주입·배포.',
          '사례·기록은 비공개 Supabase 버킷 `roast-learning` 에 쌓이고 공개 저장소에는 집계만 남는다.', '']
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f'{TODAY}-판독벤치마크.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--reanalyze', type=int, default=0, help='현재 AI 프롬프트로 다시 판독할 최대 사례 수')
    ap.add_argument('--feedback-out', help='roast_feedback.py --extra 로 넘길 행 파일')
    ap.add_argument('--local', help='버킷 대신 쓸 로컬 폴더')
    args = ap.parse_args()
    store = Store(args.local)

    cases = load_cases(store)
    print(f'판독 사례 {len(cases)}건 (사이트 {sum(1 for c in cases if c["set"] == "site")}건)')
    ver = prompt_version()
    stored = {pathlib.Path(p).name for p in store.list(f'benchmark/ai/{ver}')}
    n_re = n_cached = 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        jobs = []
        for i, c in enumerate(cases):
            job = {k: c[k] for k in ('id', 'set', 'screen_type', 'roaster', 'ai', 'truth')}
            try:
                img = store.get(c['image'])
                name = f'{case_key(c["id"])}.ai.json'
                if name in stored:
                    job['ai'] = c['ai'] = store.get_json(f'benchmark/ai/{ver}/{name}')
                    n_cached += 1
                elif n_re < args.reanalyze:
                    ai = reanalyze(store, c, img, ver)
                    if ai:
                        job['ai'] = c['ai'] = ai
                        n_re += 1
                w, h = to_rgba(img, tmp / f'{i}.rgba')
                job.update(rgba=str(tmp / f'{i}.rgba'), w=w, h=h)
            except Exception as e:  # noqa: BLE001 — 이미지 하나 문제로 전체를 멈추지 않는다
                print(f'  ⚠️ 이미지 처리 실패 {c["id"] if c["set"] != "site" else "사이트 사례"}: {e}')
            jobs.append(job)
        (tmp / 'jobs.json').write_text(json.dumps(jobs, ensure_ascii=False), encoding='utf-8')
        res = subprocess.run(['node', str(EVAL_JS), str(tmp / 'jobs.json')], capture_output=True, text=True)
        if res.returncode:
            raise SystemExit(f'평가기 실패: {res.stderr[-2000:]}')
        results = json.loads(res.stdout)

    summary = summarize(results)
    hist = json.loads(HISTORY.read_text(encoding='utf-8')) if HISTORY.exists() else {'runs': []}
    prev = next((r for r in reversed(hist['runs']) if r['date'] != TODAY), None)
    regs = regressions(summary, (prev or {}).get('groups') or {})
    hist['runs'] = [r for r in hist['runs'] if r['date'] != TODAY] + [
        {'date': TODAY, 'code': git_rev(), 'prompt': ver, 'cases': len(results), 'reanalyzed': n_re,
         'ai_cached': n_cached, 'groups': summary}]
    hist['runs'] = hist['runs'][-200:]
    HISTORY.parent.mkdir(exist_ok=True)
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    ai_stat = {'prompt': ver, 'cached': n_cached, 'new': n_re, 'old': len(cases) - n_cached - n_re}
    report = write_report(summary, prev, results, regs, ai_stat)
    print(f'AI 판독: 프롬프트 {ver} · 재사용 {n_cached} · 새로 {n_re} · 예전 판독 {ai_stat["old"]}')

    for k, g in summary.items():
        print(f'  · {k:18s} n={g["n"]:<3} 픽셀 {g["pixel_ok"]}/{g["n"]}  BT {fmt(g["bt_mae"])}  ET {fmt(g["et_mae"])}  '
              f'RoR {fmt(g["ror_mae"])}  교반 {fmt(g["agit_match"])}  앵커 {fmt(g["anchor_mae"])}  AI만 BT {fmt(g["ai_bt_mae"])}')
    for r in regs:
        print(f'::warning title=판독 정확도 퇴보::{r}')
    print(f'✓ {HISTORY.relative_to(ROOT)} · {report.relative_to(ROOT)}')

    if args.feedback_out:
        rows = feedback_rows(cases, results)
        pathlib.Path(args.feedback_out).write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
        print(f'✓ 피드백 행 {len(rows)}건 → {args.feedback_out}')


if __name__ == '__main__':
    main()
