# EASYSTER 800G (이지스터 800, 한국 로스터기 제조사)

<!-- 신규 등록 (2026-08-31). 사장님이 실물로 차트를 만들어 주실 수 있는 3대 중 하나.
     아직 실측 차트가 없어 verified: no 로 둔다. -->

- heat_source: 드럼(전도)+열풍(대류) 하이브리드(반열풍) — "소켓식 일체형 버너"(가스 추정, 전기식 여부 미확인)
- temp_probe: BT + ET (Artisan 공식 연동 문서로 확인 — 이지스터 계열은 원두온도·환경온도를 로깅). 일부 기종은 배기온도를 3번째 채널로 제공. 800G가 어느 계열(Autonics TK4 PID / Smart)인지는 미확인
- typical_total_time: 미확인 — 시간당 최대 처리량 3kg라는 수치만 확인, 분당 로스팅 시간은 역산하지 말 것
- chart_app: Artisan 공식 지원 — Autonics TK4 PID 탑재기는 MODBUS RTU(USB, 시리얼 드라이버 필요), Smart 시리즈(터치 디스플레이)는 MODBUS TCP(WiFi). 800G 개별 확인은 아님
- verified: no

## 판독 규칙

- CONFIRMED CHANNELS (Artisan official integration docs, 2026-09-01): Easyster machines log
  BEAN TEMPERATURE (BT) and ENVIRONMENTAL TEMPERATURE (ET). SOME models additionally expose
  EXHAUST TEMPERATURE as a THIRD temperature channel. So a 3-temperature Easyster chart is
  normal and expected — do NOT assume the third line is a mislabeled duplicate of ET.
- The "Smart" series (touch display) additionally logs DRUM PRESSURE (Pa), DRUM and FAN SPEED
  (RPM), and BURNER LEVEL (%). If those non-temperature channels are present, the machine is a
  Smart-series unit; read them on their own axes and never confuse burner % with a temperature.
- ⚠️ WHICH SERIES the 800G belongs to is NOT confirmed. Do not assert TK4-PID vs Smart from the
  model number alone — infer it from which channels actually appear in the uploaded chart.
- OPTIONAL HARDWARE (manufacturer product page): exhaust-fan/air-pressure control, a digital
  micro-pressure gauge, and drum-speed control are PURCHASE OPTIONS on the 800G, not standard.
  Therefore the presence or absence of drum-pressure / drum-speed / fan-speed curves varies
  between two 800G units. A missing channel is a configuration difference, NOT a reading error.

- This is a Korean semi-hot-air (반열풍) HYBRID drum roaster: heat comes from a burner-fed duct
  combining drum conduction with hot-air convection, NOT a pure direct-fire drum and NOT a
  fluid-bed design. Treat its general curve shape like other Korean/gas drum roasters
  (Fuji Royal, Taehwan Proaster, Giesen) rather than applying IKAWA's fluid-bed rules.
- The manufacturer describes the burner as a "socket-type integrated burner" comparable to
  German 1kg-class roasters. This wording strongly implies a GAS burner, but the exact fuel
  (LPG vs LNG) and any electric-heat variant are NOT confirmed — do not state a specific fuel
  type or kcal/hr rating to the user.
- Rated batch range for the 800G unit is 200g–800g, with a manufacturer-stated throughput of
  "up to 3kg/hour." Do NOT use the 3kg/hour figure to infer an exact per-batch roast time in
  minutes — that conversion has not been confirmed and depends on unknown cooling/reload time.
- Temperature-probe configuration is UNCONFIRMED for the 800G model specifically. Two different
  pieces of general "Easyster" information exist and may not both apply to this model:
  (a) some smaller/older Easyster units (e.g. a user's "이지스터 300") are reported needing an
  AFTERMARKET K-type thermocouple to log via Artisan — i.e. no built-in digital probe;
  (b) the open-source Artisan machine directory separately describes an "Easyster" line as
  compatible via two Autonics TK4 PID controllers (one set as BT, one as ET) over MODBUS RTU,
  plus a newer "Easyster Smart" touchscreen series over MODBUS TCP/WiFi.
  Do NOT assume either (a) or (b) applies to the 800G without confirming from the actual chart
  or from the user. If a chart image is provided, read the on-image legend/axis labels rather
  than guessing BT/ET channel identity from this note.
- Because this is a small-batch (≤800g) semi-hot-air drum roaster, do not default to
  Probat/Loring-scale batch or timing assumptions, and do not apply IKAWA's "3–10 min" rule
  just because the batch is small — that rule is specific to fluid-bed roasters only.
- If the chart looks like a standard Artisan interface (red BT / blue ET, ROR sub-axis), follow
  Artisan's own legend conventions — no confirmed proprietary Easyster charting UI/color scheme
  was found in available sources.
- When in doubt, prefer stating "미확인" / lowering confidence over inventing a specific number
  for this machine — no verified chart exists yet to check assumptions against.

## 근거

- [EASYSTER 800G - easyster.co.kr](https://easyster.co.kr/product/easyster-800g/32/)
- [800g 상품설명 - easyster.co.kr](https://easyster.co.kr/layout/800g.html)
- [Easyster - Coffee roasting software - artisan-scope.org](https://artisan-scope.org/machines/easyster/)
  (검색 요약 기반 — 세션 WebFetch 차단(EGRESS_BLOCKED), 원문은 대기열 등록)
- [이지스터 800g 공식 매뉴얼 PDF - easyster.linkfile.co.kr](https://easyster.linkfile.co.kr/manual/800g.pdf)
  (제조사 공식 문서로 검색에서 확인, 세션에서 열람 못함 — 대기열 등록)
- 검증 대기 — 실제 이지스터 800G 차트/사진으로 아직 테스트하지 못함. **사장님이 실물 차트를
  주실 수 있는 기기 — 최우선 검증 후보.**
- 참고: 열원 연료 종류, 정확한 분단위 로스팅 시간대, BT/ET 프로브 기본 탑재 여부는 검색만으로
  확정하지 못해 "미확인"으로 남김. bwissue.com 등 커뮤니티 포럼 글도 검색됐으나 화면으로
  검증 불가능한 사용자 후기라 이 문서에 반영하지 않음(정책 우선순위 ④ 미충족).
