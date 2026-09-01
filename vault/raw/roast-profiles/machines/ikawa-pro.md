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
- MANUFACTURER COLOUR MAPPING (IKAWA's own Profile Library page, fetched 2026-09-01 — see
  sources/ikawa-pro-www-ikawacoffee-com-pro-sample-roaster-profiles.md): on IKAWA profile
  charts the RED line is the EXHAUST profile and the YELLOW line is the INLET profile.
  Use this only as a FALLBACK when the on-image legend is missing or unreadable — PHASE 0
  (read the legend) still wins if a legend is present, because users may re-colour exports.
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

- supabase/functions/analyze-roast/index.ts 기존 프롬프트 (운영 중 검증된 규칙)
- roasting.js:489,567,642 — IKAWA CSV 전용 파서 (실제 파일로 검증됨)
