"""로스팅 AI 누적 학습 — 공통 모듈.

학습 자료는 공개 GitHub 저장소가 아니라 Supabase Storage 비공개 버킷 `roast-learning` 에 쌓인다.
  seed/       2026-10 세션에서 옮긴 초기 자료 (Firescope 곡선·특징값, Boost 기록·상세 곡선, 판독 검증 사례)
  readings/   사이트에서 분석할 때마다 roast-learn 함수가 남기는 기록 (+ 동의한 경우 사진)
  corpus/     주간 동기화가 쌓는 새 원천 데이터 (Boost 신규 로스팅 등)
공개 저장소에는 집계값(기준값 백분위·정확도 추이)만 커밋한다.

환경변수: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (GitHub Actions 시크릿)
로컬 시험: Store(local_dir=...) 로 같은 구조의 폴더를 버킷 대신 쓴다.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import pathlib
import urllib.error
import urllib.parse
import urllib.request

BUCKET = 'roast-learning'


class Store:
    """비공개 버킷(또는 같은 구조의 로컬 폴더) 읽기·쓰기."""

    def __init__(self, local_dir: str | None = None):
        self.local = pathlib.Path(local_dir) if local_dir else None
        self.url = os.environ.get('SUPABASE_URL', '').rstrip('/')
        self.key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
        if not self.local and not (self.url and self.key):
            raise SystemExit('SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY 가 없습니다 (또는 --local 폴더 지정).')

    def _req(self, method, path, data=None, headers=None):
        h = {'Authorization': f'Bearer {self.key}', 'apikey': self.key}
        h.update(headers or {})
        req = urllib.request.Request(f'{self.url}/storage/v1/{path}', data=data, method=method, headers=h)
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.read()

    def list(self, prefix: str) -> list[str]:
        """prefix 아래 모든 파일 경로(재귀)."""
        if self.local:
            base = self.local / prefix
            if not base.exists():
                return []
            return sorted(str(p.relative_to(self.local)) for p in base.rglob('*') if p.is_file())
        out, stack = [], [prefix.rstrip('/')]
        while stack:
            pre = stack.pop()
            offset = 0
            while True:
                body = json.dumps({'prefix': pre, 'limit': 1000, 'offset': offset,
                                   'sortBy': {'column': 'name', 'order': 'asc'}}).encode()
                try:
                    items = json.loads(self._req('POST', f'object/list/{BUCKET}', body,
                                                 {'Content-Type': 'application/json'}))
                except urllib.error.HTTPError:
                    items = []
                for it in items:
                    full = f"{pre}/{it['name']}" if pre else it['name']
                    if it.get('id') is None:      # 폴더
                        stack.append(full)
                    else:
                        out.append(full)
                if len(items) < 1000:
                    break
                offset += 1000
        return sorted(out)

    def get(self, path: str) -> bytes:
        if self.local:
            return (self.local / path).read_bytes()
        return self._req('GET', f'object/{BUCKET}/{urllib.parse.quote(path)}')

    def get_json(self, path: str):
        raw = self.get(path)
        if path.endswith('.gz'):
            raw = gzip.decompress(raw)
        return json.loads(raw.decode('utf-8'))

    def get_text(self, path: str) -> str:
        raw = self.get(path)
        if path.endswith('.gz'):
            raw = gzip.decompress(raw)
        return raw.decode('utf-8-sig')

    def put(self, path: str, data: bytes, content_type='application/json'):
        if self.local:
            p = self.local / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            return
        self._req('POST', f'object/{BUCKET}/{urllib.parse.quote(path)}', data,
                  {'Content-Type': content_type, 'x-upsert': 'true'})


# ── 곡선 특징값 (roasting.js 의 curveShape·computeRoR 와 같은 정의) ─────────────

def interp(pts, t):
    if not pts:
        return None
    if t <= pts[0][0]:
        return pts[0][1]
    if t >= pts[-1][0]:
        return pts[-1][1]
    lo, hi = 0, len(pts) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if pts[m][0] <= t:
            lo = m
        else:
            hi = m
    (a, va), (b, vb) = pts[lo], pts[hi]
    return va if b == a else va + (vb - va) * (t - a) / (b - a)


def resample5(pts, end_t):
    ts = [i * 5 for i in range(int(end_t // 5) + 1)]
    return ts, [interp(pts, t) for t in ts]


def ror30(ts, vals):
    out = []
    for i, t in enumerate(ts):
        if i == 0:
            out.append(None)
            continue
        k = i
        while k > 0 and t - ts[k] < 30:
            k -= 1
        dt = t - ts[k]
        out.append((vals[i] - vals[k]) / dt * 60 if dt > 0 else None)
    return out


def curve_features(bt, dur, et=None, tp_on='bt'):
    """bt/et: [(t, °C)] 정렬. 반환: total·tpT·tpBt·dry·mai·ror200·dtr200(200°C 도달 이후 비율)."""
    if not bt or len(bt) < 10 or not dur or dur < 120:
        return None
    ts, b = resample5(bt, dur)
    src = b
    if tp_on == 'et' and et and len(et) >= 10:
        src = resample5(et, dur)[1]
    early = [i for i, t in enumerate(ts) if t <= 150]
    if not early:
        return None
    tp = min(early, key=lambda i: src[i])
    start = tp if src is b else 0

    def reach(th):
        for i in range(start, len(b)):
            if b[i] >= th:
                return i
        return None
    i150, i200 = reach(150), reach(200)
    r = ror30(ts, b)
    f = {'total': dur / 60, 'tpT': ts[tp], 'tpBt': src[tp]}
    if i150 is not None:
        f['dry'] = ts[i150] / dur * 100
    if i150 is not None and i200 is not None:
        f['mai'] = (ts[i200] - ts[i150]) / dur * 100
    if i200 is not None:
        f['dtr200'] = (dur - ts[i200]) / dur * 100
        if r[i200] is not None:
            f['ror200'] = r[i200]
    return f


def group_for(machine: str | None, charge_g, fluid_bed=False) -> str:
    """roasting.js pickBaseline 과 같은 분류."""
    if fluid_bed or (machine or '').upper() == 'IKAWA':
        return 'ikawa'
    if machine and any(k in machine.lower() for k in ('s7x', 'stronghold', '스트롱')):
        return 's7x'
    try:
        w = float(charge_g)
    except (TypeError, ValueError):
        w = None
    if w and w <= 300:
        return 'drumSmall'
    if w and w >= 800:
        return 'drumLarge'
    return 'drum'


def detail_id(path: str) -> str:
    """Boost 상세 곡선 파일명 → 기록 ID.  …/4409_20261008173925489939.json(.gz) → 20261008173925489939"""
    return pathlib.Path(path).name.split('.', 1)[0].split('_', 1)[1]


def percentile(vals, p):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    k = (len(v) - 1) * p
    a = int(k)
    b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)


def gz_lines(raw: bytes):
    return gzip.decompress(raw).decode('utf-8-sig').splitlines()


def tar_members(raw: bytes):
    import tarfile
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as tf:
        for m in tf.getmembers():
            if m.isfile():
                yield m.name, tf.extractfile(m).read()
