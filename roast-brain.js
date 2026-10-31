/* 로스팅 판단 두뇌 — 브라우저 쪽 (roasting.html 에서 roasting.js 앞에 로드)
 *
 * scripts/roast_brain.py 가 매주 학습해 data/roast-brain.json 을 만든다.
 *   rules  : 같은 생두를 같은 날 볶아 맛 결과가 갈린 배치 쌍에서 확인된 차이 (예: 오버 배치는 배출 +2.1°C)
 *   models : 맛 결과 예측 모델. 학습에 안 쓴 기록으로 잰 정확도(AUC)가 기준을 넘은 것만 들어 있다 —
 *            기록이 쌓여 두뇌가 자라면 자동으로 켜진다.
 * 특징값 정의는 scripts/roast_brain.py (Firescope 1초 곡선 → features30) 와 똑같다.
 */
(function (root) {
  'use strict';

  /* ── 생두 이름 정규화 (roast_brain.py bean_key 와 같음) ── */
  function beanKey(name) {
    return String(name || '').toLowerCase().replace(/[\s\-_/()[\]]+/g, '').slice(0, 40);
  }

  /* ── 가공방식 (scrapers/common.py guess_process 와 같은 순서·키워드) ── */
  const PROC_RULES = [
    ['펄프드내추럴', ['pulped natural', '펄프드내추럴', '펄프드', 'pulped']],
    ['무산소발효', ['anaerobic', '무산소', '카보닉', 'carbonic', 'infused', '인퓨즈드', '공동발효', 'co-ferment', 'co ferment',
      '코퍼멘', '마세라시온', 'maceration', '써멀', 'thermal', '젖산', 'lactic', '효모', 'yeast', '더블 퍼멘', 'double ferment',
      '카보닉 마세라시온', 'natural anaerobic']],
    ['허니', ['honey', '허니', '레드허니', '화이트허니', '옐로우허니', '블랙허니', '골든허니', 'red honey', 'yellow honey',
      'white honey', 'black honey']],
    ['웻훌드', ['wet hulled', 'wet hul', 'wet-hull', '웻훌', '웻-헐', '웻헐', '웻 헐', 'giling', '길링', '세미워시', '세미 워시',
      'semi washed', 'semi-washed', 'wet polished', 'wet polish']],
    ['내추럴', ['natural', '내추럴', '내츄럴', 'reposado', '레포사도']],
    ['워시드', ['washed', 'fully washed', 'fully-washed', '워시드', '워시', '풀리워시', 'double washed', '더블워시', '수세식', '습식']],
    ['디카페인', ['디카페인', 'decaf', '마운틴워터', 'mountain water', '스위스워터', 'swiss water', '슈가케인', 'sugar cane',
      'sugarcane', 'ethyl acetate']],
  ];
  function guessProcess(text) {
    const n = String(text || '').toLowerCase();
    for (const [name, kws] of PROC_RULES) if (kws.some(k => n.includes(k))) return name;
    return '알수없음';
  }

  /* ── 1초 간격으로 보간 ── */
  function to1s(times, vals) {
    const out = [];
    if (!times || times.length < 2) return out;
    const end = Math.floor(times[times.length - 1]);
    let j = 0;
    for (let t = Math.ceil(times[0]); t <= end; t++) {
      while (j < times.length - 2 && times[j + 1] < t) j++;
      const a = times[j], b = times[j + 1], va = vals[j], vb = vals[j + 1];
      out.push(va == null || vb == null ? NaN : b === a ? va : va + (vb - va) * (t - a) / (b - a));
    }
    return out;
  }

  /* ── 곡선 특징값 (scripts/fs_feat 정의: 터닝포인트 = 150초 안 최저점, RoR = 30초 창) ── */
  function curveFeatures(times, bts) {
    let B = to1s(times, bts);
    const t0 = Math.ceil(times && times.length ? times[0] : 0);
    let n = B.length;
    if (n < 120 || B.some(v => !isFinite(v))) return null;
    const lim = Math.min(n, 150);
    let tp = 0;
    for (let i = 0; i < lim; i++) if (B[i] < B[tp]) tp = i;
    let m = tp;
    for (let i = tp; i < n; i++) if (B[i] > B[m]) m = i;
    if (m < n - 1) { B = B.slice(0, m + 1); n = B.length; }
    const first = th => { for (let i = tp; i < n; i++) if (B[i] >= th) return i; return null; };
    const i150 = first(150), i200 = first(200);
    const R = B.map((_, i) => { const j = Math.max(0, i - 30); return i > j ? (B[i] - B[j]) * 60 / (i - j) : null; });
    const post = R.slice(Math.max(tp + 60, 0)).filter(r => r != null);
    let crash = 0, flick = 0;
    if (i200) {
      const seg = R.slice(i200).filter(r => r != null);
      for (let a = 0; a < seg.length - 30; a += 5) if (seg[a] - seg[a + 30] >= 5) { crash = 1; break; }
      let mn = Infinity;
      for (const v of seg) { mn = Math.min(mn, v); if (v - mn >= 1.5) { flick = 1; break; } }
    }
    const T = i => t0 + i;
    const dur = T(n - 1);
    if (!(dur > 240 && dur < 1500) || !i150 || !i200 || i200 <= i150) return null;
    return {
      total_min: dur / 60, dtr: (dur - T(i200)) / dur * 100, dry_pct: T(i150) / dur * 100,
      mai_pct: (T(i200) - T(i150)) / dur * 100, drop_bt: B[n - 1], charge_bt: B[0], tp_t: T(tp), tp_bt: B[tp],
      ror150: R[i150] != null ? +R[i150].toFixed(2) : NaN, ror200: R[i200] != null ? +R[i200].toFixed(2) : NaN,
      ror_drop: R[n - 1] != null ? +R[n - 1].toFixed(2) : NaN, ror_peak: post.length ? +Math.max(...post).toFixed(2) : NaN,
      crash, flick,
    };
  }

  /* ── 같은 생두의 이전 배치 ── */
  function profileTime(p) { return Date.parse(p.roast_date || p.created_at || '') || 0; }

  function sameBeanHistory(d, profiles) {
    const key = beanKey(d.bean_name);
    if (!key) return [];
    const now = d.id ? profileTime(d) : Infinity;
    return (profiles || [])
      .filter(p => p.id !== d.id && beanKey(p.bean_name) === key && (d.id ? profileTime(p) <= now : true))
      .sort((a, b) => profileTime(b) - profileTime(a));
  }

  function median(vals) {
    const v = vals.filter(x => x != null && isFinite(x)).sort((a, b) => a - b);
    if (!v.length) return null;
    const k = (v.length - 1) / 2;
    return (v[Math.floor(k)] + v[Math.ceil(k)]) / 2;
  }

  /* ── 모델 입력 (roast_brain.py FEATURES 순서) ── */
  function featureVector(brain, d, history) {
    const f = curveFeatures(d.time_series, d.bt_series);
    if (!f) return null;
    const x = Object.assign({}, f);
    x.charge_g = d.charge_weight ?? NaN;
    x.weight_loss = d.weight_loss != null && d.weight_loss > 5 && d.weight_loss < 30 ? d.weight_loss : NaN;
    x.density = NaN; x.moisture = NaN;
    const proc = guessProcess(d.bean_name);
    for (const p of brain.processes || []) x[`proc_${p}`] = proc === p ? 1 : 0;
    const prior = (history || []).slice(0, 10).map(p => curveFeatures(p.time_series, p.bt_series)).filter(Boolean);
    x.prior_roasts = (history || []).length;
    for (const k of ['dtr', 'drop_bt', 'total_min', 'ror200', 'dry_pct']) {
      const vals = prior.map(p => p[k]).filter(v => isFinite(v));
      x[`d_${k}`] = vals.length >= 3 ? x[k] - median(vals) : NaN;
    }
    return brain.features.map(k => (x[k] == null ? NaN : x[k]));
  }

  /* ── 결정 트리 앙상블 (sklearn HistGradientBoosting 을 JSON 으로 옮긴 것) ── */
  function predict(model, xs) {
    let s = model.base;
    for (const tree of model.trees) {
      let i = 0;
      for (;;) {
        const nd = tree[i];
        if (nd[5]) { s += nd[6]; break; }
        const v = xs[nd[0]];
        i = (v == null || Number.isNaN(v)) ? (nd[2] ? nd[3] : nd[4]) : (v <= nd[1] ? nd[3] : nd[4]);
      }
    }
    return 1 / (1 + Math.exp(-s));
  }

  root.RoastBrain = { beanKey, guessProcess, curveFeatures, sameBeanHistory, median, featureVector, predict, profileTime };
  if (typeof module !== 'undefined') module.exports = root.RoastBrain;
})(typeof window !== 'undefined' ? window : globalThis);
