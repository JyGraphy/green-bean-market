#!/usr/bin/env python3
"""로스팅 AI 학습 파이프라인 — 기기별 지식을 실제 AI 프롬프트에 주입한다.

**이게 왜 '학습'인가**
`supabase/functions/analyze-roast/index.ts` 의 로스팅 프로파일 AI는 파인튜닝 모델이 아니라
**Claude 비전 모델 + 판독 규칙 프롬프트** 구조다. 즉 이 AI의 '지식'은 곧 그 프롬프트다.
따라서 프로파일 데이터를 모으는 것만으로는 AI가 똑똑해지지 않는다.
**모은 지식을 이 프롬프트에 반영해야** 비로소 학습이 된다. 이 스크립트가 그 반영을 담당한다.

**왜 기기별로 나누는가** (사장님 지시, 2026-08-03)
로스터기마다 열원 방식(드럼 전도/열풍 대류/할로겐 복사)이 다르고 그래프도 제각각이다.
사용자가 로스터기를 입력하면 **그 기기에 맞는 그래프와 결과값**이 나와야 오차가 줄고,
로스터가 나중에 피드백할 때 정확해진다.

입력: vault/raw/roast-profiles/machines/*.md   (기기 1대 = 파일 1개)
출력: analyze-roast/index.ts 의 <<<MACHINE_KNOWLEDGE_START/END>>> 구간

사용법:
    python3 scripts/build_roast_knowledge.py            # 주입
    python3 scripts/build_roast_knowledge.py --check    # 변경 필요 여부만 (필요하면 exit 1)
    python3 scripts/build_roast_knowledge.py --report   # 학습 현황 보고서 생성
"""
from __future__ import annotations

import argparse
import datetime
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MACHINES = ROOT / 'vault' / 'raw' / 'roast-profiles' / 'machines'
TARGET = ROOT / 'supabase' / 'functions' / 'analyze-roast' / 'index.ts'
REPORT = ROOT / 'vault' / 'raw' / 'roast-profiles'

START = '// <<<MACHINE_KNOWLEDGE_START>>>'
END = '// <<<MACHINE_KNOWLEDGE_END>>>'

# 기기 문서에서 뽑아 쓰는 필드 (없으면 '미확인')
FIELDS = ['heat_source', 'temp_probe', 'typical_total_time', 'chart_app',
          'bt_curve', 'et_curve', 'control_curves', 'quirks', 'verified']


def parse_machine(path: pathlib.Path) -> dict:
    """마크다운 상단의 `- key: value` 블록과 본문 규칙을 읽는다."""
    text = path.read_text(encoding='utf-8')
    d = {'name': path.stem, 'raw': text}
    m = re.search(r'^#\s+(.+)$', text, re.M)
    d['title'] = m.group(1).strip() if m else path.stem
    for f in FIELDS:
        mm = re.search(rf'^-\s*{f}\s*:\s*(.+)$', text, re.M | re.I)
        d[f] = mm.group(1).strip() if mm else '미확인'
    # "## 판독 규칙" 섹션 = 프롬프트에 들어갈 본문
    rules = re.search(r'^##\s*판독 규칙\s*$(.*?)(?=^##\s|\Z)', text, re.M | re.S)
    d['rules'] = rules.group(1).strip() if rules else ''
    return d


def load_all() -> list[dict]:
    if not MACHINES.exists():
        return []
    return [parse_machine(p) for p in sorted(MACHINES.glob('*.md')) if not p.name.startswith('_')]


def build_block(machines: list[dict]) -> str:
    if not machines:
        return (f'{START}\n'
                '// (등록된 기기 지식 없음 — vault/raw/roast-profiles/machines/ 에 추가하세요)\n'
                f'{END}')

    lines = [
        START,
        '// 자동 생성 — 직접 수정 금지. 원본: vault/raw/roast-profiles/machines/*.md',
        # 생성일을 넣지 않는다. 넣으면 규칙이 하나도 안 바뀐 날에도 이 줄 때문에 파일이
        # 달라져서, 매주 리서치 실행마다 의미 없는 커밋과 재배포가 일어난다.
        # "언제 만들었나"는 git 이력이 더 정확하게 답한다.
        f'// 등록 기기 {len(machines)}대',
        '',
        '════════════════════════════════════════',
        'PHASE 1-B — MACHINE-SPECIFIC READING RULES (verified knowledge base)',
        '════════════════════════════════════════',
        'The user may specify which roaster produced the chart. Heat-transfer method differs',
        'per machine (drum conduction / fluid-bed convection / halogen radiation), so the curve',
        'shapes, typical temperature ranges and total roast times differ too. Use the matching',
        'entry below to calibrate your reading; if the machine is unknown, infer it from the',
        'chart app and total roast time, then apply that entry.',
        '',
        '| Machine | Heat source | Temp probe | Typical total | Chart app |',
        '|---|---|---|---|---|',
    ]
    for m in machines:
        lines.append(f'| {m["title"]} | {m["heat_source"]} | {m["temp_probe"]} | '
                     f'{m["typical_total_time"]} | {m["chart_app"]} |')

    for m in machines:
        if not m['rules']:
            continue
        lines += ['', f'▶ {m["title"]}']
        for ln in m['rules'].splitlines():
            lines.append(f'  {ln}' if ln.strip() else '')

    lines += [
        '',
        'CRITICAL: report the detected machine in the output "notes" field, e.g.',
        '"machine: IKAWA Pro (fluid-bed)". If the observed values contradict the machine\'s',
        'typical range above by a wide margin, lower "confidence" and say so in notes rather',
        'than forcing the numbers to fit.',
        '',
        END,
    ]
    return '\n'.join(lines)


