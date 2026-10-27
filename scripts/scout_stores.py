#!/usr/bin/env python3
"""
신규 생두 공급사 후보 조사 — 취급 품목과 **크롭(수확연도) 표기**를 본다.

    python3 scripts/scout_stores.py --audit-existing     # 우리 데이터 전수조사 (네트워크 불필요)
    python3 scripts/scout_stores.py --candidates         # 후보 사이트 실제 조사 (네트워크 필요)

사장님 기준: "좋은 퀄리티의 생두가 있는지 보고, **올드크롭이 있으면 안 된다**".
그래서 이 스크립트의 핵심은 상품 수가 아니라 **크롭 표기 분포**다.

판정 규칙(2026년 기준 — `CROP_NOW` 로 매년 갱신):
    뉴크롭   26 / 2026 / 2025-26 / "뉴크롭" / "New Crop"
    지난크롭  25 / 2025 / 2024-25            → 노란불
    올드크롭  24 이하 / "올드크롭" / "패스트크롭" → 빨간불 (사장님 기준 탈락)

⚠️ **표기가 없는 상품이 대부분이다.** 우리 데이터 1,348개 중 크롭을 적은 것은
약 11%뿐이었다(2026-10-27 실측). 그래서 "올드크롭 0건"은 **"올드크롭이 없다"가
아니라 "올드크롭이라고 적힌 게 없다"** 는 뜻이다. 이 구분을 보고서에 명시한다.
표기율 자체가 공급사의 투명성 지표라서 함께 보고한다.
"""
import argparse
import json
import pathlib
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'scrapers'))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'vault' / 'raw' / 'stores'

CROP_NOW = 26          # 현재 뉴크롭 연도 두 자리 — 해마다 올린다

# ── 크롭 표기 판정 ───────────────────────────────────────────────
OLD_WORD = re.compile(r'(올드\s*크롭|old\s*crop|past\s*crop|패스트\s*크롭|지난\s*크롭)', re.I)
# 연도는 **크롭 문맥 안에 있을 때만** 센다.
# 2026-10-27 실측: 문맥 없이 연도만 잡았더니 푸터의 저작권 연도(ⓒ2020·2023)와
# 통신판매업 신고연도를 전부 '올드크롭'으로 읽었다 — "회사소개"·"과일청" 페이지까지
# 올드크롭으로 찍혔다. 그래서 '크롭/crop/수확/harvest' 가 연도 근처에 있어야 한다.
# 재현율은 떨어지지만(연도만 적는 곳은 놓친다), **멀쩡한 공급사를 탈락시키는 쪽이
# 훨씬 큰 손해**라 정밀도를 택한다.
_CW = r'(?:크롭|crop|수확|harvest|하베스트)'
YEAR = re.compile(
    # 크롭 단어와 연도 사이에 '시기:', '연도 :' 같은 말이 끼는 경우가 있어
    # 숫자 아닌 문자 8자까지 허용한다("수확시기: 2024-2025").
    rf'{_CW}[^0-9]{{0,8}}(?:20)?(\d{{2}})(?:\s*[/~\-]\s*(?:20)?(\d{{2}}))?'
    rf'|(?:20)?(\d{{2}})(?:\s*[/~\-]\s*(?:20)?(\d{{2}}))?[^0-9]{{0,4}}{_CW}', re.I)
NEW_WORD = re.compile(r'(뉴\s*크롭|new\s*crop)', re.I)


def crop_verdict(text: str) -> tuple[str, str]:
    """(판정, 근거). 판정 = new | past | old | none."""
    if OLD_WORD.search(text):
        return 'old', OLD_WORD.search(text).group(0)
    years = []
    for m in YEAR.finditer(text):
        for g in m.groups():
            if g and 18 <= int(g) <= CROP_NOW + 1:  # 터무니없는 숫자 제외
                years.append(int(g))
    if years:
        # 범위 표기(2024/25)는 **뒷 연도**가 실제 수확이므로 최대값을 본다
        y = max(years)
        ev = f'{2000 + y}'
        if y >= CROP_NOW:
            return 'new', ev
        if y == CROP_NOW - 1:
            return 'past', ev
        return 'old', ev
    if NEW_WORD.search(text):
        return 'new', NEW_WORD.search(text).group(0)
    return 'none', ''


