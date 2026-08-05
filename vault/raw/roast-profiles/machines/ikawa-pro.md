# IKAWA Pro (50g / 100g)

- heat_source: 열풍(대류) — fluid-bed
- temp_probe: 배기온도만 (원두 프로브 없음)
- typical_total_time: 3–10분
- chart_app: IKAWA Pro app
- verified: yes

## 판독 규칙

- FLUID-BED air roaster — there is NO bean-temperature probe. Never invent a BT probe reading.
- Temperature curves are setpoint (target) vs actual AIR temperature. If both inlet and exhaust
  are shown, treat EXHAUST as BT and INLET as ET. If only one line, output it as BT.
- Fan speed curve (%) has its own axis, usually 60–95%. Report step changes in "agitation"
  as percent ÷ 10 (e.g. 80% → 8).
- Roasts are SHORT (3–10 min). Do NOT stretch the time axis to drum-roaster lengths —
  this is the single most common error when the machine is misidentified.
- First crack may be marked by the app (ADFC) — read it if shown.
- Note "IKAWA fluid-bed" in the notes field so the client applies air-roast rules.
- CSV export exists: 구형 헤더는 'exaust temp'(원문 오타), 신형은 'temp above'.
  roasting.js 의 IKAWA CSV 파서가 이 두 형태를 모두 인식한다.

## 근거

- `supabase/functions/analyze-roast/index.ts` 기존 프롬프트 (운영 중 검증된 규칙)
- `roasting.js:489,567,642` — IKAWA CSV 전용 파서 (실제 파일로 검증됨)
