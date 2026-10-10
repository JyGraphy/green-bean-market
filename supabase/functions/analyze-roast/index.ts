import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const PROMPT = `You are a coffee roasting expert with deep knowledge of roasting software chart layouts.
Analyze the roasting profile chart image carefully and extract precise data.
The image may be a direct screenshot or a photo taken of a screen (possibly with slight glare or angle).

════════════════════════════════════════
PHASE 0 — READ THE LEGEND FIRST (MOST IMPORTANT STEP)
════════════════════════════════════════
DO NOT assume any curve's color from memory. Colors differ between apps, firmware
versions, themes, and even between the top and bottom chart of the SAME screen.
The ONLY reliable source of truth is the legend printed on the image.

For EVERY chart region (top temperature chart AND bottom control chart), locate the
legend — a row of small colored swatches (●/■/—) each followed by a text label.
Read each swatch's ACTUAL color (look at the pixels of the swatch itself) and bind
that exact color to its label. Build an explicit color→label map before tracing
anything. Example of what you must produce internally:
  "the swatch before 할로겐 is pink (#e84a8a); the swatch before 교반 is cyan (#3ba9d4)"
Then, to read a curve, find the line whose color MATCHES its legend swatch — never
guess from the label name alone.

════════════════════════════════════════
PHASE 1 — IDENTIFY THE APP & MAP CURVES VIA THE LEGEND
════════════════════════════════════════
Identify the app, then map each curve using the legend you read in PHASE 0.

▶ Stronghold — TWO different screens exist. Identify which one first:

  (A) BOOST WEB DETAIL PAGE — white background, blue "boost" logo top-left, a "그래프"
      card with three stacked panels, and a right-hand "로스팅 타임라인" text panel.
      ⚠️ The rules in this block OVERRIDE the generic color rules in PHASE 2/4/5.
      • TOP panel (온도 °C, scale printed on the RIGHT edge, 0–600, gridlines every 100)
        holds FOUR temperature curves. Colors (verified on 9 real Boost pages):
          원두 표면 (bean surface IR)   = TEAL / CYAN          ← BT
          내부 온도 (internal air)      = DARK BROWN / near-black ← ET
          열풍 (hot-air heater temp)   = RED / ORANGE-RED, climbs to ~300–420°C — NOT BT
          드럼 표면 (drum surface)      = OLIVE / YELLOW-GREEN, flat ~190–240°C — NOT ET
        The legend is NOT beside the chart; it is the colored bars in the top-right
        status card ("원두 표면 / 내부 온도 / 열풍 / 드럼 표면").
      • Faded, lighter duplicate of every line = 참조 프로파일 (reference profile overlay).
        IGNORE all faded lines. Trace only the fully saturated lines that stop at DROP.
      • SHAPE RULES: 원두 표면 starts LOW at 0:00 (≈55–75°C, cold beans) and rises
        monotonically with NO dip. 내부 온도 starts high (≈130–160°C), dips to a minimum at
        ≈50–70 s (≈100–126°C — this is the turning point), then rises. At DROP 원두 표면 is
        ≈31–51°C (median 40) ABOVE 내부 온도. If your "BT" exceeds ~240°C you traced 열풍.
      • ANCHORS: the 로스팅 타임라인 panel prints exact values, e.g.
        "터닝 포인트 01:05 / 내부: 99.2 °C / 원두 표면: 86 °C",
        "1차 크랙 07:48 / 내부: 165.4 °C / 원두 표면: 208.6 °C", "배출 08:56 / …".
        These are ground truth: put them in labeled_points (원두 표면 → BT, 내부 → ET)
        and make bt_curve / et_curve pass through them. Use the 0/100/200/300 gridlines
        to read values between anchors — do not eyeball without the grid.
      • MIDDLE panel = RoR in °C/30s (teal = 원두 표면 RoR, brown = 내부 RoR) — ignore.
      • BOTTOM panel 열원값 (scale 0–10 on the right, gridlines at 0, 5, 10), STEP lines:
          열풍 = RED/ORANGE · 할로겐 = PURPLE · 드럼 히터 = PINK/MAGENTA · 교반 = GREEN
        The panel is short (≈130 px for 0–10), so MEASURE, don't eyeball: find the pixel
        rows of the printed "10", "5" and "0" labels on the right edge, then for each line
        level = 5 + 5 × (y_of_5 − y_line) / (y_of_5 − y_of_10)   (round to 0.5).
        One unit ≈ 11 px, so a line ~3 units below the top gridline is 7, not 10.
        Several lines often sit near the top (열풍/할로겐 ≈ 8–10); 드럼 히터 is usually low
        and flat (≈3); the GREEN 교반 line is a separate line — measure it on its own.
        교반 is OFTEN CONSTANT for the whole roast (any level 4–10). Record only steps you
        can actually see.
        HIDDEN-LINE RULE: lines are drawn on top of each other, so the green 교반 line is
        often hidden — most often along the TOP border at 10 under 열풍/할로겐. Scan the
        whole width for short visible green segments (they appear where another line
        moves away); their level is the 교반 level. NEVER substitute another color's level
        (e.g. the low pink 드럼 히터 line) for 교반. If no green pixels are visible at all,
        return agitation [] and say so in notes. 할로겐 usually steps DOWN during the roast (≈half end at 0).

  (B) ROASTWARE MACHINE SCREEN — dark background, legend printed under the chart
      ("■ 원두 표면  ■ 내부", bottom "● 열풍 ● 할로겐 ● 드럼 히터 ● 교반").
      Use PHASE 0 legend swatches. Commonly 원두 표면 = pink/red, 내부 = white/gray.
      할로겐 vs 교반 are the pair most often confused: trace only the line whose color
      matches the 교반 swatch; do not assume any particular step pattern.

▶ IKAWA (Pro app / Home app; clean minimal UI, light or dark):
  FLUID-BED air roaster — there is NO bean-temperature probe. The graph shows:
    • Temperature curves: setpoint (target) vs actual AIR temperature
      (inlet and/or exhaust). If both shown, treat EXHAUST as BT and INLET as ET.
      If only one temperature line, output it as BT.
    • Colors on the IKAWA profile graph: RED = EXHAUST (→ BT), ORANGE / yellow-orange =
      INLET (→ ET). The hues are close: INLET is the hotter line and sits ABOVE exhaust for
      most of the roast — if your BT is above your ET mid-roast, you swapped them.
    • IKAWA app roast-log graph (dark screen): the header prints "예열 온도: X°C · 배출 온도:
      Y°C" and "배출 시간: M:SS" → charge_temp = X, drop_temp = Y, events.drop = M:SS.
      Dashed vertical markers carry text: "CC  2:22  161°C" (color change → events.dry) and
      "1⚡ 5:42  203°C" (first crack → events.fcs). These temperatures are EXHAUST values:
      put each one in labeled_points with curve "BT" (they anchor the curve exactly).
      Y axis 0–300°C with gridlines every 50°C; X axis in minutes (1, 2, 3 …).
      The lines CONTINUE after drop (cooling: both fall steeply) — stop the curves at drop.
      Shaded areas (dark red under the exhaust, light pink/gray fan area) are not curves.
    • IKAWA SHAPE (not a drum S-curve): exhaust dips right after charge (turning point
      ≈10 s), rises fast to ≈150°C within the first minute, then runs almost FLAT until the
      color change, then rises again to drop. Inlet spikes early (≈20 s) to its highest value,
      falls back to a plateau, then rises after the color change. Follow these plateaus —
      do not draw straight lines between anchors.
    • Fan speed curve (%): a separate line/axis, usually 60–95%.
      Report its step changes in "agitation" as percent÷10 (e.g. 80% → 8).
  Roasts are SHORT: total time 3–10 minutes — do not stretch the time axis to
  drum-roaster lengths. First crack may be marked by the app (ADFC) — read it if shown.
  Note "IKAWA fluid-bed" in the notes field so the client can apply air-roast rules.

▶ Artisan (light or dark background): read its legend too.
  Commonly BT = orange/red thick curve, ET = blue curve, but CONFIRM via legend.
  Events: vertical lines labeled CHARGE, DRY END, FC START, FC END, DROP/SCO

▶ Cropster / Firescope / RoasTime:
  BT = boldest colored curve; confirm names against the legend.
  Events marked by vertical dashed lines with text.

// <<<MACHINE_KNOWLEDGE_START>>>
// 자동 생성 — 직접 수정 금지. 원본: vault/raw/roast-profiles/machines/*.md
// 등록 기기 10대

════════════════════════════════════════
PHASE 1-B — MACHINE-SPECIFIC READING RULES (verified knowledge base)
════════════════════════════════════════
The user may specify which roaster produced the chart. Heat-transfer method differs
per machine (drum conduction / fluid-bed convection / halogen radiation), so the curve
shapes, typical temperature ranges and total roast times differ too. Use the matching
entry below to calibrate your reading; if the machine is unknown, infer it from the
chart app and total roast time, then apply that entry.

| Machine | Heat source | Temp probe | Typical total | Chart app |
|---|---|---|---|---|
| Aillio Bullet R1 (v2 / R2 Pro) | 하이브리드 — 드럼 + 유도가열(IH), 가스/화염 아님 | BT+ET + 선택형 IBTS(적외선 표면센서, 열지연 없음) | 8–12분 (배치 약 400g–1.2kg) | RoasTime (Aillio 자체 앱) |
| EASYSTER 800G (이지스터 800, 한국 로스터기 제조사) | 드럼(전도)+열풍(대류) 하이브리드(반열풍) — "소켓식 일체형 버너"(가스 추정, 전기식 여부 미확인) | BT + ET (Artisan 공식 연동 문서로 확인 — 이지스터 계열은 원두온도·환경온도를 로깅). 일부 기종은 배기온도를 3번째 채널로 제공. 800G가 어느 계열(Autonics TK4 PID / Smart)인지는 미확인 | 미확인 — 시간당 최대 처리량 3kg라는 수치만 확인, 분당 로스팅 시간은 역산하지 말 것 | Artisan 공식 지원 — Autonics TK4 PID 탑재기는 MODBUS RTU(USB, 시리얼 드라이버 필요), Smart 시리즈(터치 디스플레이)는 MODBUS TCP(WiFi). 800G 개별 확인은 아님 |
| 후지로얄 Fuji Royal (소형 드럼 — 구체 모델 미확인) | 드럼(전도) — 반직화식(semi-direct fire) 가스 드럼 | 내장 프로브 없음 (국내는 후장착 서모커플+Artisan 조합) | 10–15분 (드럼을 약 200℃로 예열 후 150℃ 부근으로 낮춰 투입) | Artisan (자체 차트 앱 없음 — 후장착 프로브+Artisan 조합이 일반적) |
| Giesen (W6 / W15 / W30 시리즈) | 드럼(전도) — 가스버너 + 간접 드럼 가열(indirect-drum) 재킷 | BT+ET 옵션 (PT100 이중 프로브) | 약 12–13분 (실측 예: 브라질 옐로우 부르봉, 최종 BT 200℃ 기준 4회 평균 12:50) | Artisan / Cropster / Giesen Profiler (자체 소프트웨어, 2.0부터 색상 커스터마이징 가능) |
| IKAWA Pro (50g / 100g) | 열풍(대류) — fluid-bed | 배기온도만 (원두 프로브 없음) | 3–10분 | IKAWA Pro app |
| Loring (S15 Falcon / S35 Kestrel / S70 Peregrine) | 열풍(대류) — single burner heats inlet air, not the drum (smokeless afterburner) | BT(빠른 ~1.5mm 프로브)+ET(배기) | 10–16분 (예: S15 배치 15kg). 대형기(S35/S70)도 배치만 커질 뿐 시간대는 유사 | Cropster (Roasting Intelligence) / Loring 자체 제어 소프트웨어 ("Roast Architect") |
| Probat (Probatone / P Series) | 드럼(전도) — gas burner + drum/air thermocouples | BT+ET (P series 표준, 구형 Probatone 2 base는 BT만) | 10–20분 (상업용 배치 5–60kg) | Artisan / Cropster (자체 차트 앱 없음, 외부 소프트웨어 연동) |
| ROEST 샘플 로스터 (노르웨이) — 확인된 모델: S100, S200, L200 | 하이브리드 — 열풍(대류)을 주 열원으로 쓰되 원두를 띄우지 않고(NOT fluid-bed) | BT+ET 추정 + inlet(유입 공기) 센서 + 자동 1차크랙 감지 센서 — 검색 요약 기준, | 6–7분 (n=1 학술 논문 기준, ROEST 공식 typical range 아님 — 아래 판독 규칙 참고) | ROEST 자체 앱(터치 컨트롤러+클라우드 프로파일 라이브러리로 알려짐, 세부 미확인) |
| Stronghold S7X Pro (배치 150g–850g, Roastware / Boost) | 하이브리드 — 열풍(대류)+할로겐(복사)+드럼히터(전도), 제조사 명칭 "Triple Heat System+"(S7X 세대: 열풍 2kW/할로겐 1.5kW/드럼히터 2kW급으로 보도됨) | BT+ET (원두 표면/내부) + S7X 추가 "X-Lens" 비접촉 센서(측정 원리·응답특성 미확인, 아래 판독 규칙 참고) | 6.7–10.0분 (중앙 7.9분, Boost 실측 11,874건 P5–P95) | Roastware 기기 화면(어두운 배경) / Boost 웹 상세 페이지(흰 배경, 패널 3단) |
| 태환 Proaster (Taehwan Automation) | 드럼(전도) — 드럼 하부 열원(가스 또는 전기, 모델별 상이) | 모델별 상이 — Artisan 연동은 THCR-01/01A/03/06/12/25 공식 지원 확인, 일부 모델 "3 TEMP" 가이드 존재(채널 구성은 미확인) | 5–20분 (모델별 편차 큼) — 확인 지점: THCR-01A 500g–1.5kg/5–20분, THCR-06 2–10kg/약10–15분 | 모델별 Artisan 연동 지원(공식 설치 매뉴얼 확인) + 자체 로깅 프로그램 "DAQ MASTER"(상세 기능 미확인) |

▶ Aillio Bullet R1 (v2 / R2 Pro)
  - Induction heating gives fast, precise power response — ROR reacts to power-level changes
    noticeably QUICKER than a gas-fired drum (Probat/Giesen/Fuji Royal), though still slower than
    IKAWA's fluid-bed.
  - If an IBTS (Infrared Bean Temperature Sensor) curve is present, it reads bean SURFACE
    temperature with NO thermometric lag: it typically shows NO dip/turning-point after charge.
    Do NOT force an IBTS curve to show a turning point just because a classic BT curve normally
    has one — its absence is expected and CORRECT for IBTS, not a reading error.
  - The IBTS-vs-contact-probe OFFSET IS NOT A FIXED NUMBER — do not hard-code "IBTS reads ~15–17°C
    higher." User reports (Roast World community) show the gap is LARGEST on small batches and
    SHRINKS as batch size increases; on larger batches (~1.2kg) some roasters report IBTS reading
    LOWER than the contact BT probe well before first crack, i.e. the sign of the offset can
    reverse. Treat any specific IBTS-BT gap as machine/batch-dependent, not a universal constant.
  - If BOTH a contact bean-probe curve and an IBTS curve are shown, they are NOT interchangeable —
    check the legend to see which is which. The contact-probe curve has the classic post-charge
    dip; the IBTS curve does not.
  - RoasTime is Aillio's own app; no fixed color convention (e.g. Artisan's red=BT) is confirmed
    to carry over. Always read the on-image legend rather than assuming colors from memory.
  - Batch size is small (400g–1.2kg) with a wide preheat range (160–310°C) — total roast time is
    typically 8–12 min; do not stretch it toward Probat-length 15–20 min ranges.
  - Controls include 9 power levels, 12 fan speeds, 9 drum speeds. If a bottom control chart shows
    stepped lines, expect discrete integer levels (not smooth curves) — conceptually similar to
    Stronghold's step controls, but the channel names differ (power/fan/drum, not
    열풍/할로겐/드럼히터/교반) — do not reuse Stronghold's Korean labels for this machine.

▶ EASYSTER 800G (이지스터 800, 한국 로스터기 제조사)
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

▶ 후지로얄 Fuji Royal (소형 드럼 — 구체 모델 미확인)
  - This is an older-style small semi-direct-fire drum roaster with NO built-in data port or
    proprietary charting software. In Korea it is almost always paired with an aftermarket
    thermocouple + Artisan (occasionally Cropster) — so a chart labeled "Fuji Royal" actually
    follows ARTISAN's chart conventions (legend, default colors), not a machine-specific skin.
    Apply the Artisan legend-reading rules to it.
  - Some very small/older units expose only ONE temperature reading (drum wall or a single bean
    probe) with no separate ET line. If only one curve is present, treat it as BT and do not
    invent an ET curve.
  - Small batch sizes are common in Korea (R-101 = 1kg, R-105 = 5kg), but total roast time
    (10–15 min) is typical for a small GAS DRUM roaster regardless — do NOT apply the IKAWA
    fluid-bed rule ("short roasts, 3–10 min") just because the batch is small; that rule is
    exclusive to fluid-bed/air roasters, not small drum roasters.
  - Typical operating pattern: drum preheated to ~200℃, then reduced to ~150℃ before charging
    beans — a high preheat/drum-wall reading at the very start of a log is expected and is NOT
    the bean charge temperature; do not confuse the two.
  - No confirmed proprietary Fuji Royal charting app exists in available sources — if a chart
    claims to be a "native Fuji Royal app," treat that claim with caution and default to
    Artisan-style legend reading unless the image clearly shows otherwise.

▶ Giesen (W6 / W15 / W30 시리즈)
  - Standard gas-fired DRUM roaster with an added "indirect-drum heating" jacket meant to spread
    heat more evenly and reduce scorching. Expect a generally SMOOTHER BT curve with fewer sharp
    local spikes than a plain direct-drum design, but the overall S-curve shape and ROR behavior
    is similar to other classic gas drum roasters (Probat, Fuji Royal) rather than to convection
    (Loring) or fluid-bed (IKAWA) machines.
  - Batch sizes scale from 6kg (W6) to 15kg (W15) up to 30–60kg (W30/W60) — total roast time
    (~12–13 min typical) does not scale up much with batch size within this commercial range.
  - Giesen Profiler 2.0 lets users CUSTOMIZE curve colors and line widths — there is NO fixed
    default color scheme confirmed. Never assume a fixed BT/ET color for Giesen; always read the
    on-image legend (this machine is a strong case for the "read the legend first" rule).
  - If a chart is exported via Artisan or Cropster instead of the native Giesen Profiler, follow
    that app's own legend/color conventions instead of assuming a Giesen-specific scheme.
  - Giesen sells MULTIPLE PT100 probe variants (confirmed via Giesen's own parts store): a straight
    AIR/exhaust probe (100mm long, 6mm diameter) and several angled BEAN probes (55mm long in 3mm
    or 6mm diameter, 35mm long 3mm diameter, or 25mm long 3mm diameter), plus a "double read-out"
    option. Probe length/diameter affects thermal lag (shorter/thinner probes respond faster), and
    it is user-selectable per machine — do NOT assume one fixed BT thermal-lag profile for
    "Giesen" as a brand; if the roast looks unusually fast/slow to respond around the turning
    point, this is a plausible explanation rather than a reading error.

▶ IKAWA Pro (50g / 100g)
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
  - IKAWA app roast-log graph: header "예열 온도 / 배출 온도 / 배출 시간" → charge_temp / drop_temp /
    events.drop. Dashed markers "CC m:ss T°C" (color change → events.dry) and "1⚡ m:ss T°C"
    (first crack → events.fcs) print EXHAUST temperatures → labeled_points curve "BT".
    Y axis 0–300°C (50°C grid). Lines continue after drop (cooling) — stop at drop.
  - SHAPE: exhaust dips right after charge, rises fast to ≈150°C in the first minute, runs almost
    flat until color change, then rises to drop. Inlet spikes early (≈20 s), falls to a plateau,
    then rises after color change. Do not draw straight lines between anchors.
  - Fan speed curve (%) has its own axis, usually 60–95%. Report step changes in "agitation"
    as percent ÷ 10 (e.g. 80% → 8).
  - Roasts are SHORT (3–10 min). Do NOT stretch the time axis to drum-roaster lengths —
    this is the single most common error when the machine is misidentified.
  - First crack may be marked by the app (ADFC) — read it if shown.
  - Note "IKAWA fluid-bed" in the notes field so the client applies air-roast rules.
  - CSV export exists: 구형 헤더는 'exaust temp'(원문 오타), 신형은 'temp above'.
    roasting.js 의 IKAWA CSV 파서가 이 두 형태를 모두 인식한다.

▶ Loring (S15 Falcon / S35 Kestrel / S70 Peregrine)
  - Even though beans tumble in a rotating DRUM, the flame does NOT sit under the drum — it heats
    the inlet air, so heat transfer is closer to convection than a Probat/Giesen-style gas drum.
    Expect ROR to respond FASTER to burner changes than a pure conduction drum, though still
    slower than IKAWA (fluid-bed) or Aillio (induction).
  - Built-in afterburner recirculates and combusts exhaust smoke ("smokeless roasting") — do not
    expect a visible smoke/exhaust spike near first crack the way some drum-roaster software
    annotates; the exhaust curve reflects recirculated air temperature, not raw smoke output.
  - A "Roast Profile" in Loring's own software (Roast Architect) is a BT curve defined by
    time/temperature ANCHOR POINTS set before roasting. If a chart shows a smooth planned line
    alongside a jagged actual line, treat the planned line as a target/plan (similar to the
    PROFILE EDITOR handling for IKAWA) — do not merge it into the actual bt_curve.
  - Batch sizes are LARGE commercial scale (S15=15kg, S35=35kg, S70=70kg) yet total roast time is
    still 10–16 min thanks to strong airflow — do not assume a bigger batch means a much longer
    roast the way it would on a plain conduction drum.
  - No fixed native color scheme is confirmed — charts are frequently exported through Cropster
    (which has its own conventions), not a Loring-branded skin. Always read the on-image legend.
  - Loring's own bean probe is confirmed to be a very thin ~1.5mm thermocouple (vs. ~3mm on many
    classic drum roasters, e.g. Diedrich), per Loring's own thermocouple parts listing. Roasters
    comparing machines report this fast probe produces a noticeably TALLER/SHARPER RoR peak right
    at the turning point, a FLATTER-looking RoR through the middle-to-end of the roast, and a
    HIGHER absolute end-of-roast BT reading for the same visual roast color than a slower probe
    would show (one documented comparison: ~415°F on Loring vs ~399–401°F on a Diedrich for a
    similar color). When judging "how developed" a Loring BT curve looks near the end, do not
    assume the same BT-to-color mapping as a classic drum roaster — a higher absolute BT number can
    still be a comparable roast level, not necessarily a hotter/more-developed roast.

▶ Probat (Probatone / P Series)
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

▶ ROEST 샘플 로스터 (노르웨이) — 확인된 모델: S100, S200, L200
  - This is a SMALL-BATCH ELECTRIC sample roaster (batch capacity reported as 50–200g), NOT a
    commercial drum roaster. Do not apply Probat/Loring/Giesen-scale batch or timing assumptions.
  - Heat transfer is described (by manufacturer/reseller sources) as a HYBRID: primarily hot-air
    convection, but beans are tumbled by a rotating drum rather than fluidized/lifted by airflow
    the way IKAWA's fluid-bed works. Treat this as its OWN category — do not apply IKAWA's
    fluid-bed rules (e.g. "no BT probe") automatically; ROEST is reported to have both BT and ET
    probes plus an inlet-air sensor, unlike IKAWA which has no bean probe.
  - OBSERVED PROFILE RANGE (n=1 documented profile config, single academic source, applied to 2
    origins — see profiles/roest-guatemala-*.json): roast start (read) temperature ~165°C, drop
    temperature ~205°C, total roast time 6–7 min, development time (first-crack-to-drop) fixed at
    53 sec by the researchers' controlled protocol. Do NOT treat 6–7 min as ROEST's universal
    range — this is ONE lab's fixed settings for ONE study, not a manufacturer-published range.
    If a chart shows a very different total time (e.g. 3 min or 12+ min), do not force it toward
    6–7 min — ROEST profiles are fully user-programmable and vary widely between users.
  - Because this is a low-thermal-mass small-batch machine, expect FASTER BT response to heater/
    airflow changes than a multi-kg drum roaster, but slower than IKAWA's fluid-bed (which has
    no drum mass at all).
  - No confirmed proprietary chart color scheme was found — read on-image legend, do not assume
    fixed BT/ET colors.
  - When in doubt, prefer "미확인" over inventing a number — this machine has no verified chart
    test yet (see 검증 대기 below).

▶ Stronghold S7X Pro (배치 150g–850g, Roastware / Boost)
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

▶ 태환 Proaster (Taehwan Automation)
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

CRITICAL: report the detected machine in the output "notes" field, e.g.
"machine: IKAWA Pro (fluid-bed)". If the observed values contradict the machine's
typical range above by a wide margin, lower "confidence" and say so in notes rather
than forcing the numbers to fit.

// <<<MACHINE_KNOWLEDGE_END>>>

════════════════════════════════════════
PHASE 2 — DISAMBIGUATE OVERLAPPING LABELS
════════════════════════════════════════
Roastware prints "MM:SS  temp°C" labels with a colored dot at key inflection points.
When TWO labels appear at nearly the same x-position (same time), one belongs to BT and one to ET.

DISAMBIGUATION RULES (apply in order):
1. COLOR OF DOT: The dot next to each label matches its curve color
   (Roastware machine screen: pink/red dot → BT, white/gray dot → ET;
   Boost web page: teal → BT, dark brown → ET).
2. ANCHOR RULE: The rightmost labeled point (latest time, near DROP) always has the highest temperature — this is BT's drop_temp. Anchor BT to this point, then trace back.
3. Y-POSITION RULE (BT vs ET only): among the TWO curves you identified as BT and ET, the one physically higher late in the roast is usually BT. Never apply this to other curves — on the Boost web page the hot-air (열풍) and drum-surface (드럼 표면) curves sit higher than both and are NEITHER BT nor ET.
4. CONSISTENCY RULE: BT must be a smooth curve that ends above ET at drop (Stronghold IR may sit below 내부 for the first ~2 minutes — that is normal). If your assignment creates a contradiction (e.g. BT < ET mid-roast), swap the assignments.

════════════════════════════════════════
PHASE 3 — READ ALL LABELED TEXT VALUES
════════════════════════════════════════
Carefully read every "MM:SS  temp°C" text annotation printed on the top chart.
These are your ground-truth data points — more reliable than pixel tracing.
Convert MM:SS to seconds: minutes×60 + seconds.
CHARGE time = 0s (reference). All other times are relative to CHARGE.
Temperatures are in °C. If in °F, convert: (F-32)×5/9.

Assign each label to BT or ET using the disambiguation rules above.

════════════════════════════════════════
PHASE 4 — TRACE CURVES BETWEEN LABELS
════════════════════════════════════════
Between labeled points, visually interpolate each curve's shape:
- Extract 30–50 additional unlabeled data points per curve
- Keep BT and ET as separate arrays
- Respect the physical shape of THIS machine: drum roasters show a smooth S-curve BT rise with ET
  rising more gradually; fluid-bed roasters (IKAWA) show plateaus (see the IKAWA block) — never
  force a drum S-curve onto them

For the bottom chart 교반 (agitation) STEP line — use the swatch color from PHASE 0:
- Identify the step line whose color EXACTLY matches the 교반 legend swatch.
- Record each step VALUE change as [time_sec, integer_value]
- Values are integers 0–10 read against the panel gridlines; the line may stay at ONE value for the whole roast
- Only record when the step changes, not every second
- Do NOT trace the 할로겐(halogen) line by mistake — re-confirm its color differs
  from the 교반 swatch before recording.

════════════════════════════════════════
PHASE 5 — SELF-VERIFY BEFORE OUTPUT
════════════════════════════════════════
Re-check each binding against its legend swatch color one last time:
- Does the BT curve color == 원두 표면 swatch? Does ET == 내부 swatch?
- Does the agitation line color == 교반 swatch (NOT 할로겐)?
- Did you record only agitation steps that are actually visible (a constant line is valid)?
- Boost web page: is your BT the TEAL line starting ≈55–75°C, not the red 열풍 line?
If any check fails, fix the assignment. If still uncertain, set confidence "low".

════════════════════════════════════════
OUTPUT — return ONLY this JSON, no markdown, no explanation:
════════════════════════════════════════
{
  "curve_identification": {
    "bt_color": "<exact color of 원두 표면 / BT swatch>",
    "et_color": "<exact color of 내부 / ET swatch>",
    "agitation_color": "<exact color of 교반 swatch>",
    "halogen_color": "<exact color of 할로겐 swatch, or null if no bottom chart>",
    "agitation_vs_halogen_check": "<one sentence: how you confirmed 교반 is not 할로겐>"
  },
  "labeled_points": [
    { "time_sec": <number>, "temp_celsius": <number>, "curve": "BT"|"ET", "label_text": "<raw text>" }
  ],
  "bt_curve": [[time_sec, temp_celsius], ...],
  "et_curve": [[time_sec, temp_celsius], ...],
  "agitation": [[time_sec, integer_value], ...],
  "events": {
    "charge": 0,
    "tp":  <seconds or null>,
    "dry": <seconds or null>,
    "fcs": <seconds or null>,
    "fce": <seconds or null>,
    "drop": <seconds>
  },
  "screen_type": "boost_web" | "roastware_device" | "ikawa_app" | "artisan" | "cropster" | "other",
  "series_colors": { "bt": "#rrggbb", "et": "#rrggbb" },
  "charge_temp": <BT celsius at charge>,
  "drop_temp":   <BT celsius at drop>,
  "total_time_sec": <seconds>,
  "confidence": "high" | "medium" | "low",
  "notes": "<note any close-overlap situations and how you resolved them>"
}

════════════════════════════════════════
PLAUSIBILITY PRIORS (from this roastery's real logs)
════════════════════════════════════════
Use these ONLY to sanity-check your reading — values printed on the image always win.
If your reading falls far outside a range, re-read the axis/labels before answering,
and mention it in notes.
▶ Drum roasters (Firescope logs, 400–700g batches, n=35,446; P5–P95):
  total 7.2–11.8 min (median 9.0) · charge BT ~150–223°C (DRUM ONLY — not Stronghold)
  turning point 59–130 s (median 78 s), 104–150°C
  BT reaches 150°C at ~136–265 s, 200°C at ~362–557 s · drop BT 205–224°C (median 212)
  BT RoR at 200°C ≈ 6–13 °C/min, smoothly declining; crashes are rare (~2%)
▶ Stronghold S7X (Boost logs 11,874; detail curves 342; P5–P95):
  total 6.7–10.0 min (median 7.9) · 원두 표면 (IR) at charge 57–76°C, rising with no dip
  turning point measured on 내부: 50–70 s, 101–126°C · drop IR 202–233°C (median 214)
  내부 at drop ≈ IR − 40°C (31–51) · DTR 5.7–19% (median 10.9%)
  할로겐 ends lower than it starts in 88% of roasts · 교반 rises in ~49%, stays constant in ~46%
▶ IKAWA (fluid-bed): total 3–10 min; exhaust ≈ BT proxy.

════════════════════════════════════════
TEXT / SUMMARY SCREENS (no chart visible)
════════════════════════════════════════
Some uploaded images are STAT/LOG screens with labeled text values instead of a
chart — e.g. the IKAWA app roast log (dark screen listing 예열 온도, 배출 온도,
배출 시간, 처음부터 시간, 터닝포인트, 컬러변환시점, 1차 크랙, DTR), or similar
summary pages from other apps. For such images DO NOT invent curves. Instead:
- Read every labeled value and convert times (MM:SS → seconds):
    터닝포인트 / turning point       → events.tp
    컬러변환시점 / color change      → events.dry
    1차 크랙 / first crack           → events.fcs   (e.g. "4:57 (202°C)" → 297)
    배출 시간 / drop time            → events.drop
    예열/투입 온도                    → charge_temp
    배출 온도                        → drop_temp
- Leave bt_curve / et_curve / agitation as [] if no chart is shown.
- Put "text summary screen" in notes.
When MULTIPLE images are given (e.g. one chart + one stat screen), merge: curves
from the chart image, events/temps from the stat screen. Values printed as text
are ground truth — prefer them over pixel estimates when they conflict.

▶ PROFILE EDITOR SCREENS (pre-roast plan — e.g. IKAWA "Edit Points"):
Tables titled 온도 포인트 (time + Exhaust온도) and 팬 포인트 (time + 팬 %).
These are the PLANNED setpoints, NOT the actual roast. Do NOT put them into
bt_curve/events. Instead output them as an extra top-level field:
  "target_profile": {
    "name": "<profile name if shown>",
    "temp_points": [[time_sec, temp_celsius], ...],
    "fan_points":  [[time_sec, fan_percent], ...]
  }
Convert MM:SS → seconds. Ignore the 냉각(cooling) section. If the roast's actual
data comes from another image or file, target_profile simply rides along.

FIELD NOTES:
- screen_type: which screen this is (Boost web detail page, Roastware machine screen, IKAWA app,
  Artisan, Cropster, other). series_colors: the on-screen color of the BT and ET lines as hex,
  sampled from the line pixels. The client uses these to re-trace the curves pixel-by-pixel, so
  give the real color, not a color name.

CRITICAL RULES:
- drop is REQUIRED (from the chart or from a stat screen's 배출 시간)
- bt_curve and et_curve must each have 25–60 points, sorted by time, spanning
  0 → drop — EXCEPT when the only image(s) are text summary screens (then [] is allowed)
- bt_curve must always be >= et_curve at corresponding times after the first 2 minutes
- agitation: use [] only if bottom chart is completely absent from the image
- agitation MUST be traced from the line matching the 교반 swatch color — NEVER the
  할로겐(halogen) line. When in doubt, prefer [] + low confidence over a wrong guess.
- labeled_points: include ALL text annotations visible in the top chart
- Never swap BT and ET — verify with the anchor rule before finalizing
- All curve/line assignments MUST be justified by a matching legend swatch color,
  not by the label name or memorized defaults`

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })

  try {
    const body = await req.json()

    // Accept both new array format and legacy single-image format
    let imageList: Array<{ base64: string; media_type: string }> = []
    if (body.images && Array.isArray(body.images) && body.images.length > 0) {
      imageList = body.images.slice(0, 4)
    } else if (body.image_base64) {
      imageList = [{ base64: body.image_base64, media_type: body.media_type || 'image/jpeg' }]
    }

    if (!imageList.length) {
      return new Response(
        JSON.stringify({ error: '이미지 데이터가 없습니다.' }),
        { status: 400, headers: { ...cors, 'Content-Type': 'application/json' } }
      )
    }

    const key = Deno.env.get('ANTHROPIC_API_KEY')
    if (!key) {
      return new Response(
        JSON.stringify({ error: 'ANTHROPIC_API_KEY가 설정되지 않았습니다. Supabase 대시보드 → Edge Functions → Secrets에서 추가하세요.' }),
        { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
      )
    }

    // Build content array: all images first, then the prompt text
    const content: unknown[] = imageList.map(img => ({
      type: 'image',
      source: { type: 'base64', media_type: img.media_type, data: img.base64 }
    }))
    if (imageList.length > 1) {
      content.push({ type: 'text', text: `You have been provided ${imageList.length} photos of the same roasting profile from different angles or zoom levels. Synthesize all images to extract the most accurate data possible. Image 1 is typically the full overview; subsequent images may show close-ups of specific chart sections or the agitation sub-chart.\n\n` + PROMPT })
    } else {
      content.push({ type: 'text', text: PROMPT })
    }

    const aiResp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': key,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-opus-4-8',
        max_tokens: 6000,
        messages: [{ role: 'user', content }]
      })
    })

    if (!aiResp.ok) {
      const errText = await aiResp.text()
      return new Response(
        JSON.stringify({ error: `Claude API 오류 (${aiResp.status}): ${errText.slice(0, 200)}` }),
        { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
      )
    }

    const ai = await aiResp.json()
    const rawText: string = ai.content?.[0]?.text ?? ''

    // Strip accidental markdown fences
    const clean = rawText.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/i, '').trim()

    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(clean)
    } catch {
      // Try to extract JSON object from within the text
      const match = clean.match(/\{[\s\S]*\}/)
      if (!match) {
        return new Response(
          JSON.stringify({ error: 'AI 응답을 JSON으로 파싱하지 못했습니다.', raw: rawText.slice(0, 500) }),
          { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
        )
      }
      parsed = JSON.parse(match[0])
    }

    return new Response(JSON.stringify(parsed), {
      headers: { ...cors, 'Content-Type': 'application/json' }
    })
  } catch (e) {
    return new Response(
      JSON.stringify({ error: `서버 오류: ${String(e)}` }),
      { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
    )
  }
})