def classify(names: list[str]) -> dict:
    out = {'n': len(names), 'new': 0, 'past': 0, 'old': 0, 'none': 0,
           'old_items': [], 'past_items': [],
           # 긁은 것이 진짜 상품명인지 사람이 확인할 표본. 사진 수집에서
           # "검색어만 믿으면 바나나가 온다"를 겪었다 — 같은 실수를 막는다.
           'samples': [n[:70] for n in names[:12]]}
    for nm in names:
        v, ev = crop_verdict(nm)
        out[v] += 1
        if v == 'old':
            out['old_items'].append(f'{nm[:70]}  ({ev})')
        elif v == 'past':
            out['past_items'].append(f'{nm[:70]}  ({ev})')
    labeled = out['n'] - out['none']
    out['label_rate'] = labeled / out['n'] if out['n'] else 0
    return out


# ── 우리 데이터 전수조사 (네트워크 불필요) ────────────────────────
def audit_existing() -> int:
    data = json.loads((ROOT / 'data' / 'products.json').read_text(encoding='utf-8'))
    by = defaultdict(list)
    for p in data['products']:
        by[p['store']].append(f"{p.get('name','')} {p.get('notes') or ''}")

    rows = []
    for store, names in by.items():
        r = classify(names)
        r['store'] = store
        rows.append(r)
    rows.sort(key=lambda r: (-r['old'], -r['past'], -r['n']))

    print(f"{'공급사':14s} {'상품':>5s} {'뉴':>4s} {'지난':>4s} {'올드':>4s} {'표기율':>6s}")
    print('-' * 46)
    for r in rows:
        print(f"{r['store']:14s} {r['n']:5d} {r['new']:4d} {r['past']:4d} "
              f"{r['old']:4d} {r['label_rate']:5.0%}")
    write_report(rows, '우리 데이터 전수조사', 'audit')
    return 0


# ── 후보 사이트 조사 (네트워크 필요 → Actions) ────────────────────
# URL 은 실재 확인된 것만 적는다. 추측한 주소는 404 가 나고 조사가 한 주 밀린다.
CANDIDATES = [
    {'name': '카브로시아', 'domain': 'cabrosia.com',
     'urls': ['https://cabrosia.com/'],
     'note': '원산지 직수입 도소매 · 스페셜티/마이크로랏/이파네마 · 생두마대특가'},
    {'name': '소펙스코리아', 'domain': 'sopexkorea.com',
     'urls': ['https://sopexkorea.com/product/list.html?cate_no=69'],
     'note': '벨기에 모기업 · 뉴크롭 전용 카테고리 운영'},
    {'name': '캅카와', 'domain': 'kapkawa.com',
     'urls': ['https://kapkawa.com/category/생두/25/'],
     'note': '탄자니아·케냐 산지 보유 · 직거래 · 상품명에 [26 New Crop] 표기'},
    {'name': '에센티아팩토리', 'domain': 'essentiaroastery.com',
     'urls': ['https://essentiaroastery.com/category/생두/57'],
     'note': '에티오피아·콜롬비아·브라질·예멘'},
    {'name': '커피명가', 'domain': 'myungga.com',
     'urls': ['https://myungga.com/category/마이크로랏/50/'],
     'note': '마이크로랏 · 생두 도매/직수입 안내'},
    {'name': '커피시스', 'domain': 'cgbeans.com',
     'urls': ['https://cgbeans.com/'],
     'note': '기존 조사 완료(47개) — 사장님 컨펌 대기 중'},
]

