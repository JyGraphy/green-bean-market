# Stronghold (Roastware / Boost)

- heat_source: 하이브리드 — 열풍 + 할로겐(복사) + 드럼히터(전도)
- temp_probe: BT+ET (원두 표면 / 내부)
- typical_total_time: 10–16분
- chart_app: Roastware / Boost web app (dark UI, Korean labels)
- verified: yes

## 판독 규칙

- TOP CHART legend reads "■ 원두 표면  ■ 내부":
  BT = 원두 표면 (bean surface), ET = 내부 (internal drum). Match legend swatch colors.
  Sanity check only: BT usually finishes HIGHER than ET at drop.
- BOTTOM CHART (labeled 열원값) has up to four control STEP curves:
  열풍 (hot air) / 할로겐 (halogen) / 드럼 히터 (drum heater) / 교반 (agitation, 0–10).
- ⚠️ 할로겐(purple) and 교반(green) are the most commonly CONFUSED pair.
  Trace ONLY the step line whose color matches the 교반 swatch pixel-for-pixel.
  BEHAVIOR CUE: 할로겐 usually DECREASES and may step DOWN to 0 near the end;
  교반 commonly HOLDS a mid value then STEPS UP in the last 1–2 minutes (7→8→9→10).
  If the traced "교반" is flat throughout or drops to 0, you likely traced 할로겐.
- Read the ENTIRE 교반 line to DROP — late step-ups are frequently missed.
- Because this machine mixes three heat sources, ROR behaviour differs from pure drum
  roasters: halogen changes cause faster BT response than a drum-only roaster would show.

## 근거

- `supabase/functions/analyze-roast/index.ts` 기존 프롬프트 (운영 중 검증된 규칙)
- 사이트 로스팅 프로파일 기능에서 실제 Boost 차트로 반복 검증됨
