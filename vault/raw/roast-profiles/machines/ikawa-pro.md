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
- COLOUR MAPPING (IKAWA app profile graph — confirmed by the owner using the real app,
  2026-10-10): the RED line is EXHAUST (→ BT) and the ORANGE line is INLET (→ ET).
  IKAWA's Profile Library page describes the inlet line as "yellow"; on screen it renders
  ORANGE / yellow-orange — treat orange and yellow-orange as the same INLET line.
  The two hues are close, so also use the physics: INLET is the HOTTER line (it measures air
  entering the chamber, before it passes the beans) and sits ABOVE EXHAUST for most of the
  roast. If your "BT" line is above your "ET" line through mid-roast, you have swapped them.
  If an on-image legend is present and says otherwise, the legend wins.
- BATCH-SIZE CAVEAT (same source, manufacturer statement): exhaust profiles are described as
  compatible across all IKAWA Pro roasters, but INLET profiles "do not translate across
  different batch sizes". So an inlet-temperature value read from a Pro50 chart is NOT
  comparable to one from a Pro100/Pro100x. If the user states a batch size or model, do not
  carry inlet-based expectations over from a different size; say so in notes instead.
- Fan speed curve (%) has its own axis, usually 60–95%. Report step changes in "agitation"
  as percent ÷ 10 (e.g. 80% → 8).
- Roasts are SHORT (3–10 min). Do NOT stretch the time axis to drum-roaster lengths —
  this is the single most common error when the machine is misidentified.
- First crack may be marked by the app (ADFC) — read it if shown.
- Note "IKAWA fluid-bed" in the notes field so the client applies air-roast rules.
- CSV export exists: 구형 헤더는 'exaust temp'(원문 오타), 신형은 'temp above'.
  roasting.js 의 IKAWA CSV 파서가 이 두 형태를 모두 인식한다.

## 근거

- 2026-10-10 사장님(실기 사용자) 확인: IKAWA 프로파일 그래프에서 빨강=배기, 주황=인렛.

- supabase/functions/analyze-roast/index.ts 기존 프롬프트 (운영 중 검증된 규칙)
- roasting.js:489,567,642 — IKAWA CSV 전용 파서 (실제 파일로 검증됨)
