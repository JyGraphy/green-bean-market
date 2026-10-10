'use strict';
/* ════════════════════════════════════════════════════════════
   로스팅 그래프 픽셀 추출 (하이브리드 판독의 '숫자' 담당)

   AI 비전은 화면 종류·곡선 색·타임라인 텍스트(앵커)를 정확히 읽지만, 곡선을 눈으로
   따라 읽으면 중반 오차가 6~25°C 남는다. 곡선 숫자는 이 모듈이 픽셀에서 직접 뽑는다.

   입력: { width, height, data(RGBA) } — 브라우저 canvas.getImageData 또는 테스트용 버퍼
   방법:
     1. 지정 색 픽셀을 열마다 찾아 곡선 경로(x→y)를 만든다. 같은 색이 여러 묶음이면
        맨 위 묶음(온도 패널)을 쓴다 — Boost는 아래 RoR 패널에 같은 색 선이 있다.
     2. 시간: 곡선 시작 = 투입(0초), 가장 뜨거운 지점 이후 온도가 떨어지기 시작하는 곳 = 배출.
        (이카와처럼 배출 뒤 냉각 구간이 이어지는 화면도 처리)
     3. 온도: AI가 읽은 텍스트 앵커(t, °C)로 y→°C 직선을 맞추고, 가로 눈금선 간격이
        보이면 기울기를 '깔끔한 눈금 단위(10/20/25/50/100°C)'로 고정한 뒤 절편만 맞춘다.
     4. 검증: 앵커 잔차가 maxResidual(기본 3°C)을 넘으면 실패로 돌려준다 → AI 판독으로 폴백.
   검증 기록: Boost 웹 상세 화면 17건에서 BT 평균 오차 1.2°C, RoR 0.6°C/분, 교반 16/16.
   ════════════════════════════════════════════════════════════ */

