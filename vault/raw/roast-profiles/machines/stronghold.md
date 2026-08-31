# Stronghold S7X (850g 배치, Roastware / Boost)

<!-- 2026-08-31 갱신: 이 문서에 "S7X"라는 모델명이 한 번도 없어 어느 모델을 검증한 것인지
     불명확했다. 아래에서 모델을 특정하고, 기존 verified:yes 의 적용 범위를 S7X 세대로
     한정했다. 근거 없이 하위/상위 모델로 확장하지 말 것. -->

- heat_source: 하이브리드 — 열풍(대류)+할로겐(복사)+드럼히터(전도), 제조사 명칭 "Triple Heat System+"(S7X 세대: 열풍 2kW/할로겐 1.5kW/드럼히터 2kW급으로 보도됨)
- temp_probe: BT+ET (원두 표면/내부) + S7X 추가 "X-Lens" 비접촉 센서(측정 원리·응답특성 미확인, 아래 판독 규칙 참고)
- typical_total_time: 10–16분
- chart_app: Roastware / Boost web app (dark UI, Korean labels)
- verified: yes — 단, **S7X(850g) 세대 한정.** 근거는 아래 '모델 확정 근거' 참고.

## 모델 확정 근거 (S7X)

- Stronghold 공식/판매처 자료에 따르면 S7X는 **850g 배치**의 100% 전기 로스터로, 2026 US
  Coffee Roasters Championship 및 2025-26 Best of Panama / Best of Hawaii 공식 로스터기로
  쓰였다.
- S7X의 핵심 차별점은 **드럼 히터(Drum Heater)를 별도 제어 채널로 추가**한 것이다: 판매처
  설명에 따르면 하위 모델 "S7 Pro"는 할로겐+열풍에 의한 **간접** 드럼 가열만 있고 드럼 히터를
  독립 변수로 조절할 수 없는 반면, S7X는 드럼 히터를 신설해 전도열을 별도 파라미터로 제어한다.
- **이 문서의 기존 판독 규칙(열풍/할로겐/드럼히터/교반 4채널 STEP 커브)은 드럼히터가 독립
  채널로 존재하는 세대의 사양과 일치한다** — 즉 S7X(또는 이를 "S7 Pro X"로 병기한 국내 매체
  자료가 같은 세대를 가리킨다면 그것)에 해당하며, 드럼히터 채널이 없는 순정 S7 / S7 Pro
  (X 없음)에는 이 4채널 규칙을 그대로 적용하지 말 것.
- 다만 기존 "실제 Boost 차트로 반복 검증됨"이라는 근거 기록에는 **검증 당시 정확히 어떤
  모델 번호였는지 남아있지 않다.** 위 정황(드럼히터 채널 존재)으로 S7X 세대일 가능성이 높다고
  판단해 verified:yes 범위를 S7X로 좁혀 명시했을 뿐, 제조사 시리얼/구매 기록으로 재확인된
  것은 아니다. **사장님이 실물 S7X로 새 차트를 주시면 이 추정을 확정 검증으로 승격할 것.**

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
- S7X ALSO markets a bean-surface sensor called "X-Lens" ("pinpoint accuracy of actual bean
  surface measurement", "increased response time... unmatched by traditional probes"). NO
  confirmed technical detail (measurement principle, numeric offset vs. the classic BT probe,
  or whether it changes the post-charge dip shape) was found beyond this marketing description
  — do NOT invent an offset number or assume it removes the turning point, similar to the
  caution already applied to Aillio's IBTS in `aillio-bullet-r1.md`. If a curve is labeled
  "X-Lens" in the legend, read it as an additional/alternative BT-family line and flag any
  unusual behavior (e.g. no dip) as an open question rather than an error.
- This document covers the **850g S7X** specifically. If the user states a different model
  (plain "S7", "S7 Pro" without X, or the larger "S9X"), do NOT assume the same 4-channel
  heat-source layout or the same batch size — those are separate machines with their own
  (currently undocumented) control-curve sets.

## 근거

- `supabase/functions/analyze-roast/index.ts` 기존 프롬프트 (운영 중 검증된 규칙)
- 사이트 로스팅 프로파일 기능에서 실제 Boost 차트로 반복 검증됨 — 단, 검증 당시 모델 기록은
  남아있지 않음 (위 '모델 확정 근거' 참고)
- [Stronghold S7X | Coffee Machines Sale - cmsale.com](https://cmsale.com/products/roasting/coffee-roasters/stronghold/stronghold-s7x)
- [Roastronix S7X - Electrical Roaster, Stronghold Roaster & Smart Roaster](https://www.roastronix.com/s7x/)
- [Stronghold S7X – Coffai](https://coffai.ph/pages/stronghold-s7x)
- [Stronghold Launches Mid-Range S8X Roaster, Unveils Home-Friendly S2 - dailycoffeenews.com](https://dailycoffeenews.com/2025/05/28/stronghold-launches-mid-range-s8x-roaster-unveils-home-friendly-s2/)
  (S7X가 850g 배치 소형/샘플 로스터군에 속함을 교차 확인)
- [스트롱홀드 s7 s7x s7pro 차이점 - bwissue.com](https://bwissue.com/BLIND/2190332) (검색 요약만
  확인, 세션 WebFetch 차단 — S7/S7Pro/S7X 세 등급이 별도 모델임을 뒷받침하는 정황 자료)
- 검증 대기 항목: X-Lens 센서의 정확한 측정 원리·오프셋, S7 Pro X 라는 국내 표기가 S7X와
  완전히 같은 세대인지 여부 — 스트롱홀드 공식 사이트(stronghold.coffee)는 세션 WebFetch가
  차단(EGRESS_BLOCKED)돼 원문을 직접 확인하지 못함
