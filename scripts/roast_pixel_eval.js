#!/usr/bin/env node
/* 로스팅 AI 누적 학습 ③ — 판독 벤치마크 평가기 (scripts/roast_benchmark.py 가 호출).
 *
 * 사이트와 **똑같은 코드**로 곡선을 만든 뒤 정답과 비교한다.
 *   - 픽셀 추출: roast-pixel.js 그대로
 *   - AI 곡선 보정·앵커·기기 판별: roasting.js 의 aiAnchors / anchorBlend / detectMachineFromScan 을
 *     소스에서 그대로 꺼내 쓴다 (이름이 바뀌면 여기서 바로 실패하므로 조용히 어긋나지 않는다)
 *
 * 사용법: node scripts/roast_pixel_eval.js jobs.json > results.json
 *   jobs.json = [{ id, set, screen_type, roaster, rgba, w, h, ai:{…}, truth:{…} }]
 *   truth = { bt:[[t,°C]], et:[[t,°C]], agitation:[[t,v]], events:{tp,drop}, drop_t, drop_temp }  (곡선 정답)
 *         또는 { anchors_bt:[[t,°C]], events, drop_temp }                                     (화면 표시값 정답)
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const RoastPixel = require(path.join(ROOT, 'roast-pixel.js'));
const SRC = fs.readFileSync(path.join(ROOT, 'roasting.js'), 'utf8');

function grabFunction(name) {
  const i = SRC.indexOf(`function ${name}(`);
  if (i < 0) throw new Error(`roasting.js 에 ${name}() 가 없습니다`);
  const j = SRC.indexOf('{', i);
  for (let k = j, d = 0; k < SRC.length; k++) {
    if (SRC[k] === '{') d++;
    else if (SRC[k] === '}' && --d === 0) return SRC.slice(i, k + 1);
  }
  throw new Error(`${name}() 끝을 못 찾음`);
}
function grabLine(prefix) {
  const line = SRC.split('\n').find(l => l.startsWith(prefix));
  if (!line) throw new Error(`roasting.js 에 '${prefix}' 가 없습니다`);
  return line;
}
const site = new Function(
  [grabLine('const FLUID_BED_PATTERNS'),
   ...['interp', 'detectFluidBed', 'detectMachineFromScan', 'aiAnchors', 'anchorBlend'].map(grabFunction),
   'return { interp, detectMachineFromScan, aiAnchors, anchorBlend };'].join('\n'))();

// ── 비교 지표 ([[t, v]] 정렬 배열) ──
const lin = (p, t) => {
  if (t <= p[0][0]) return p[0][1];
  if (t >= p[p.length - 1][0]) return p[p.length - 1][1];
  let lo = 0, hi = p.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (p[m][0] <= t) lo = m; else hi = m; }
  const [a, va] = p[lo], [b, vb] = p[hi];
  return b === a ? va : va + (vb - va) * (t - a) / (b - a);
};
const step = (p, t) => { let v = p[0][1]; for (const [a, va] of p) if (a <= t) v = va; return v; };
const ror30 = (p, ts) => {
  const v = ts.map(t => lin(p, t)), out = {};
  ts.forEach((t, i) => { let j = i; while (j > 0 && t - ts[j] < 30) j--; if (t > ts[j]) out[t] = (v[i] - v[j]) / (t - ts[j]) * 60; });
  return out;
};
const mean = a => a.length ? a.reduce((s, x) => s + x, 0) / a.length : null;
const r2 = x => x == null || !isFinite(x) ? null : Math.round(x * 100) / 100;
const toPairs = pts => (pts || []).filter(p => isFinite(p.t) && isFinite(p.bt)).map(p => [p.t, p.bt]).sort((a, b) => a[0] - b[0]);

function curveErrors(bt, et, agit, truth, dropT) {
  const out = {};
  if (bt.length >= 2 && truth.bt && truth.bt.length >= 2) {
    const ts = []; for (let t = 10; t < dropT; t += 5) ts.push(t);
    const e = ts.map(t => Math.abs(lin(bt, t) - lin(truth.bt, t)));
    out.bt_mae = r2(mean(e)); out.bt_max = r2(Math.max(...e));
    const a = ror30(bt, ts), b = ror30(truth.bt, ts);
    out.ror_mae = r2(mean(ts.filter(t => t >= 90 && a[t] != null && b[t] != null).map(t => Math.abs(a[t] - b[t]))));
    if (et.length >= 2 && truth.et && truth.et.length >= 2)
      out.et_mae = r2(mean(ts.map(t => Math.abs(lin(et, t) - lin(truth.et, t)))));
    if (agit.length && truth.agitation && truth.agitation.length)
      out.agit_match = r2(ts.filter(t => step(agit, t) === step(truth.agitation, t)).length / ts.length * 100);
  }
  if (bt.length >= 2 && truth.anchors_bt && truth.anchors_bt.length)
    out.anchor_mae = r2(mean(truth.anchors_bt.map(([t, T]) => Math.abs(lin(bt, t) - T))));
  return out;
}

function evaluate(job) {
  const ai = job.ai || {}, truth = job.truth || {};
  const machine = site.detectMachineFromScan(ai, job.roaster || '');
  const screenType = job.screen_type || machine.screenType;
  const { rawCurve, rawEt, evDrop, anchorsBt, anchorsEt } = site.aiAnchors(ai);
  const truthDrop = (truth.events && truth.events.drop) || truth.drop_t ||
    (truth.bt && truth.bt.length ? truth.bt[truth.bt.length - 1][0] : null);
  const dropT = truthDrop || evDrop;
  const out = { id: job.id, set: job.set, screen_type: screenType, machine: machine.name };

  let pix = { ok: false, reason: '이미지 없음' };
  if (job.rgba && evDrop) {
    try {
      const img = { width: job.w, height: job.h, data: fs.readFileSync(job.rgba) };
      pix = RoastPixel.extract(img, { screenType, colors: ai.series_colors || {}, dropT: evDrop, anchorsBt, anchorsEt });
    } catch (e) { pix = { ok: false, reason: `오류: ${e.message}` }; }
  } else if (!evDrop) pix = { ok: false, reason: 'AI가 배출 시점을 못 읽음' };
  out.pixel = { ok: !!pix.ok, reason: pix.reason || null, max_res: r2(pix.maxRes), anchors: pix.anchorsUsed ?? null, time_ref: pix.timeRef || null };

  // AI 곡선만 썼을 때 (픽셀 추출이 없던 예전 방식) vs 사이트가 실제로 쓰는 곡선
  const aiBt = toPairs(site.anchorBlend(rawCurve, anchorsBt));
  const aiEt = toPairs(site.anchorBlend(rawEt, anchorsEt));
  const aiAg = (ai.agitation || []).map(([t, v]) => [+t, +v]).sort((a, b) => a[0] - b[0]);
  out.ai = dropT ? curveErrors(aiBt, aiEt, aiAg, truth, dropT) : {};
  if (pix.ok) {
    const bt = toPairs(pix.btPts);
    const et = pix.etPts && pix.etPts.length >= 2 ? toPairs(pix.etPts) : aiEt;
    const ag = pix.agitSorted && pix.agitSorted.length ? pix.agitSorted.map(s => [s.t, s.v]) : aiAg;
    out.site = curveErrors(bt, et, ag, truth, dropT);
  } else out.site = out.ai;

  // 텍스트 값 판독 (AI)
  if (evDrop && truthDrop) out.drop_t_err = r2(Math.abs(evDrop - truthDrop));
  const truthDropTemp = truth.drop_temp ?? (truth.bt && truthDrop ? lin(truth.bt, truthDrop) : null);
  if (ai.drop_temp != null && truthDropTemp != null) out.drop_temp_err = r2(Math.abs(+ai.drop_temp - truthDropTemp));
  const aiTp = ai.events && ai.events.tp;
  if (aiTp != null && truth.events && truth.events.tp != null) out.tp_err = r2(Math.abs(aiTp - truth.events.tp));
  return out;
}

const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const results = jobs.map(j => { try { return evaluate(j); } catch (e) { return { id: j.id, set: j.set, error: e.message }; } });
process.stdout.write(JSON.stringify(results));
