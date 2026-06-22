import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

const PROMPT = `You are analyzing a coffee roasting profile chart image from software like Artisan, Cropster, Firescope, RoasTime, or Stronghold Boost.

Extract the roasting data and return ONLY a valid JSON object with NO markdown or extra text:

{
  "bt_curve": [[time_seconds, temperature_celsius], ...],
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
  "confidence": "high" | "medium" | "low"
}

Rules:
- All time values are SECONDS from CHARGE (charge = 0)
- All temperatures are °C (convert from °F if axis shows °F: (F-32)*5/9)
- bt_curve: extract 40-60 evenly distributed points along the BT (bean temperature) curve ONLY — NOT the ROR/green curve or ET curve
- bt_curve must span from 0 seconds (charge) to drop time
- Events: read axis labels and vertical marker lines carefully; use null if not visible
- drop is REQUIRED — use end of BT curve if DROP label is absent
- Return ONLY the JSON object, nothing else`

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })

  try {
    const { image_base64, media_type = 'image/jpeg' } = await req.json()

    const key = Deno.env.get('ANTHROPIC_API_KEY')
    if (!key) {
      return new Response(
        JSON.stringify({ error: 'ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.' }),
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
        max_tokens: 2048,
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
      const err = await aiResp.text()
      return new Response(
        JSON.stringify({ error: `Claude API 오류: ${aiResp.status} ${err}` }),
        { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
      )
    }

    const ai = await aiResp.json()
    const text: string = ai.content?.[0]?.text ?? ''

    // Strip any accidental markdown fences
    const clean = text.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
    const parsed = JSON.parse(clean)

    return new Response(JSON.stringify(parsed), {
      headers: { ...cors, 'Content-Type': 'application/json' }
    })
  } catch (e) {
    return new Response(
      JSON.stringify({ error: String(e) }),
      { status: 500, headers: { ...cors, 'Content-Type': 'application/json' } }
    )
  }
})
