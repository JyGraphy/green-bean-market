#!/usr/bin/env python3
"""로스팅 AI 자동 학습 — 실제 업로드 데이터로 판독 오차를 찾아 규칙에 되먹인다.

**이 스크립트가 하는 일**
사이트의 로스팅 프로파일 카테고리에 로스터가 차트를 올리면 analyze-roast(AI)가 값을 읽고,
사용자는 마법사에서 그 값을 고친 뒤 저장한다. 그 **수정분이 곧 AI의 오답 노트**다.
이 스크립트는 Supabase에서 그 데이터를 읽어 기기별로 오차 패턴을 집계하고,
`vault/raw/roast-profiles/machines/<기기>.md` 의 "관측된 오차" 절을 자동 갱신한다.
이후 build_roast_knowledge.py 가 그 내용을 프롬프트에 주입하면 학습이 완료된다.

**왜 이게 학습인가**: analyze-roast 는 파인튜닝 모델이 아니라 프롬프트 기반이다.
실사용 오차를 판독 규칙 문장으로 바꿔 프롬프트에 넣는 것이 이 구조에서의 학습이다.

**개인정보**: 집계만 한다. user_id·bean_name·memo 등은 읽지도 저장하지도 않는다.

필요 환경변수 (GitHub Actions 시크릿):
    SUPABASE_URL              예) https://xxxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY RLS를 우회해 전체 집계를 읽기 위해 필요

사용법:
    python3 scripts/roast_feedback.py            # 집계 + 기기 문서 갱신
    python3 scripts/roast_feedback.py --dry-run  # 집계만 출력, 파일 수정 없음
"""
from __future__ import annotations

import argparse
import collections
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
MACHINES = ROOT / 'vault' / 'raw' / 'roast-profiles' / 'machines'
REPORT_DIR = ROOT / 'vault' / 'raw' / 'roast-profiles'

# 집계에 필요한 컬럼만 선택 — 개인정보 컬럼은 아예 요청하지 않는다.
COLUMNS = ('id,created_at,roaster,ai_raw,ai_confidence,ai_machine,ai_input_kind,'
           'charge_temp,drop_temp,total_time,events')

SECTION = '## 관측된 오차 (실사용 피드백)'
# 이 절은 스크립트가 관리한다. 사람이 쓴 '## 판독 규칙' 은 건드리지 않는다.

# 오차로 볼 최소 차이 (이보다 작으면 판독 성공으로 본다)
TEMP_TOL = 3.0      # °C
EVENT_TOL = 10.0    # 초
MIN_SAMPLES = 3     # 이 미만이면 패턴으로 단정하지 않는다


