import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const PROMPT = `You are a coffee roasting expert analyzing a roasting profile chart image.
The image may come from apps like Roastware, Artisan, Cropster, Firescope, RoasTime, or Stronghold Boost.
The image may be a direct screenshot or a photo taken of a screen (possibly with glare or slight angle).

== STEP 1: READ TEXT LABELS FIRST (most reliable) ==
Many apps print time+temperature labels directly on the chart as text like "07:00 216.7°C" or "01:15 115.1°C".
READ THESE PRINTED NUMBERS before attempting to trace curves visually.
They are your highest-accuracy data points even if the image has glare or angle distortion.

== STEP 2: IDENTIFY APP LAYOUT ==

Roastware (dark background, Korean UI):
- Two main curves: "원두 표면" (bean surface = BT, pink/red curve) and "내부" (internal = ET, gray/white curve)
- Labeled dots appear at key inflection points with "MM:SS temp°C" text
- Phase bars at top show timing: e.g. "02:48 | 40.0%" = 2 min 48 sec phase
- Time axis: MM:SS format (00:00 to ~10:00)
- ROR curve in bottom sub-chart — IGNORE this, only use top chart

Artisan (light or dark background):
- BT = orange/red curve (Bean Temp), ET = blue curve (Environment Temp)
- Event markers: CHARGE, TP, DRY END, FC START, FC END, DROP as vertical lines with labels
- X-axis in MM:SS or decimal minutes

Cropster / Firescope / RoasTime:
- BT curve is typically the boldest colored curve
- Vertical dashed lines mark events with text labels

== STEP 3: EXTRACT DATA ==

From text labels and curve: collect time+temperature pairs along the BT curve.
Convert all times to SECONDS from CHARGE (charge moment = 0 seconds).
If time is shown as MM:SS, convert: minutes×60 + seconds.
If temperature is in °F, convert to °C: (F - 32) × 5/9.

Collect at minimum: CHARGE, any labeled mid-curve points, and DROP.
Then estimate 10-20 additional unlabeled points by visually interpolating the curve shape.

== OUTPUT FORMAT ==
Return ONLY a valid JSON object, no markdown, no explanation:

{
  "labeled_points": [[time_sec, temp_celsius, "label_or_empty"], ...],
  "bt_curve": [[time_sec, temp_celsius], ...],
  "events": {
    "charge": 0,
    "tp": <seconds or null>,
    "dry": <seconds or null>,
    "fcs": <seconds or null>,
    "fce": <seconds or null>,
    "drop": <seconds>
  },
  "charge_temp": <celsius>,
  "drop_temp": <celsius>,
  "total_time_sec": <seconds>,
  "confidence": "high" | "medium" | "low",
  "notes": "<brief note about image quality or any uncertainty>"
}

Rules:
- charge is always 0 (your reference point)
- drop is REQUIRED — use last visible BT data point if DROP label absent
- bt_curve must include labeled_points merged in, sorted by time, spanning 0 to drop time, 25-60 total points
- If a value is genuinely unreadable, use null (never guess wildly)
- confidence: "high" if text labels clear + image sharp; "medium" if some glare/angle; "low" if heavily obscured`

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
        max_tokens: 4096,
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
