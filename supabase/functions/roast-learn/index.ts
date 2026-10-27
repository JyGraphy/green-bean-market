// 로스팅 AI 누적 학습 기록 함수
//
// 사이트에서 프로파일을 분석할 때마다(저장 여부와 무관) 판독 결과를 비공개 스토리지에 쌓는다.
// 매주 roast-learning.yml 이 이 기록을 모아 기준값 재계산·판독 정확도 재측정·규칙 갱신을 한다.
//   - AI 원본 판독, 픽셀 추출 결과, 화면 종류·기기
//   - 데이터 파일을 함께 올린 경우 그 곡선(= 정답) → 자동으로 검증 사례가 된다
//   - 사용자가 동의한 경우에만 사진 원본
//
// 저장 위치: Storage 버킷 'roast-learning' (비공개). 공개 저장소(GitHub)에는 원본을 두지 않는다.
// 인증: 로그인한 사용자 토큰만 받는다(익명 키 거부).
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.45.4'

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}
const BUCKET = 'roast-learning'
const MAX_IMAGES = 4
const MAX_IMAGE_BYTES = 6 * 1024 * 1024
const MAX_READING_BYTES = 2 * 1024 * 1024   // 판독 기록(JSON) 상한 — 5초 곡선 수백 점 + AI 원본이면 수십 KB

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } })

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors })
  if (req.method !== 'POST') return json({ error: 'POST only' }, 405)

  const url = Deno.env.get('SUPABASE_URL')!
  const service = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  const admin = createClient(url, service, { auth: { persistSession: false } })

  // 로그인 사용자 확인 (익명 키로는 user 가 없다)
  const jwt = (req.headers.get('authorization') || '').replace(/^Bearer\s+/i, '')
  const { data: userData } = await admin.auth.getUser(jwt)
  const user = userData?.user
  if (!user) return json({ error: '로그인이 필요합니다.' }, 401)

  let body: any
  try { body = await req.json() } catch { return json({ error: 'JSON 본문이 필요합니다.' }, 400) }
  if (body?.action !== 'log' || !body.reading || typeof body.reading !== 'object') return json({ error: '잘못된 요청' }, 400)
  const readingText = JSON.stringify(body.reading)
  if (readingText.length > MAX_READING_BYTES) return json({ error: '기록이 너무 큽니다.' }, 413)

  // 버킷이 없으면 만든다 (비공개)
  const { error: bErr } = await admin.storage.getBucket(BUCKET)
  if (bErr) await admin.storage.createBucket(BUCKET, { public: false })

  const now = new Date()
  const month = now.toISOString().slice(0, 7)
  const id = `${now.toISOString().replace(/[:.]/g, '-')}_${crypto.randomUUID().slice(0, 8)}`
  const base = `readings/${month}/${id}`

  const images: string[] = []
  if (body.consent === true && Array.isArray(body.images)) {
    for (const [i, im] of body.images.slice(0, MAX_IMAGES).entries()) {
      try {
        const bytes = Uint8Array.from(atob(String(im.base64 || '')), c => c.charCodeAt(0))
        if (!bytes.length || bytes.length > MAX_IMAGE_BYTES) continue
        const type = String(im.media_type || 'image/png')
        const ext = type.includes('jpeg') || type.includes('jpg') ? 'jpg' : type.includes('webp') ? 'webp' : 'png'
        const path = `${base}_${i}.${ext}`
        const { error } = await admin.storage.from(BUCKET).upload(path, bytes, { contentType: type, upsert: false })
        if (!error) images.push(path)
      } catch { /* 이미지 하나 실패는 기록 전체를 막지 않는다 */ }
    }
  }

  // 서버가 정하는 필드를 뒤에 둬서 클라이언트 값이 덮어쓰지 못하게 한다
  const record = {
    ...body.reading,
    id, created_at: now.toISOString(), user_id: user.id,
    consent: body.consent === true, images,
  }
  const { error } = await admin.storage.from(BUCKET)
    .upload(`${base}.json`, new TextEncoder().encode(JSON.stringify(record)), { contentType: 'application/json', upsert: false })
  if (error) return json({ error: `기록 저장 실패: ${error.message}` }, 500)
  return json({ ok: true, id, images: images.length })
})