const RoastPixel = (() => {
  // 화면 종류별 곡선 색 (실측 화면에서 샘플링)
  const TEMPLATES = {
    boost_web: { bt: [64, 168, 168], et: [80, 56, 16], agit: [8, 160, 64], heatRef: [208, 24, 96], tol: 45 },
    // timeFill: 투입~배출 구간에만 칠해지는 팬(fan) 영역 색 — 이 영역의 좌우 끝이 0초·배출
    ikawa_app: { bt: [210, 125, 115], et: [230, 182, 132], timeFill: [129, 95, 91], tol: 32 },
  };
  const NICE_STEPS = [5, 10, 20, 25, 50, 100, 200];

  function hexToRgb(h) {
    const m = /^#?([0-9a-f]{6})$/i.exec(String(h || '').trim());
    if (!m) return null;
    const n = parseInt(m[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  function px(img, x, y) {
    const i = (y * img.width + x) * 4;
    return [img.data[i], img.data[i + 1], img.data[i + 2]];
  }

  function dist(a, b) {
    const dr = a[0] - b[0], dg = a[1] - b[1], db = a[2] - b[2];
    return Math.sqrt(dr * dr + dg * dg + db * db);
  }

  /* 배경색: 그래프 영역에서 가장 흔한 색 (흰 배경 Boost, 어두운 배경 이카와 모두 대응) */
  function backgroundColor(img) {
    const counts = new Map();
    const sx = Math.max(1, Math.floor(img.width / 120)), sy = Math.max(1, Math.floor(img.height / 120));
    for (let y = 0; y < img.height; y += sy) for (let x = 0; x < img.width; x += sx) {
      const c = px(img, x, y), k = (c[0] >> 3) << 10 | (c[1] >> 3) << 5 | (c[2] >> 3);
      counts.set(k, (counts.get(k) || 0) + 1);
    }
    let best = 0, bestN = -1;
    for (const [k, n] of counts) if (n > bestN) { bestN = n; best = k; }
    return [((best >> 10) & 31) * 8 + 4, ((best >> 5) & 31) * 8 + 4, (best & 31) * 8 + 4];
  }

  /* 선 픽셀 판별 → 0(아님) / 1(옅은 혼합: 안티앨리어싱 가장자리·축소 이미지) / 2(진한 일치).
     픽셀 P가 배경 B와 선 색 C의 혼합(B + α(C−B))에 가깝고 α가 충분히 크면 선이다.
     해상도·안티앨리어싱으로 색이 옅어져도 잡고, 반투명 참조 프로파일(α≈0.3~0.5)은 거른다. */
  function makeMatcher(color, bg, tol) {
    const d = [color[0] - bg[0], color[1] - bg[1], color[2] - bg[2]];
    const dd = d[0] * d[0] + d[1] * d[1] + d[2] * d[2] || 1;
    return c => {
      if (dist(c, color) < tol) return 2;
      const v = [c[0] - bg[0], c[1] - bg[1], c[2] - bg[2]];
      const alpha = (v[0] * d[0] + v[1] * d[1] + v[2] * d[2]) / dd;
      if (alpha < 0.55 || alpha > 1.15) return 0;
      const r = Math.hypot(v[0] - alpha * d[0], v[1] - alpha * d[1], v[2] - alpha * d[2]);
      return r < 16 ? 1 : 0;
    };
  }

  /* 열마다 선 픽셀 묶음들의 중심 y 목록. 너무 큰 묶음(색 블록·범례)은 버린다.
     한 열에 진한 묶음이 있으면 옅은 묶음(참조 프로파일 등)은 버린다. */
  function columnClusters(img, color, tol, yMin, yMax, xMin, xMax) {
    const match = makeMatcher(color, img._bg || (img._bg = backgroundColor(img)), tol);
    const maxThick = Math.max(12, Math.round(img.height / 110));
    const cols = new Map();
    for (let x = xMin; x <= xMax; x++) {
      const cl = [];
      for (let y = yMin; y <= yMax; y++) {
        const m = match(px(img, x, y));
        if (!m) continue;
        const last = cl[cl.length - 1];
        if (last && y - last[1] <= 2) { last[1] = y; last[2] = Math.max(last[2], m); } else cl.push([y, y, m]);
      }
      let ok = cl.filter(([a, b]) => b - a <= maxThick);
      if (ok.some(c => c[2] === 2)) ok = ok.filter(c => c[2] === 2);
      const c = ok.map(([a, b]) => (a + b) / 2);
      if (c.length) cols.set(x, c);
    }
    return cols;
  }

  /* 이웃 점(자기 자신 제외, 앞뒤 W개)으로 직선 추세를 맞춰 i 위치의 예측 y.
     중앙값과 달리 가파른 기울기·완만한 꼭짓점(인렛 초반 급상승 등)을 이상치로 오인하지 않는다. */
  function trendAt(xs, ys, i, W) {
    let n = 0, sx = 0, sy = 0, sxx = 0, sxy = 0;
    for (let j = Math.max(0, i - W); j <= Math.min(xs.length - 1, i + W); j++) {
      if (j === i) continue;
      const x = xs[j] - xs[i], y = ys[j];
      n++; sx += x; sy += y; sxx += x * x; sxy += x * y;
    }
    if (n < 3) return null;
    const den = n * sxx - sx * sx;
    if (!den) return sy / n;
    const slope = (n * sxy - sx * sy) / den;
    return (sy - slope * sx) / n;           // 상대좌표 0(= xs[i])에서의 예측값
  }

  /* 곡선 경로: 기본은 맨 위 묶음(온도 패널). 선이 가려진 열에서는 아래 RoR 패널의 같은 색을
     집어 와 튀므로, 이웃 추세(직선 맞춤)와 중앙값 중 가까운 쪽에서 멀리 벗어난 점은 버린다. */
  function traceColumns(img, color, tol, yMin = 0, yMax = img.height - 1, xMin = 0, xMax = img.width - 1) {
    const cols = columnClusters(img, color, tol, yMin, yMax, xMin, xMax);
    const xs = [...cols.keys()].sort((a, b) => a - b);
    const top = xs.map(x => cols.get(x)[0]);
    const maxDev = Math.max(6, img.height * 0.012);
    const ys = new Map();
    for (let i = 0; i < xs.length; i++) {
      const win = top.slice(Math.max(0, i - 15), i + 16).sort((a, b) => a - b);
      const med = win[win.length >> 1];
      const tr = trendAt(xs, top, i, 15);
      const devOf = c => Math.min(Math.abs(c - med), tr == null ? Infinity : Math.abs(c - tr));
      const best = cols.get(xs[i]).reduce((p, c) => devOf(c) < devOf(p) ? c : p);
      if (devOf(best) <= maxDev) ys.set(xs[i], best);
    }
    return despike(ys, maxDev);
  }

  /* 최종 경로에서 이웃 추세와 동떨어진 점 제거 — 선이 오래 가려진 구간에 남은 다른 패널의
     같은 색 점을 지운다. 좁은 창(직선 추세) 두 번 + 넓은 창(중앙값, 큰 덩어리 오류만) 한 번. */
  function despike(ys, maxDev) {
    for (let pass = 0; pass < 2; pass++) {
      const xs = [...ys.keys()].sort((a, b) => a - b), vals = xs.map(x => ys.get(x));
      for (let i = 0; i < xs.length; i++) {
        const tr = trendAt(xs, vals, i, 8);
        if (tr != null && Math.abs(vals[i] - tr) > maxDev) ys.delete(xs[i]);
      }
    }
    const xs = [...ys.keys()].sort((a, b) => a - b), vals = xs.map(x => ys.get(x));
    const W = Math.max(40, Math.round(xs.length * 0.08));
    for (let i = 0; i < xs.length; i++) {
      const nb = vals.slice(Math.max(0, i - W), i + W + 1).sort((a, b) => a - b);
      if (Math.abs(vals[i] - nb[nb.length >> 1]) > maxDev * 4) ys.delete(xs[i]);
    }
    return ys;
  }

  /* 가장 긴 연속 구간(틈 ≤ maxGap)의 [x, y] 목록 — 범례·상태 카드의 같은 색 조각을 걸러낸다 */
  function longestRun(ys, maxGap = 14) {
    const xs = [...ys.keys()].sort((a, b) => a - b);
    let best = [], cur = [];
    for (const x of xs) {
      if (cur.length && x - cur[cur.length - 1] > maxGap) {
        if (cur.length > best.length) best = cur;
        cur = [];
      }
      cur.push(x);
    }
    if (cur.length > best.length) best = cur;
    return best.map(x => [x, ys.get(x)]);
  }

  function yAt(path, x) {
    if (!path.length) return null;
    if (x <= path[0][0]) return path[0][1];
    if (x >= path[path.length - 1][0]) return path[path.length - 1][1];
    let lo = 0, hi = path.length - 1;
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (path[m][0] <= x) lo = m; else hi = m; }
    const [x0, y0] = path[lo], [x1, y1] = path[hi];
    return x1 === x0 ? y0 : y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }

  /* 배출 x: 가장 뜨거운(가장 위) 지점 이후, 온도가 dropFrac만큼 떨어지기 직전 */
  function findDropX(path) {
    const ys = path.map(p => p[1]);
    const span = Math.max(...ys) - Math.min(...ys);
    let iMax = 0;
    for (let i = 1; i < path.length; i++) if (ys[i] <= ys[iMax]) iMax = i;  // 동률이면 오른쪽
    const thr = ys[iMax] + Math.max(4, span * 0.04);
    for (let i = iMax; i < path.length; i++) if (ys[i] > thr) {
      // 떨어지기 시작한 지점: 최고점 근처 높이를 마지막으로 유지한 x
      let j = i - 1;
      while (j > iMax && ys[j] > ys[iMax] + 2) j--;
      return path[j][0];
    }
    return path[path.length - 1][0];
  }

  /* 가로 눈금선 행 검출 → 우세 간격(px). 없으면 null */
  function gridSpacing(img, x0, x1, y0, y1) {
    const step = Math.max(1, Math.floor((x1 - x0) / 300));
    const lum = [];
    for (let y = y0; y <= y1; y++) {
      const vals = [];
      for (let x = x0; x <= x1; x += step) { const c = px(img, x, y); vals.push((c[0] + c[1] + c[2]) / 3); }
      vals.sort((a, b) => a - b);
      lum.push(vals[vals.length >> 1]);   // 행 중앙값 — 곡선이 지나가도 영향 적음
    }
    const rows = [];
    for (let i = 3; i < lum.length - 3; i++) {
      const around = (lum[i - 3] + lum[i + 3]) / 2;
      if (Math.abs(lum[i] - around) >= 4 &&
          Math.abs(lum[i] - around) >= Math.abs(lum[i - 1] - around) &&
          Math.abs(lum[i] - around) >= Math.abs(lum[i + 1] - around)) rows.push(i + y0);
    }
    if (rows.length < 3) return null;
    const diffs = [];
    for (let i = 1; i < rows.length; i++) if (rows[i] - rows[i - 1] > 8) diffs.push(rows[i] - rows[i - 1]);
    if (diffs.length < 2) return null;
    // 우세 간격: 서로 ±3px 안에 가장 많이 모이는 값의 평균
    let best = null, bestN = 0;
    for (const d of diffs) {
      const near = diffs.filter(v => Math.abs(v - d) <= 3);
      if (near.length > bestN) { bestN = near.length; best = near.reduce((a, b) => a + b, 0) / near.length; }
    }
    return bestN >= 2 ? best : null;
  }

  /* 곡선 아래쪽 행들에서 fill 색이 가장 길게 이어지는 구간 [시작x, 끝x]. 여러 행의 중앙값. */
  function fillSpan(img, color, yFrom) {
    const spans = [];
    const rowsStep = Math.max(1, Math.floor((img.height - yFrom) / 12));
    for (let y = yFrom + 4; y < img.height; y += rowsStep) {
      // 세로 점선 표시선(CC·1차 크랙 등)이 영역을 끊으므로 6px 이하 끊김은 잇는다
      let best = null, start = -1, lastOn = -1;
      for (let x = 0; x <= img.width; x++) {
        const on = x < img.width && dist(px(img, x, y), color) < 22;
        if (on) { if (start < 0) start = x; lastOn = x; continue; }
        if (start >= 0 && x - lastOn > 6) {
          if (!best || lastOn - start > best[1] - best[0]) best = [start, lastOn];
          start = -1;
        }
      }
      if (start >= 0 && (!best || lastOn - start > best[1] - best[0])) best = [start, lastOn];
      if (best && best[1] - best[0] > img.width * 0.2) spans.push(best);
    }
    if (spans.length < 2) return null;
    const med = a => a.sort((p, q) => p - q)[a.length >> 1];
    return [med(spans.map(s => s[0])), med(spans.map(s => s[1]))];
  }

  /* 시간 기준 이동평균(±halfSec) */
  function smooth(pts, halfSec) {
    const out = [];
    let lo = 0, hi = 0, sum = 0;
    for (let i = 0; i < pts.length; i++) {
      while (hi < pts.length && pts[hi].t <= pts[i].t + halfSec) sum += pts[hi++].bt;
      while (pts[lo].t < pts[i].t - halfSec) sum -= pts[lo++].bt;
      out.push({ t: pts[i].t, bt: sum / (hi - lo) });
    }
    return out;
  }

  function fitLine(pairs) {                 // y(px) → °C
    const n = pairs.length;
    const my = pairs.reduce((s, p) => s + p[0], 0) / n, mt = pairs.reduce((s, p) => s + p[1], 0) / n;
    let sxy = 0, sxx = 0;
    for (const [y, t] of pairs) { sxy += (y - my) * (t - mt); sxx += (y - my) * (y - my); }
    const a = sxx ? sxy / sxx : 0;
    return { a, b: mt - a * my };
  }

  /* 앵커 쌍으로 y→°C 직선 + 검증. 앵커가 2개면 눈금선 간격으로 기울기를 확인한다. */
  function calibrate(img, bt, xs, xd, pairs, maxResidual) {
    if (pairs.length < 2) return { ok: false, reason: '앵커 2개 미만' };
    const spread = Math.max(...pairs.map(p => p[1])) - Math.min(...pairs.map(p => p[1]));
    if (spread < 12) return { ok: false, reason: '앵커 온도 폭 부족' };
    let { a, b } = fitLine(pairs);
    if (!(a < 0)) return { ok: false, reason: '온도축 방향 이상' };
    let gridStep = null, verified = pairs.length >= 3;
    if (pairs.length < 3) {
      const ysAll = bt.map(p => p[1]);
      const pad = Math.round(img.height * 0.12);
      const g = gridSpacing(img, xs, xd, Math.max(0, Math.min(...ysAll) - pad), Math.min(img.height - 1, Math.max(...ysAll) + pad));
      if (g) {
        const raw = -a * g;
        const snap = NICE_STEPS.reduce((p, s) => Math.abs(s - raw) < Math.abs(p - raw) ? s : p, NICE_STEPS[0]);
        if (Math.abs(snap - raw) / snap < 0.1) {
          gridStep = snap; verified = true;
          a = -snap / g; b = pairs.reduce((s, [y, t]) => s + (t - a * y), 0) / pairs.length;
        }
      }
    }
    const y2T = y => a * y + b;
    const maxRes = Math.max(...pairs.map(([y, t]) => Math.abs(y2T(y) - t)));
    if (maxRes > maxResidual) return { ok: false, reason: `앵커 오차 ${maxRes.toFixed(1)}°C`, maxRes };
    return { ok: true, y2T, maxRes, gridStep, verified, pairs };
  }

  /* 본 함수 */
  function extract(img, opts) {
    const tpl = TEMPLATES[opts.screenType] || {};
    const btColor = tpl.bt || hexToRgb(opts.colors && opts.colors.bt);
    const etColor = tpl.et || hexToRgb(opts.colors && opts.colors.et);
    const tol = tpl.tol || 40;
    const maxResidual = opts.maxResidual ?? 3;
    const dropT = +opts.dropT;
    const anchors = (opts.anchorsBt || []).filter(a => a && a.t > 0 && a.t <= dropT + 1 && isFinite(a.T));
    if (!btColor) return { ok: false, reason: 'BT 색 정보 없음' };
    if (!(dropT > 0)) return { ok: false, reason: '배출 시각 없음' };
    if (anchors.length < 2) return { ok: false, reason: '앵커 2개 미만' };

    const bt = longestRun(traceColumns(img, btColor, tol));
    if (bt.length < 80) return { ok: false, reason: `BT 선 추적 실패(${bt.length}px)` };
    const xs = bt[0][0], xd = findDropX(bt);
    if (xd - xs < 60) return { ok: false, reason: '배출 지점 검출 실패' };
    // 시간축: 기본은 곡선 시작(투입)~배출. 화면에 투입~배출 구간만 칠하는 영역이 있으면
    // (이카와의 팬 영역) 그 좌우 끝을 쓴다 — 곡선 앞부분이 축 글자에 가려도 시간이 밀리지 않는다.
    let t0x = xs, dropX = xd, timeRef = 'curve';
    if (tpl.timeFill) {
      const span = fillSpan(img, tpl.timeFill, Math.round(Math.max(...bt.map(p => p[1]))));
      if (span && span[1] - span[0] > (xd - xs) * 0.8) { [t0x, dropX] = span; timeRef = 'fill'; }
    }
    const pps = (dropX - t0x) / dropT;
    const x2t = x => (x - t0x) / pps;
    const t2x = t => t0x + t * pps;

    // ET 경로를 먼저 추적 — 같은 온도축이라 ET 앵커도 축 보정에 함께 쓴다
    let et = [];
    if (etColor) {
      et = longestRun(traceColumns(img, etColor, tol, 0, img.height - 1, Math.max(0, Math.min(xs, t0x) - 2), dropX));
      if (et.length < (dropX - t0x) * 0.5) et = [];
    }
    const anchorsEt = (opts.anchorsEt || []).filter(a => a && a.t > 0 && a.t <= dropT + 1 && isFinite(a.T));

    // 앵커로 y→°C (BT·ET 앵커를 한 직선으로). ET 쪽이 어긋나면 BT 앵커만으로 다시 맞춘다.
    const btPairs = anchors.map(a => [yAt(bt, t2x(a.t)), a.T]).filter(p => p[0] != null);
    const etPairs = et.length ? anchorsEt.map(a => [yAt(et, t2x(a.t)), a.T]).filter(p => p[0] != null) : [];
    let cal = calibrate(img, bt, xs, xd, btPairs.concat(etPairs), maxResidual);
    if (!cal.ok && etPairs.length) {
      const btOnly = calibrate(img, bt, xs, xd, btPairs, maxResidual);
      if (btOnly.ok) { cal = btOnly; et = []; }       // ET 경로를 믿을 수 없으니 버린다 (AI 판독으로 대체)
    }
    if (!cal.ok) return cal;
    const { y2T, maxRes, gridStep, verified, pairs } = cal;

    // 픽셀 계단(1px ≈ 0.5~1°C)이 RoR 잔떨림·가짜 크래시 경고를 만들지 않도록 ±3초 이동평균
    const toPts = path => smooth(path.filter(([x]) => x <= dropX && x2t(x) >= -0.5)
      .map(([x, y]) => ({ t: Math.max(0, x2t(x)), bt: y2T(y) })), 3)
      .map(p => ({ t: +p.t.toFixed(1), bt: +p.bt.toFixed(1) }));
    const out = { ok: true, btPts: toPts(bt), etPts: et.length ? toPts(et) : [], agitSorted: null,
                  maxRes, gridStep, verified, anchorsUsed: pairs.length, timeRef, xs: t0x, xd: dropX };

    if (opts.screenType === 'boost_web' && tpl.agit) out.agitSorted = boostAgitation(img, tpl, t0x, dropX, x2t);
    return out;
  }

  /* Boost '열원값' 패널의 교반(초록) 레벨. 눈금선 3개(10/5/0)로 환산. 선이 전부 가려지면 null */
  function boostAgitation(img, tpl, xs, xd, x2t) {
    const ref = longestRun(traceColumns(img, tpl.heatRef, 60, 0, img.height - 1, xs, xd));
    if (ref.length < 40) return null;
    const refY = ref.reduce((s, p) => s + p[1], 0) / ref.length;
    // 열원값 패널: 진한 테두리 두 줄 사이. 그 안의 연회색 눈금선이 10(위)·5·0(아래).
    const step = Math.max(1, Math.floor((xd - xs) / 200));
    const BORDER = [138, 148, 173];          // Boost 패널 테두리(슬레이트) 색
    const bg = img._bg || (img._bg = backgroundColor(img));
    const isBorder = makeMatcher(BORDER, bg, 30);
    const rowStat = y => {
      let border = 0, light = 0, m = 0;
      for (let x = xs; x <= xd; x += step) {
        const c = px(img, x, y); m++;
        if (isBorder(c)) border++;
        // 연회색 눈금선(축소 이미지에서는 흰 배경과 섞여 더 옅어진다)
        if (Math.abs(c[0] - c[1]) < 8 && Math.abs(c[1] - c[2]) < 8 && c[0] > 200 && c[0] <= 249) light++;
      }
      return { border: border / m, light: light / m };
    };
    const yA = Math.max(0, Math.round(refY - img.height * 0.15)), yB = Math.min(img.height - 1, Math.round(refY + img.height * 0.1));
    const stats = [];
    for (let y = yA; y <= yB; y++) stats.push([y, rowStat(y)]);
    const borders = stats.filter(([, st]) => st.border > 0.6).map(([y]) => y);
    const top = Math.max(...borders.filter(y => y < refY - 2), -Infinity);
    const bot = Math.min(...borders.filter(y => y > refY + 2), Infinity);
    if (!isFinite(top) || !isFinite(bot) || bot - top < 30) return null;
    const grid = [];
    for (const [y, st] of stats) if (y > top + 1 && y < bot - 1 && st.light > 0.45) {
      if (!grid.length || y - grid[grid.length - 1] > 2) grid.push(y);
    }
    if (!grid.length) return null;
    const y0 = grid[grid.length - 1];
    const margin = bot - y0;
    let y10 = grid[0];
    if (Math.abs((y10 - top) - margin) > Math.max(4, margin * 0.4)) y10 = top + margin;   // 10 눈금이 가려진 경우
    if (y0 - y10 < 20) return null;
    const y5 = (y10 + y0) / 2;
    const green = traceColumns(img, tpl.agit, 60, Math.round(top + 1), Math.round(bot - 1), xs, xd);
    if (!green.size) return null;
    const pts = [...green.entries()].sort((p, q) => p[0] - q[0])
      .map(([x, y]) => ({ t: x2t(x), v: Math.max(0, Math.min(10, Math.round(5 + 5 * (y5 - y) / (y5 - y10)))) }));
    // 2px 이하 짧은 전환 조각 제거 후 변화 지점만 남김
    const steps = [];
    for (let i = 0; i < pts.length; i++) {
      const v = pts[i].v;
      let run = 1;
      while (i + run < pts.length && pts[i + run].v === v) run++;
      if (run >= 3 && (!steps.length || steps[steps.length - 1].v !== v)) steps.push({ t: +Math.max(0, pts[i].t).toFixed(1), v });
      i += run - 1;
    }
    if (steps.length) steps[0].t = 0;
    return steps.length ? steps : null;
  }

  return { extract, TEMPLATES, hexToRgb };
})();

if (typeof module !== 'undefined') module.exports = RoastPixel;
