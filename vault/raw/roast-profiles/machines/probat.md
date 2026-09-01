# Probat (Probatone / P Series)

- heat_source: 드럼(전도) — gas burner + drum/air thermocouples
- temp_probe: BT+ET (P series 표준, 구형 Probatone 2 base는 BT만)
- typical_total_time: 10–20분 (상업용 배치 5–60kg)
- chart_app: Artisan / Cropster (자체 차트 앱 없음, 외부 소프트웨어 연동)
- verified: no

## 판독 규칙

- This is the classic reference gas-fired DRUM roaster: burner heats the drum and the air that
  flows through it; thermocouples read product (BT) and exhaust (ET) temperature.
- Older base Probatone 2 units ship with a BT probe ONLY; the ET probe is an aftermarket addition
  fitted to the exhaust. If only ONE temperature curve is shown, treat it as BT — do not invent
  an ET line.
- Probat has NO proprietary chart skin — charts are almost always exported via Artisan or
  Cropster, so legend colors follow THAT app's convention, not a Probat-specific one. Always
  read the on-image legend (do not assume fixed colors for "Probat").
- Commercial batch scale is 5–60kg (Probatone 5/12, P12–P60); total roast time is typically
  10–20 min. Do not shrink the time axis toward small sample-roaster durations.
- Expect the classic BT S-curve: a dip/turning-point shortly after charge, then a steady rise
  through Maillard to drop. ET typically tracks below BT after the turning point but the exact
  offset varies by probe placement — confirm relative position with the anchor/consistency
  rules rather than assuming a fixed gap.
- Because heat transfer is drum conduction plus burner-heated air (not induction or fluid-bed),
  ROR responds more SLOWLY to burner (gas) changes than IKAWA (fluid-bed) or Aillio (induction) —
  do not expect fast, step-like ROR jumps right after a burner adjustment.
- OBSERVED PROFILE RANGES (n=2 documented events, single Probat P5 unit at UC Davis Coffee
  Center, academic source — see profiles/probat-ucdavis-*.json): a "Fast Start" style profile
  hit first crack at ~8 min with drop at 16 min; a "Slow Start" style profile hit first crack
  at ~12 min with the same 16 min drop. Reported start/drop temperatures were ~215±8°C and
  ~237±2°C respectively (BT vs ET not specified in the source). IMPORTANT CAVEAT: the 16-minute
  total time was an EXPERIMENTAL DESIGN CHOICE (researchers fixed all 7 tested profiles to the
  same duration for sampling purposes) — do NOT treat 16 min as this machine's natural/typical
  roast length, and do NOT lower confidence just because a real Probat P5 chart shows a
  shorter total time (e.g. 10–12 min, which is more typical for commercial production). Use
  this only as a loose sanity check that first-crack timing anywhere from ~8–12+ min into a
  drum roast on this class of machine is plausible.

## 근거

- [Probat | Leading coffee roasting software - Artisan](https://artisan-scope.org/machines/probat/)
- [artisan blog: Probat Probatone](https://artisan-roasterscope.blogspot.com/2017/06/probat-probatone.html)
- [artisan blog: Probatone: Adding ET](https://artisan-roasterscope.blogspot.com/2017/06/probatone-adding-et.html)
- [P Series | PROBAT SE](https://www.probat.com/en/products/shop-roaster/p-series/)
- [12 Kg - P12-3 Probat Coffee Roaster - coffeetec](https://coffeetec.com/products/12-kg-p12-3-probat-2022-model-excellent-condition-used)
- [12 kilo Probat P12-2 Probatone Roaster - coffeetec](https://coffeetec.com/products/12-kilo-probat-p12-2-probatone-roaster-amazing-condition-2019-model-used)
- [The effect of roast profiles on the dynamics of titratable acidity during coffee roasting — Anokye-Bempah et al. 2024, Scientific Reports (PMC11002029)](https://europepmc.org/article/PMC/PMC11002029)
  — Probat P5(5kg, 천연가스) 실측: FS/SS 프로파일의 시작·투입·1차크랙·배출 시각/온도.
  vault/raw/roast-profiles/profiles/probat-ucdavis-fs-uganda-washed.json,
  probat-ucdavis-ss-uganda-washed.json 참고.
- [A universal color curve for roasted arabica coffee — Anokye-Bempah et al. 2025, Scientific
  Reports (PMC12234775)](https://europepmc.org/article/PMC/PMC12234775) — 동일 실험실·동일 로스터를
  "P5 model 2, Probat GmbH, Emmerich am Rhein, Germany"로 모델 특정(교차 확인)
- 검증 대기 — 실제 Probat/Artisan 차트 이미지로 아직 테스트하지 못함