def fetch_rows(limit=1000) -> list[dict]:
    url = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    if not url or not key:
        print('⚠️ SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 없어 집계를 건너뜁니다.')
        print('   GitHub 저장소 Settings → Secrets → Actions 에 등록하면 자동 학습이 켜집니다.')
        return []
    q = urllib.parse.urlencode({
        'select': COLUMNS,
        'ai_raw': 'not.is.null',       # AI 판독 흔적이 있는 것만
        'order': 'created_at.desc',
        'limit': str(limit),
    })
    req = urllib.request.Request(
        f'{url}/rest/v1/roasting_profiles?{q}',
        headers={'apikey': key, 'Authorization': f'Bearer {key}', 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001 — 어떤 실패든 학습을 막지 않는다
        print(f'✗ Supabase 조회 실패: {type(e).__name__}: {e}')
        return []


def ev(d, k):
    """events(jsonb 또는 dict)에서 초 단위 값을 꺼낸다."""
    if not isinstance(d, dict):
        return None
    v = d.get(k)
    return float(v) if isinstance(v, (int, float)) else None


def diff_row(row: dict) -> dict | None:
    """한 건에서 'AI 판독 vs 최종 저장' 차이를 뽑는다."""
    ai = row.get('ai_raw')
    if not isinstance(ai, dict):
        return None
    # 집계 기준은 **사용자가 선언한 로스터기**다. 사용자가 실제로 쓴 기기가 정답이므로,
    # AI가 오인한 기기 쪽에 오차를 적으면 엉뚱한 문서에 규칙이 쌓인다.
    out = {'issues': [], 'machine': (row.get('roaster') or row.get('ai_machine') or '미지정').strip(),
           'declared': (row.get('roaster') or '').strip(),
           'detected': (row.get('ai_machine') or '').strip(),
           'confidence': row.get('ai_confidence') or 'medium',
           'input_kind': row.get('ai_input_kind') or 'photo'}

    # 1) 기기 오인 — 사용자가 고른 로스터기와 AI 판독이 다름
    if out['declared'] and out['detected']:
        a, b = out['declared'].lower(), out['detected'].lower()
        if a not in b and b not in a:
            out['issues'].append(('machine_mismatch',
                                  f'이 기기를 "{out["detected"]}"(으)로 오인'))

    # 2) 온도 판독 오차
    for col, aikey, label in (('charge_temp', 'charge_temp', '투입온도'),
                              ('drop_temp', 'drop_temp', '배출온도')):
        fin, raw = row.get(col), ai.get(aikey)
        if isinstance(fin, (int, float)) and isinstance(raw, (int, float)):
            d = float(fin) - float(raw)
            if abs(d) > TEMP_TOL:
                out['issues'].append((f'temp_{col}', f'{label} {d:+.1f}°C (AI {raw} → 저장 {fin})'))

    # 3) 이벤트 시점 오차
    ai_ev = ai.get('events') if isinstance(ai.get('events'), dict) else {}
    fin_ev = row.get('events') if isinstance(row.get('events'), dict) else {}
    for k, label in (('tp', '터닝포인트'), ('dry', '건조종료'), ('fcs', '1차크랙'),
                     ('fce', '1차크랙종료'), ('drop', '배출')):
        a_v, f_v = ev(ai_ev, k), ev(fin_ev, k if k != 'dry' else 'dryend') or ev(fin_ev, k)
        if a_v is not None and f_v is not None and abs(f_v - a_v) > EVENT_TOL:
            out['issues'].append((f'event_{k}', f'{label} {f_v - a_v:+.0f}초 (AI {a_v:.0f} → 저장 {f_v:.0f})'))

    # 4) 총 시간 오차 — 열풍기를 드럼으로 오인하면 여기서 크게 벌어진다
    fin_t, raw_t = row.get('total_time'), ai.get('total_time_sec')
    if isinstance(fin_t, (int, float)) and isinstance(raw_t, (int, float)) and abs(fin_t - raw_t) > 30:
        out['issues'].append(('total_time', f'총시간 {fin_t - raw_t:+.0f}초 (AI {raw_t:.0f} → 저장 {fin_t:.0f})'))

    return out


def aggregate(rows: list[dict]) -> dict:
    by_machine = collections.defaultdict(lambda: {
        'n': 0, 'clean': 0, 'issues': collections.Counter(),
        'examples': collections.defaultdict(list), 'conf': collections.Counter(),
        'input': collections.Counter()})
    for row in rows:
        d = diff_row(row)
        if d is None:
            continue
        m = by_machine[d['machine']]
        m['n'] += 1
        m['conf'][d['confidence']] += 1
        m['input'][d['input_kind']] += 1
        if not d['issues']:
            m['clean'] += 1
        for kind, detail in d['issues']:
            m['issues'][kind] += 1
            if len(m['examples'][kind]) < 3:
                m['examples'][kind].append(detail)
    return by_machine


def match_machine_file(name: str) -> pathlib.Path | None:
    """AI가 보고한 기기명을 machines/*.md 파일에 느슨하게 매칭한다."""
    if not name:
        return None
    key = re.sub(r'[^a-z0-9가-힣]', '', name.lower())
    for p in MACHINES.glob('*.md'):
        if p.name.startswith('_'):
            continue
        stem = re.sub(r'[^a-z0-9가-힣]', '', p.stem.lower())
        title = re.sub(r'[^a-z0-9가-힣]', '',
                       (re.search(r'^#\s+(.+)$', p.read_text(encoding='utf-8'), re.M) or
                        re.match('', '')).group(1).lower() if re.search(
                           r'^#\s+(.+)$', p.read_text(encoding='utf-8'), re.M) else '')
        if key and (key in stem or stem in key or (title and (key in title or title in key))):
            return p
    return None


ISSUE_RULE = {
    'machine_mismatch': 'Users frequently corrected the detected machine here — do NOT infer the '
                        'machine from curve shape alone; state low confidence when the chart app '
                        'is ambiguous.',
    'total_time': 'Total roast time was frequently corrected — re-check the time axis labels '
                  'before assuming a drum-roaster length.',
    'temp_charge_temp': 'Charge temperature was frequently corrected — prefer the printed text '
                        'label at t=0 over pixel tracing.',
    'temp_drop_temp': 'Drop temperature was frequently corrected — anchor to the rightmost '
                      'printed label, not the curve end pixel.',
    'event_tp': 'Turning point was frequently corrected — on machines without thermal lag the TP '
                'may be absent; report null instead of guessing.',
    'event_dry': 'Dry-end was frequently corrected — read the app marker if present rather than '
                 'estimating from curve slope.',
    'event_fcs': 'First crack timing was frequently corrected — prefer an app-marked FC over '
                 'inference from the ROR dip.',
    'event_fce': 'First-crack-end was frequently corrected — do not assume a fixed offset from FC start.',
    'event_drop': 'Drop time was frequently corrected — read the printed drop label.',
}


def update_machine_docs(agg: dict, dry: bool) -> list[str]:
    touched = []
    for machine, stat in agg.items():
        if stat['n'] < MIN_SAMPLES:
            continue
        path = match_machine_file(machine)
        if not path:
            continue
        top = [(k, c) for k, c in stat['issues'].most_common() if c >= MIN_SAMPLES]
        lines = [SECTION, '',
                 f'<!-- scripts/roast_feedback.py 자동 생성 · {datetime.date.today().isoformat()} -->',
                 f'실사용 업로드 **{stat["n"]}건** 중 수정 없이 통과 **{stat["clean"]}건** '
                 f'({stat["clean"] * 100 // max(stat["n"], 1)}%).', '']
        if top:
            lines += ['| 오차 유형 | 건수 | 예시 |', '|---|---|---|']
            for k, c in top:
                exs = '<br>'.join(stat['examples'][k][:2]) or '—'
                lines.append(f'| {k} | {c} | {exs} |')
            lines += ['', '위 패턴에서 도출한 판독 지침(프롬프트에 함께 주입됨):', '']
            lines += [f'- {ISSUE_RULE[k]}' for k, _ in top if k in ISSUE_RULE]
        else:
            lines.append('반복 오차 패턴 없음 — 현재 판독 규칙이 잘 맞고 있다.')
        lines.append('')
        block = '\n'.join(lines)

        src = path.read_text(encoding='utf-8')
        if SECTION in src:
            new = re.sub(re.escape(SECTION) + r'.*?(?=\n## |\Z)', block, src, flags=re.S)
        else:
            new = src.rstrip() + '\n\n' + block
        if new != src and not dry:
            path.write_text(new, encoding='utf-8')
        touched.append(f'{path.name} (n={stat["n"]}, 오차유형 {len(top)})')
    return touched


def write_report(agg: dict, rows: list[dict], touched: list[str]) -> pathlib.Path:
    today = datetime.date.today().isoformat()
    total = sum(s['n'] for s in agg.values())
    clean = sum(s['clean'] for s in agg.values())
    L = [
        '# 로스팅 AI 실사용 피드백 학습',
        '',
        f'**작성일**: {today} · **담당**: scripts/roast_feedback.py (자동·토큰 0) · '
        '**신뢰도**: 상 (실사용 DB 직접 집계)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. 분석 대상 업로드 **{total}건** · 사용자 수정 없이 통과 **{clean}건** '
        f'({clean * 100 // max(total, 1)}%)',
        f'2. 기기 문서 **{len(touched)}개** 에 관측 오차를 반영 '
        f'{"(반영됨)" if touched else "(표본 부족으로 반영 없음)"}',
        f'3. 표본 {MIN_SAMPLES}건 미만인 기기는 우연을 규칙으로 굳히지 않기 위해 건너뜁니다.',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
        ('- [ ] 없음 — 자동 반영됨' if touched else
         '- [ ] 데이터가 더 쌓여야 합니다. 로스팅 프로파일 업로드가 늘면 자동으로 학습됩니다.'),
        '',
        '## 기기별 판독 정확도',
        '',
        '| 기기 | 업로드 | 무수정 통과 | 정확도 | 주요 오차 |',
        '|---|---|---|---|---|',
    ]
    for m, s in sorted(agg.items(), key=lambda kv: -kv[1]['n']):
        top = ', '.join(f'{k}×{c}' for k, c in s['issues'].most_common(3)) or '—'
        L.append(f'| {m} | {s["n"]} | {s["clean"]} | {s["clean"] * 100 // max(s["n"], 1)}% | {top} |')

    if touched:
        L += ['', '## 갱신된 기기 문서', ''] + [f'- {t}' for t in touched]

    L += ['', '## 학습 루프에서 이 단계의 위치', '',
          '1. 로스터가 사이트에 차트를 업로드 → AI가 판독',
          '2. 사용자가 마법사에서 값 수정 → **AI 원본과 최종값이 함께 저장** (ai_raw 컬럼)',
          '3. **이 스크립트**가 그 차이를 집계해 기기별 오차 패턴을 도출 ← 지금 단계',
          '4. `build_roast_knowledge.py` 가 패턴을 판독 규칙으로 프롬프트에 주입',
          '5. `deploy-functions.yml` 이 실서비스에 자동 배포',
          '',
          '즉 **로스터가 쓰면 쓸수록 AI가 정확해진다.**',
          '',
          '## 개인정보', '',
          'user_id·생두명·메모 등은 조회하지 않는다. 판독 정확도 집계에 필요한 컬럼만 읽는다.',
          '',
          '## 출처', '', '- Supabase `public.roasting_profiles` — 1차 (실사용 데이터 직접 집계)', '']

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORT_DIR / f'{today}-실사용피드백.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--limit', type=int, default=1000)
    a = ap.parse_args()

    rows = fetch_rows(a.limit)
    if not rows:
        print('분석할 데이터가 없습니다 (자격증명 미설정이거나 업로드가 아직 없음). 정상 종료.')
        return

    agg = aggregate(rows)
    print(f'업로드 {sum(s["n"] for s in agg.values())}건 · 기기 {len(agg)}종')
    for m, s in sorted(agg.items(), key=lambda kv: -kv[1]['n']):
        print(f'  {m:<28} n={s["n"]:<4} 무수정={s["clean"]:<4} '
              f'주요오차={", ".join(f"{k}×{c}" for k, c in s["issues"].most_common(2)) or "—"}')

    touched = update_machine_docs(agg, a.dry_run)
    out = write_report(agg, rows, touched)
    print(f'\n✓ {out.relative_to(ROOT)} 생성')
    if touched:
        print(f'✓ 기기 문서 {len(touched)}개 갱신 — build_roast_knowledge.py 를 이어서 실행하세요')
    if a.dry_run:
        print('(dry-run: 파일은 수정하지 않았습니다)')


if __name__ == '__main__':
    main()
