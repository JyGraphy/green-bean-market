# 태환 Proaster (Taehwan Automation)

- heat_source: 드럼(전도) — 드럼 하부 열원(가스 또는 전기, 모델별 상이)
- temp_probe: 모델별 상이 — Artisan 연동은 THCR-01/01A/03/06/12/25 공식 지원 확인, 일부 모델 "3 TEMP" 가이드 존재(채널 구성은 미확인)
- typical_total_time: 5–20분 (모델별 편차 큼) — 확인 지점: THCR-01A 500g–1.5kg/5–20분, THCR-06 2–10kg/약10–15분
- chart_app: 모델별 Artisan 연동 지원(공식 설치 매뉴얼 확인) + 자체 로깅 프로그램 "DAQ MASTER"(상세 기능 미확인)
- verified: no

## 판독 규칙

- Korean-market drum roaster with the heat source located below/under the drum (conduction),
  spanning a WIDE range of models from small (200g–1.5kg sample models like THCR-01/01A) to
  mid-size (THCR-06: 2–10kg, ~10–15 min) to large industrial (THCR-12/THCR-25, 30kg+) capacity.
  Do NOT apply one fixed time/batch assumption — if the model or batch capacity is stated by the
  user, scale expectations accordingly: small sample models can roast in well under 10 min,
  larger industrial batches typically need longer even though total time does not scale linearly
  with batch size (THCR-01A and THCR-06 overlap in the 10–15 min range despite very different
  batch sizes).
- Proaster models are OFFICIALLY compatible with Artisan (confirmed via Taehwan's own install-
  manual download page, covering THCR-01/01A/03/06/12/25) as well as Taehwan's own logging
  software "DAQ MASTER." If a Proaster chart is provided, do NOT assume Artisan-style default
  colors purely because Artisan is supported — still read the on-image legend, and if no legend
  is visible, lower "confidence" to "low" rather than guessing which curve is BT/ET.
- Gas vs electric heater variants exist (e.g. THCR-01A: gas ~3900kcal/hr or 3.3kW electric
  option; THCR-06: gas ~18,000kcal/hr natural gas or ~1.5kg/hr LPG, single-phase 220–240V,
  ~2.0kW/hr power draw). Heater type may plausibly affect burner-response speed for ROR, but no
  verified data on the magnitude of that difference was found — do not invent a specific ROR-lag
  figure for this.
- Treat probe COUNT/PLACEMENT as still LOW-CONFIDENCE: a "3 TEMP Artisan connection guide" is
  confirmed to exist for at least one model, implying 3-channel temperature logging is possible,
  but which channels (BT/ET/drum-wall/preheat) are not confirmed from search alone — do not
  assume a specific 3-probe layout without the primary manual. Prefer asking the user for the
  exact model over guessing machine-specific behavior beyond what is stated here.

## 근거

- [㈜태환자동화산업 - 커피로스터사업부](http://www.taehwan.co.kr/bbs/board.php?bo_table=coffee_roaster)
- [23-24 제12회 GCA 공식 로스터기 - ㈜태환자동화산업 <PROASTER THCR-01A> - 한국커피로스터연합](https://crak.or.kr/notice/?bmode=view&idx=16332283)
- [(주)태환자동화산업 - 코머신](https://www.komachine.com/ko/companies/taehwan-automation)
- [프로스터 아티산(artisan) 설치 매뉴얼 업로드 - taehwan.co.kr (검색 요약 — THCR-01/01A/03/06/12/25
  Artisan 연동 확인, "3 TEMP" 가이드 존재 확인. 원문 PDF는 대기열 등록, 세션 WebFetch 403)](http://taehwan.co.kr/en/bbs/board.php?bo_table=down&wr_id=1)
- [THCR-06 사용 매뉴얼 - manualslib.com (검색 요약 기반, 원문은 대기열 등록)](https://www.manualslib.com/manual/2630997/Proaster-Thcr-06.html)
- 검증 대기 — 실제 Proaster 차트 이미지로 아직 테스트하지 못함
- 참고: 정확한 프로브 채널 구성(BT/ET 여부)은 원문 매뉴얼 확보 전까지 추정하지 않음.