NAME_SELECTORS = [
    '.prdName', '.name a', '.item_name', '.prd_name', '.goods_name',
    'li .description .name', '.xans-product-listnormal .name',
    'a[href*="product_no"]', 'a[href*="goods_view"]', 'a[href*="/product/"]',
]


def scrape_names(session, urls: list[str]) -> tuple[list[str], str, list[str]]:
    """상품명과 상세페이지 링크를 긁는다. 플랫폼이 제각각이라 여러 셀렉터를 시도한다."""
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    names, how, links = [], '', []
    for url in urls:
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
        except Exception as e:                       # noqa: BLE001
            print(f'    ✗ {url} — {type(e).__name__}: {e}')
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        for a in soup.select('a[href*="product_no"], a[href*="goods_view"], '
                             'a[href*="/product/"]'):
            href = a.get('href') or ''
            if href and 'javascript' not in href:
                links.append(urljoin(url, href))
        for sel in NAME_SELECTORS:
            got = [el.get_text(' ', strip=True) for el in soup.select(sel)]
            got = [g for g in got if 6 <= len(g) <= 120]
            if len(got) >= 5:
                names += got
                how = sel
                break
        time.sleep(1.0)
    # 중복 제거(순서 유지)
    seen, uniq = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    seen2, ulinks = set(), []
    for l in links:
        if l not in seen2:
            seen2.add(l)
            ulinks.append(l)
    return uniq, how, ulinks


# 크롭 연도는 목록 페이지 상품명이 아니라 **상세페이지**(요약정보·상세설명)에
# 적히는 경우가 대부분이다(2026-10-27 실측: 목록 기준 표기율 0~8%).
# 그래서 상세페이지를 표본으로 열어 본문 전체에서 크롭 표기를 찾는다.
DETAIL_SAMPLE = 10


def scan_details(session, links: list[str]) -> dict:
    import re as _re
    from bs4 import BeautifulSoup
    res = {'checked': 0, 'new': 0, 'past': 0, 'old': 0, 'none': 0, 'hits': []}
    for url in links[:DETAIL_SAMPLE]:
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
        except Exception:                            # noqa: BLE001
            continue
        soup = BeautifulSoup(r.text, 'html.parser')
        for t in soup(['script', 'style']):
            t.decompose()
        text = _re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))[:20000]
        title = (soup.title.get_text(strip=True) if soup.title else url)[:60]
        v, ev = crop_verdict(text)
        res['checked'] += 1
        res[v] += 1
        if v in ('old', 'past', 'new'):
            # 적중 문구의 앞뒤를 같이 남긴다 — 오탐인지 사람이 바로 판단할 수 있게
            ctx = ''
            m = _re.search(r'.{0,45}' + _re.escape(ev) + r'.{0,45}', text)
            if m:
                ctx = m.group(0).strip()
            res['hits'].append(f'{v.upper()} {ev} — {title} … 「{ctx}」')
        time.sleep(1.0)
    return res


def scout() -> int:
    import requests
    from common import HEADERS

    session = requests.Session()
    session.headers.update(HEADERS)

    rows = []
    for c in CANDIDATES:
        print(f"\n▶ {c['name']} ({c['domain']})")
        names, how, links = scrape_names(session, c['urls'])
        if not names:
            print('    상품명을 못 긁음 — 클라이언트 렌더링이거나 차단')
            rows.append({'store': c['name'], 'domain': c['domain'], 'note': c['note'],
                         'n': 0, 'new': 0, 'past': 0, 'old': 0, 'none': 0,
                         'label_rate': 0, 'old_items': [], 'past_items': [],
                         'how': '수집 실패'})
            continue
        r = classify(names)
        r.update(store=c['name'], domain=c['domain'], note=c['note'], how=how)
        print(f'    상세페이지 표본 {min(len(links), DETAIL_SAMPLE)}개 확인 중…')
        r['detail'] = scan_details(session, links)
        rows.append(r)
        print(f"    상품명 {r['n']}개 · 뉴 {r['new']} / 지난 {r['past']} / "
              f"올드 {r['old']} · 표기율 {r['label_rate']:.0%}")
        for s in r['old_items'][:5]:
            print(f'      🔴 {s}')

    write_report(rows, '신규 공급사 후보 조사', 'scout')
    return 0


