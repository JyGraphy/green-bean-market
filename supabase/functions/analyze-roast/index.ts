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

CRITICAL RULES:
- drop is REQUIRED
- bt_curve and et_curve must each have 25–60 points, sorted by time, spanning 0 → drop
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
