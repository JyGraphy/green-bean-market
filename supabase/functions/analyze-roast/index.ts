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

▶ Roastware / Stronghold (dark background, Korean UI "원두 표면 / 내부"):
  TOP CHART — two temperature curves, legend "■ 원두 표면  ■ 내부":
    • BT = "원두 표면" (bean surface) — match its legend swatch color
    • ET = "내부" (internal drum)     — match its legend swatch color
  Sanity check (use ONLY to catch a mistake, NOT as the primary method):
  BT usually rises faster and finishes HIGHER than ET at the drop point.

  BOTTOM CHART (labeled "열원값" in the Boost web app) — up to four control STEP
  curves. The legend reads "● 열풍 <n>  ● 할로겐 <n>  ● 드럼 히터 <n>  ● 교반 <n>"
  where <n> is that channel's CURRENT value. TYPICAL colors in the Boost web export:
    • 열풍   (hot air)      = ORANGE / RED step
    • 할로겐 (halogen)      = PURPLE / VIOLET step   ← often confused with 교반
    • 드럼 히터 (drum heater) = PINK / MAGENTA step (usually flat)
    • 교반   (agitation)    = GREEN step   ← THIS IS WHAT WE NEED (0–10 integer scale)
  Colors/order can vary by firmware, so ALWAYS confirm against the legend swatch.
  ⚠️ CRITICAL — 할로겐(halogen, purple) and 교반(agitation, green) are the most
  commonly CONFUSED pair. To avoid swapping them:
    1. Read the EXACT swatch color next to 교반 in the bottom-chart legend (green).
    2. Trace ONLY the step line whose color matches that swatch pixel-for-pixel.
    3. BEHAVIOR CUE — 할로겐(halogen) usually DECREASES over the roast, often stepping
       DOWN to 0 near the end. 교반(agitation) commonly HOLDS a mid value then STEPS UP
       near the end of the roast (e.g. 7 → 8 → 9 → 10 in the last 1–2 minutes). If your
       "교반" line is flat the whole time or drops to 0, you likely traced 할로겐 or the
       drum heater — re-check the swatch color and read the FULL length of the line, all
       the way to DROP, so you don't miss late step-ups.
    4. Read the ENTIRE 교반 line to the end — do not assume it is constant. Record every
       step change [time_sec, value], especially any rises in the final third.
    5. If you cannot confidently distinguish them from color, lower "confidence"
       to "low" and say so in "notes" rather than guessing.
  The thin noisy line in the bottom chart is ROR — ignore it here.

▶ IKAWA (Pro app / Home app; clean minimal UI, light or dark):
  FLUID-BED air roaster — there is NO bean-temperature probe. The graph shows:
    • Temperature curves: setpoint (target) vs actual AIR temperature
      (inlet and/or exhaust). If both shown, treat EXHAUST as BT and INLET as ET.
      If only one temperature line, output it as BT.
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
// 등록 기기 8대

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
| 후지로얄 Fuji Royal (R-101 / R-105 등 소형 드럼) | 드럼(전도) — 반직화식(semi-direct fire) 가스 드럼 | 내장 프로브 없음 (국내는 후장착 서모커플+Artisan 조합) | 10–15분 (드럼을 약 200℃로 예열 후 150℃ 부근으로 낮춰 투입) | Artisan (자체 차트 앱 없음 — 후장착 프로브+Artisan 조합이 일반적) |
| Giesen (W6 / W15 / W30 시리즈) | 드럼(전도) — 가스버너 + 간접 드럼 가열(indirect-drum) 재킷 | BT+ET 옵션 (PT100 이중 프로브) | 약 12–13분 (실측 예: 브라질 옐로우 부르봉, 최종 BT 200℃ 기준 4회 평균 12:50) | Artisan / Cropster / Giesen Profiler (자체 소프트웨어, 2.0부터 색상 커스터마이징 가능) |
| IKAWA Pro (50g / 100g) | 열풍(대류) — fluid-bed | 배기온도만 (원두 프로브 없음) | 3–10분 | IKAWA Pro app |
| Loring (S15 Falcon / S35 Kestrel / S70 Peregrine) | 열풍(대류) — single burner heats inlet air, not the drum (smokeless afterburner) | BT(빠른 ~1.5mm 프로브)+ET(배기) | 10–16분 (예: S15 배치 15kg). 대형기(S35/S70)도 배치만 커질 뿐 시간대는 유사 | Cropster (Roasting Intelligence) / Loring 자체 제어 소프트웨어 ("Roast Architect") |
| Probat (Probatone / P Series) | 드럼(전도) — gas burner + drum/air thermocouples | BT+ET (P series 표준, 구형 Probatone 2 base는 BT만) | 10–20분 (상업용 배치 5–60kg) | Artisan / Cropster (자체 차트 앱 없음, 외부 소프트웨어 연동) |
| Stronghold (Roastware / Boost) | 하이브리드 — 열풍 + 할로겐(복사) + 드럼히터(전도) | BT+ET (원두 표면 / 내부) | 10–16분 | Roastware / Boost web app (dark UI, Korean labels) |
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

▶ 후지로얄 Fuji Royal (R-101 / R-105 등 소형 드럼)
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

▶ Stronghold (Roastware / Boost)
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
1. COLOR OF DOT: The dot next to each label matches its curve color.
   Pink/red dot → BT label. White/gray dot → ET label.
2. ANCHOR RULE: The rightmost labeled point (latest time, near DROP) always has the highest temperature — this is BT's drop_temp. Anchor BT to this point, then trace back.
3. Y-POSITION RULE: At any given time after the first minute, the curve that is PHYSICALLY HIGHER on the chart is BT (pink). Assign the higher temperature value to BT, lower to ET.
4. CONSISTENCY RULE: BT must always be a smooth monotonically increasing curve that is above ET after the turning point. If your assignment creates a contradiction (e.g. BT < ET mid-roast), swap the assignments.

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
- Keep BT (pink) and ET (white) as separate arrays
- Respect the physical shape: BT has S-curve rise; ET rises more linearly/gradually

For the bottom chart 교반 (agitation) STEP line — use the swatch color from PHASE 0:
- Identify the step line whose color EXACTLY matches the 교반 legend swatch.
- Record each step VALUE change as [time_sec, integer_value]
- Typical agitation values: step through several mid levels e.g. 4, 5, 6, 7, 8 (0–10 scale)
- Only record when the step changes, not every second
- Do NOT trace the 할로겐(halogen) line by mistake — re-confirm its color differs
  from the 교반 swatch before recording.

════════════════════════════════════════
PHASE 5 — SELF-VERIFY BEFORE OUTPUT
════════════════════════════════════════
Re-check each binding against its legend swatch color one last time:
- Does the BT curve color == 원두 표면 swatch? Does ET == 내부 swatch?
- Does the agitation line color == 교반 swatch (NOT 할로겐)?
- Is agitation a multi-level mid-range step (not a binary on/off like halogen)?
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
  "charge_temp": <BT celsius at charge>,
  "drop_temp":   <BT celsius at drop>,
  "total_time_sec": <seconds>,
  "confidence": "high" | "medium" | "low",
  "notes": "<note any close-overlap situations and how you resolved them>"
}

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
