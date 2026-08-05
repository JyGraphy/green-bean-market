# 태환 Proaster (Taehwan Automation)

- heat_source: 드럼(전도) — 드럼 하부 열원(가스 또는 전기, 모델별 상이)
- temp_probe: 미확인 (모델별 상이, 표준 BT/ET 구성 확인 안 됨)
- typical_total_time: 5–20분 (모델별 편차 큼 — 예: THCR-01A 500g–1.5kg 배치, 5–20분)
- chart_app: 미확인 — 자체 데이터로깅/차트 소프트웨어 존재를 검색으로 확인하지 못함
- verified: no

## 판독 규칙

- Korean-market drum roaster with the heat source located below/under the drum (conduction),
  spanning a WIDE range of models from small (200g sample roasters) to large industrial
  (30kg+) capacity. Do NOT apply one fixed time/batch assumption — if the model or batch
  capacity is stated by the user, scale expectations accordingly: small sample models can roast
  in well under 10 min, larger industrial batches typically need longer.
- No confirmed proprietary charting app or default color legend was found for Proaster in
  available sources. If a Proaster chart is provided, do NOT assume Artisan-style default
  colors — read the on-image legend, and if no legend is visible, lower "confidence" to "low"
  rather than guessing which curve is BT/ET.
- Gas vs electric heater variants exist (e.g. THCR-01A: gas ~3900kcal or 3.3kW electric option).
  Heater type may plausibly affect burner-response speed for ROR, but no verified data on the
  magnitude of that difference was found — do not invent a specific ROR-lag figure for this.
- Treat this entry as PARTIAL/LOW-CONFIDENCE knowledge: the batch/time range above is sourced
  from ONE specific small model's public spec listing, not confirmed across the full Proaster
  lineup actually used in Korean roasteries. Prefer asking the user for the exact model over
  guessing machine-specific behavior beyond what is stated here.

## 근거

- [㈜태환자동화산업 - 커피로스터사업부](http://www.taehwan.co.kr/bbs/board.php?bo_table=coffee_roaster)
- [23-24 제12회 GCA 공식 로스터기 - ㈜태환자동화산업 <PROASTER THCR-01A> - 한국커피로스터연합](https://crak.or.kr/notice/?bmode=view&idx=16332283)
- [(주)태환자동화산업 - 코머신](https://www.komachine.com/ko/companies/taehwan-automation)
- 검증 대기 — 실제 Proaster 차트 이미지로 아직 테스트하지 못함
- 참고: temp_probe·chart_app은 검색으로 확정하지 못해 "미확인"으로 남김. 추측으로 채우지 않았음.
