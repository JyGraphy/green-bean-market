#!/usr/bin/env python3
"""로스팅 AI 누적 학습 ② — Stronghold Boost 신규 로스팅 동기화.

지난번까지 받은 기록(seed + corpus) 이후의 새 로스팅만 받아 비공개 버킷에 쌓는다.
  corpus/boost/list/<날짜>.json                새 기록 메타 (총 시간·배출 온도·DTR …)
  corpus/boost/details/<기기>_<기록ID>.json.gz  상세 곡선 (1초 단위 IR·내부 온도, 교반 …)
roast_baselines.py 가 이 자료를 seed 와 합쳐 S7X 기준선을 다시 계산한다.

환경변수: BOOST_ID, BOOST_PW (GitHub 시크릿). 없으면 아무것도 하지 않고 정상 종료한다.
         SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (버킷 쓰기)

사용법:
    python3 scripts/roast_corpus_sync.py [--max-details 400] [--local DIR]
"""
from __future__ import annotations

import argparse
import datetime
import gzip
import http.cookiejar
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from roast_learning_lib import Store, detail_id  # noqa: E402

BASE = 'https://boost.stronghold.coffee'
PAGE = 200


class Boost:
    def __init__(self, user, pw):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [('User-Agent', 'Mozilla/5.0 (green-bean-market roast-learning)'),
                              ('X-Requested-With', 'XMLHttpRequest')]
        r = self._call('POST', '/acct/login/get.sq',
                       {'userId': user, 'userPwd': pw, 'timeZone': 'Asia/Seoul'})
        if r.get('resultCd') != 'COMM_0000':
            raise SystemExit(f'Boost 로그인 실패: {r.get("resultCd")}')

    def _call(self, method, path, params):
        q = urllib.parse.urlencode(params)
        if method == 'GET':
            req = urllib.request.Request(f'{BASE}{path}{"&" if "?" in path else "?"}{q}')
        else:
            req = urllib.request.Request(f'{BASE}{path}', data=q.encode(), method='POST',
                                         headers={'Content-Type': 'application/x-www-form-urlencoded'})
        for attempt in range(3):
            try:
                with self.op.open(req, timeout=60) as r:
                    return json.loads(r.read().decode('utf-8'))
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt * 2)

    def machines(self):
        r = self._call('GET', '/rstry/profile/status/all/list.sq?rc=w0', {})
        return [(m['prodCd'], (m.get('prodNickName') or '').replace(' ', ''), m.get('totalPrflCnt') or 0)
                for m in r.get('status') or []]

    def page(self, prod, page):
        r = self._call('GET', '/rstry/profile/status/list.sq?rc=w0',
                       {'prodCd': prod, 'page': page, 'pageSetCnt': PAGE, 'minRstTime': 0, 'maxRstTime': 36000})
        return r.get('profiles') or []

    def detail(self, prod, cd):
        return self._call('GET', '/rstry/profile/detail/get.sq', {'prodCd': prod, 'prflMCd': cd, 'rc': 'w0'})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-details', type=int, default=400, help='한 번에 받을 상세 곡선 최대 수')
    ap.add_argument('--local', help='버킷 대신 쓸 로컬 폴더')
    args = ap.parse_args()
    user, pw = os.environ.get('BOOST_ID'), os.environ.get('BOOST_PW')
    if not (user and pw):
        print('ℹ️ BOOST_ID / BOOST_PW 시크릿이 없어 Boost 동기화를 건너뜁니다.')
        return
    store = Store(args.local)

    known = {r['prflMCd'] for r in store.get_json('seed/boost/all_profiles.json.gz')}
    synced = []                       # 지난 동기화로 받은 메타 — 상세를 못 받은 것은 이어서 받는다
    for p in store.list('corpus/boost/list'):
        synced += store.get_json(p)
    known |= {r['prflMCd'] for r in synced}
    have_detail = {detail_id(p) for p in store.list('corpus/boost/details')}
    print(f'기존 기록 {len(known)}건 (동기화분 {len(synced)}건, 상세 {len(have_detail)}건)')

    bo = Boost(user, pw)
    new = []
    for prod, nick, total in bo.machines():
        got = 0
        for page in range(1, total // PAGE + 2):
            rows = bo.page(prod, page)
            fresh = [r for r in rows if r['prflMCd'] not in known]
            for r in fresh:
                r['_machine'] = nick
                r['_prodCd'] = prod
            new += fresh
            got += len(fresh)
            if len(fresh) < len(rows) or not rows:   # 최신순이므로 아는 기록이 나오면 그 뒤는 다 받은 것
                break
            time.sleep(0.5)
        print(f'  · {nick}({prod}) 새 기록 {got}건')
    if new:
        name = f'corpus/boost/list/{datetime.datetime.now().strftime("%Y-%m-%dT%H%M")}.json'
        store.put(name, json.dumps(new, ensure_ascii=False).encode('utf-8'))
        print(f'✓ {name} ({len(new)}건)')

    todo = [r for r in new + synced
            if r['prflMCd'] not in have_detail and r.get('_prodCd') and (r.get('totalRstTime') or 0) > 0]
    ok = 0
    for r in todo[:args.max_details]:
        try:
            d = bo.detail(r['_prodCd'], r['prflMCd'])
        except Exception as e:  # noqa: BLE001
            print(f'  ⚠️ 상세 실패 {r["prflMCd"]}: {e}')
            continue
        if d.get('resultCd') != 'COMM_0000':
            continue
        store.put(f'corpus/boost/details/{r["_prodCd"]}_{r["prflMCd"]}.json.gz',
                  gzip.compress(json.dumps(d, ensure_ascii=False).encode('utf-8')), 'application/gzip')
        ok += 1
        time.sleep(0.3)
    print(f'✓ 상세 곡선 {ok}건 저장 (대기 {max(0, len(todo) - args.max_details)}건은 다음 실행에서)')


if __name__ == '__main__':
    main()