def inject(block: str) -> bool:
    src = TARGET.read_text(encoding='utf-8')
    if START not in src or END not in src:
        print(f'✗ {TARGET.relative_to(ROOT)} 에 주입 마커가 없습니다.', file=sys.stderr)
        sys.exit(2)
    new = re.sub(re.escape(START) + r'.*?' + re.escape(END), block, src, flags=re.S)
    if new == src:
        return False
    TARGET.write_text(new, encoding='utf-8')
    return True


def write_report(machines: list[dict], changed: bool):
    today = datetime.date.today().isoformat()
    verified = [m for m in machines if m['verified'].lower().startswith(('y', '검증', 'true'))]
    L = [
        '# 로스팅 AI 학습 현황',
        '',
        f'**작성일**: {today} · **담당**: scripts/build_roast_knowledge.py (자동·토큰 0) · '
        '**신뢰도**: 상 (소스 직접 검사)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. 등록 기기 **{len(machines)}대** · 실측 검증 완료 **{len(verified)}대**',
        f'2. 이번 실행에서 AI 프롬프트 {"**갱신됨**" if changed else "변경 없음"} '
        f'(`supabase/functions/analyze-roast/index.ts`)',
        '3. 프롬프트 반영 후에는 **Supabase 배포가 있어야 실제 서비스에 적용**됩니다.',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
        ('- [ ] 배포 확인 — main 푸시 시 `deploy-functions.yml` 이 자동 배포합니다. '
         '저장소 시크릿 `SUPABASE_ACCESS_TOKEN` 이 없으면 건너뛰므로 등록 여부를 확인하세요.'
         if changed else '- 없음'),
        '',
        '## 등록된 기기 지식',
        '',
        '| 기기 | 열원 | 온도 프로브 | 총 로스팅 시간 | 차트 앱 | 판독규칙 | 검증 |',
        '|---|---|---|---|---|---|---|',
    ]
    for m in machines:
        L.append(f'| {m["title"]} | {m["heat_source"]} | {m["temp_probe"]} | '
                 f'{m["typical_total_time"]} | {m["chart_app"]} | '
                 f'{"✅" if m["rules"] else "❌ 없음"} | {m["verified"]} |')

    L += ['', '## 학습 루프 (이 순서로 돈다)', '',
          '1. `roast-profile-collector`가 신뢰 가능한 출처에서 기기별 프로파일·판독 특성을 수집',
          '2. `vault/raw/roast-profiles/machines/<기기>.md` 에 기록 (열원·프로브·시간·판독규칙)',
          '3. `python3 scripts/build_roast_knowledge.py` 로 AI 프롬프트에 주입 ← **여기가 학습**',
          '4. 실제 차트 이미지로 판독 테스트 → 오차 확인 → 규칙 보정 → 2번으로',
          '5. `supabase functions deploy analyze-roast` 로 서비스 반영',
          '',
          '## 왜 기기별로 나누는가', '',
          '로스터기마다 열원 방식(드럼 전도 / 열풍 대류 / 할로겐 복사)이 달라 온도 곡선의 모양,',
          '터닝포인트 위치, 총 로스팅 시간, ROR 거동이 전부 다르다. 기기를 특정하지 않으면',
          'AI가 드럼 기준으로 열풍 로스터를 읽어 시간축을 늘려 잡는 식의 오차가 난다.',
          '사용자가 로스터기를 입력하면 **그 기기에 맞는 그래프와 결과값**을 내놓아야',
          '오차가 줄고 로스터의 사후 피드백도 정확해진다.',
          '',
          '## 출처', '', '- `vault/raw/roast-profiles/machines/*.md` — 1차 (수집된 기기 지식)',
          '- `supabase/functions/analyze-roast/index.ts` — 1차 (주입 대상 프롬프트)', '']

    REPORT.mkdir(parents=True, exist_ok=True)
    out = REPORT / f'{today}-AI학습현황.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', action='store_true')
    a = ap.parse_args()

    machines = load_all()
    block = build_block(machines)

    if a.check:
        src = TARGET.read_text(encoding='utf-8')
        cur = re.search(re.escape(START) + r'.*?' + re.escape(END), src, re.S)
        same = cur and cur.group(0) == block
        print(f'등록 기기 {len(machines)}대 · 프롬프트 {"최신" if same else "갱신 필요"}')
        sys.exit(0 if same else 1)

    changed = inject(block)
    print(f'✓ 기기 {len(machines)}대 지식을 AI 프롬프트에 '
          f'{"주입했습니다 (변경 있음)" if changed else "확인했습니다 (변경 없음)"}')
    for m in machines:
        print(f'   · {m["title"]:<28} 열원={m["heat_source"]:<12} '
              f'규칙={"있음" if m["rules"] else "없음"} 검증={m["verified"]}')

    if a.report:
        out = write_report(machines, changed)
        print(f'✓ {out.relative_to(ROOT)} 생성')
    if changed:
        print('\n⚠️ 실제 서비스 반영에는 배포가 필요합니다.')
        print('   · 자동: 이 변경을 main에 푸시하면 deploy-functions.yml 이 배포합니다')
        print('     (저장소 시크릿 SUPABASE_ACCESS_TOKEN 필요)')
        print('   · 수동: supabase functions deploy analyze-roast '
              '--project-ref txnpbzukavajwbmggpfk')


if __name__ == '__main__':
    main()
