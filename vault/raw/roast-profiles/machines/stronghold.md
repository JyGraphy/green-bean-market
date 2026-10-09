# Stronghold S7X Pro (배치 150g–850g, Roastware / Boost)

<!-- 2026-08-31 갱신: 이 문서에 "S7X"라는 모델명이 한 번도 없어 어느 모델을 검증한 것인지
     불명확했다. 아래에서 모델을 특정하고, 기존 verified:yes 의 적용 범위를 S7X 세대로
     한정했다. 근거 없이 하위/상위 모델로 확장하지 말 것. -->

- heat_source: 하이브리드 — 열풍(대류)+할로겐(복사)+드럼히터(전도), 제조사 명칭 "Triple Heat System+"(S7X 세대: 열풍 2kW/할로겐 1.5kW/드럼히터 2kW급으로 보도됨)
- temp_probe: BT+ET (원두 표면/내부) + S7X 추가 "X-Lens" 비접촉 센서(측정 원리·응답특성 미확인, 아래 판독 규칙 참고)
- typical_total_time: 6.7–10.0분 (중앙 7.9분, Boost 실측 11,874건 P5–P95)
- chart_app: Roastware 기기 화면(어두운 배경) / Boost 웹 상세 페이지(흰 배경, 패널 3단)
- verified: no — 아래 '모델명 충돌' 참고. 검증 기록에 모델 번호가 없어 어느 기종을 검증했는지 확정할 수 없다.

## ⚠️ 모델명 충돌 (2026-09-01, 미해결)

**사장님(실물 소유자) 진술: 정확한 모델명은 "S7X Pro" 다.**
그런데 우리가 2026-09-01 에 수집한 stronghold.coffee 공식 페이지의 제품 내비게이션에는
S2 / S7Pro / S7X / S8X / S9X 만 있고 **"S7X Pro" 표기는 없다.**

둘 중 하나다: (가) 공식 내비게이션이 축약 표기이고 정식 제품명이 S7X Pro 이거나,
(나) 우리가 "S7 Pro" 와 "S7X" 를 별개 모델로 나눈 구분 자체가 틀렸거나.

**소유자 진술을 우선한다** — 실물을 가진 사람의 표기가 우리가 긁은 메뉴 텍스트보다
강한 증거다. 문서 제목을 S7X Pro 로 바꾼다. 다만 제조사 1차 확인 전까지 이 충돌을
지우지 않는다.

이것이 무결성 검사가 없어서 생긴 사고다. 아래 '드럼히터로 모델을 나눈' 서술은
**판매처 2차 설명**이 근거였고, 제조사 1차 자료로 확인한 적이 없다.
`scripts/verify_machines.py` 를 이 사건 뒤에 만들었다.

## 모델 관계 서술 (근거: 판매처 2차 설명 — 제조사 미확인)

- Stronghold **공식 제품 페이지(2026-09-01 수집)** 기준 S7X 배치 용량은 **150g–850g**이다
  (기존 문서에 '850g'로만 적혀 있던 것을 정정 — 850g 은 최대치다). 100% 전기 로스터로, 2026 US
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
  것은 아니다. **사장님이 실물 S7X Pro 로 새 차트를 주시면 그때 확정 검증으로 승격한다.**
  그 전까지 verified: no 를 유지한다 — 모델을 특정하지 못한 검증은 검증이 아니다.

## 판독 규칙

- Boost web detail page (white background, "그래프" card + "로스팅 타임라인" panel):
  BT = 원두 표면 = TEAL, ET = 내부 온도 = DARK BROWN. RED = 열풍 (up to ~420°C) and
  OLIVE = 드럼 표면 are NOT BT/ET. Faded duplicate lines = 참조 프로파일 → ignore.
- Roastware machine screen (dark): BT = 원두 표면, ET = 내부 — match legend swatches.
- 원두 표면 (IR) starts LOW at charge (57–76°C) and rises with no dip. The turning point is
  read on 내부 온도 (50–70 s, 101–126°C). At drop, IR ≈ 내부 + 40°C (31–51).
- BOTTOM CHART 열원값 (0–10): 열풍 red · 할로겐 purple · 드럼 히터 pink · 교반 green.
  Read levels against the 0/5/10 gridlines. 교반 is constant for the whole roast in ~46% of
  roasts and rises in ~49% — never assume a pattern; record only steps you can see.
  할로겐 ends lower than it starts in 88% of roasts (about half end at 0).
- Because this machine mixes three heat sources, ROR behaviour differs from pure drum
  roasters: halogen changes cause faster BT response than a drum-only roaster would show.
- S7X ALSO markets a bean-surface sensor called "X-Lens". No confirmed technical detail
  (measurement principle, offset vs. a classic BT probe) — do NOT invent an offset. If a curve
  is labeled "X-Lens", read it as a BT-family line and flag unusual behavior as an open question.
- This document covers the **S7X (150g–850g batch)** specifically. For plain S7 / S7 Pro / S9X,
  do NOT assume the same 4-channel layout or batch size.

## 근거

- **2026-10-09 실측 검증**: Boost 계정(머신 3대, Boost API `modelName: "S7X"`)의 기록 11,874건과
  상세 곡선 342건으로 수치 범위를 산출했다. Boost 웹 상세 화면 9건을 캡처해 AI 판독 결과를
  원본 초 단위 데이터와 비교해 색상·형태 규칙을 확인했다(원두 표면=청록, 내부=진갈색,
  열풍=빨강, 드럼 표면=올리브, 교반=초록, 할로겐=보라, 드럼 히터=분홍).

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