def write_report(rows: list[dict], title: str, kind: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = time.strftime('%Y-%m-%d')
    L = [f'# {title} — 크롭(수확연도) 표기 기준', '',
         f'**작성일**: {today} · **담당**: `scripts/scout_stores.py` (자동·토큰 0)', '',
         '> 판정 기준 — 뉴크롭 `26/2026/2025-26` · 지난크롭 `25/2025/2024-25` · '
         '올드크롭 `24 이하 / 올드크롭 / 패스트크롭`',
         '>',
         '> ⚠️ **"올드 0건" ≠ "올드크롭이 없다".** 상품명에 크롭을 적지 않는 곳이 많다. '
         '0건은 *올드크롭이라고 적힌 게 없다*는 뜻이고, **표기율**을 함께 봐야 한다. '
         '표기율이 낮으면 판정 자체가 불가능하다.', '',
         '| 공급사 | 상품명 | 뉴 | 지난 | 올드 | 표기율 | 판정 |', '|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda x: (-x['old'], -x['past'], -x['n'])):
        if r['n'] == 0:
            verdict = '⚪ 조사 실패'
        elif r['old']:
            verdict = '🔴 올드크롭 있음'
        elif r['label_rate'] < 0.15:
            verdict = '⚪ 판정 불가(표기율 낮음)'
        elif r['past']:
            verdict = '🟡 지난크롭 있음'
        else:
            verdict = '🟢 올드 표기 없음'
        L.append(f"| {r['store']} | {r['n']} | {r['new']} | {r['past']} | {r['old']} | "
                 f"{r['label_rate']:.0%} | {verdict} |")
    L += ['', '## 상세페이지 크롭 표본 조사', '',
          '목록 페이지 상품명에는 크롭이 거의 안 적힌다. 상세페이지 본문을 표본으로 열어 확인했다.', '',
          '| 공급사 | 확인 | 뉴 | 지난 | 올드 | 표기 없음 |', '|---|---|---|---|---|---|']
    for r in rows:
        d = r.get('detail') or {}
        if d.get('checked'):
            L.append(f"| {r['store']} | {d['checked']} | {d['new']} | {d['past']} | "
                     f"{d['old']} | {d['none']} |")
    for r in rows:
        d = r.get('detail') or {}
        if d.get('hits'):
            L += ['', f"**{r['store']}** 상세페이지 적중"]
            for h in d['hits']:
                L.append(f'- {h}')

    L += ['', '## 긁어온 상품명 표본 (스크래퍼가 제대로 읽었는지 사람이 확인)', '']
    for r in rows:
        L.append(f"**{r['store']}** — {r.get('how', '')} · {r['n']}개")
        if r.get('samples'):
            for s0 in r['samples']:
                L.append(f'- {s0}')
        else:
            L.append('- (없음)')
        L.append('')
    for r in rows:
        if r['old_items'] or r['past_items']:
            L += ['', f"### {r['store']}"]
            for s in r['old_items']:
                L.append(f'- 🔴 {s}')
            for s in r['past_items'][:10]:
                L.append(f'- 🟡 {s}')
    (OUT_DIR / f'{today}-{kind}-크롭조사.md').write_text('\n'.join(L) + '\n',
                                                        encoding='utf-8')
    print(f"\n📝 vault/raw/stores/{today}-{kind}-크롭조사.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--audit-existing', action='store_true')
    ap.add_argument('--candidates', action='store_true')
    a = ap.parse_args()
    if a.audit_existing:
        return audit_existing()
    if a.candidates:
        return scout()
    ap.error('--audit-existing 또는 --candidates 중 하나를 쓰세요.')


if __name__ == '__main__':
    sys.exit(main())
