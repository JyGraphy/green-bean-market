import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const PROMPT = `You are a coffee roasting expert with deep knowledge of roasting software chart layouts.
Analyze the roasting profile chart image carefully and extract precise data.
The image may be a direct screenshot or a photo taken of a screen (possibly with slight glare or angle).

════════════════════════════════════════
PHASE 1 — IDENTIFY THE APP & CURVE COLORS
════════════════════════════════════════
Before reading any numbers, identify which app this is and map each curve to its color.

▶ Roastware / Stronghold (dark background, Korean UI "원두 표면 / 내부"):
  TOP CHART — two temperature curves:
    • BT ("원두 표면", bean surface) = PINK / MAGENTA / RED curve
    • ET ("내부", internal drum)     = WHITE / LIGHT GRAY / PALE YELLOW curve
  The legend at bottom-left of the top chart shows "■ 원두 표면  ■ 내부" with matching colors.
  BT (pink) typically rises faster and finishes HIGHER than ET (white) at the drop point.

  BOTTOM CHART — four control step-curves (all different colors):
    • 열풍   (hot air)       = ORANGE / YELLOW step
    • 할로겐 (halogen)       = PINK / MAGENTA step
    • 드럼히터 (drum heater) = TEAL / GREEN step
    • 교반   (agitation)     = BLUE / CYAN step   ← THIS IS WHAT WE NEED
  The legend at bottom-left reads "● 열풍  ■ 할로겐  ■ 드럼히터  ■ 교반".
  교반 is the BLUE step line. Read its step changes (0–10 integer scale).
  The thin white noisy line in the bottom chart is ROR — ignore it here.

▶ Artisan (light or dark background):
  BT = orange/red thick curve, ET = blue curve
  Events: vertical lines labeled CHARGE, DRY END, FC START, FC END, DROP/SCO

▶ Cropster / Firescope / RoasTime:
  BT = boldest colored curve, events marked by vertical dashed lines with text

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

For the bottom chart 교반 (blue step line):
- Record each step VALUE change as [time_sec, integer_value]
- Typical values: 4, 5, 6, 7, 8 etc. (integer 0–10 scale)
- Only record when the step changes, not every second

════════════════════════════════════════
OUTPUT — return ONLY this JSON, no markdown, no explanation:
════════════════════════════════════════
{
  "curve_identification": {
    "bt_color": "<color you identified for BT>",
    "et_color": "<color you identified for ET>",
    "agitation_color": "<color you identified for 교반>"
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
- labeled_points: include ALL text annotations visible in the top chart
- Never swap BT and ET — verify with the anchor rule before finalizing`

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })

  try {
    const { image_base64, media_type = 'image/jpeg' } = await req.json()

    if (!image_base64) {
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
        messages: [{
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type, data: image_base64 } },
            { type: 'text', text: PROMPT }
          ]
        }]
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
