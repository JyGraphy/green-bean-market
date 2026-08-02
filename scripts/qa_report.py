#!/usr/bin/env python3
"""검수부서 자동화 — LLM 토큰 0으로 QA 보고서를 생성한다.

data-validator / scraper-checker 가 하던 '기계적으로 판정 가능한' 검사를 전부 대신한다.
결과는 REPORT-FORMAT 규격의 마크다운으로 저장되어 현황판 보고서함에 그대로 뜬다.

사용법:
    python3 scripts/qa_report.py            # 보고서 생성
    python3 scripts/qa_report.py --check    # 생성 없이 문제 유무만 (문제 있으면 exit 1)

AI 에이전트는 이 스크립트가 ⚠️/❌ 를 뱉었을 때만 부르면 된다.
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'products.json'
DAILY = ROOT / 'vault' / 'raw' / 'qa'

PROC_CLS = {
    '펄프드내추럴', '무산소발효', '허니', '웻훌드', '내추럴', '워시드', '디카페인', '알수없음',
}
REQUIRED = ['id', 'store', 'name', 'price', 'origin', 'region', 'url']
PRICE_MIN, PRICE_MAX = 5_000, 900_000     # 1kg 환산 상식 범위(원)
NEW_HINTS = ('2026', '-26CROP-', '2025/26', '2025/2026')
SPECIAL_HINTS = ('게이샤', 'geisha', 'gesha', '파카마라', 'pacamara', '에스메랄다', 'sl28', 'sl34')


def load():
    d = json.loads(DATA.read_text(encoding='utf-8'))
    return d['products'] if isinstance(d, dict) else d


# ─────────────────────────── 데이터 검증 ───────────────────────────
def check_data(P):
    """(항목명, 상태, 상세) 리스트와 문제 상품 dict 를 돌려준다."""
    rows, detail = [], {}

    missing = [p for p in P if any(f not in p or p[f] in (None, '') for f in REQUIRED)]
    rows.append(('필수 필드', '✅' if not missing else '❌', f'누락 {len(missing)}건'))
    detail['필수 필드 누락'] = missing

    ids = Counter(p['id'] for p in P)
    dup = [i for i, c in ids.items() if c > 1]
    rows.append(('중복 ID', '✅' if not dup else '❌', f'{len(dup)}건' + (f' {dup[:5]}' if dup else '')))

    bad_url = [p for p in P if not str(p.get('url', '')).startswith(('http://', 'https://'))]
    rows.append(('절대경로 URL', '✅' if not bad_url else '❌', f'상대경로 {len(bad_url)}건'))
    detail['상대경로 URL'] = bad_url

    ours = [p for p in P if 'green-bean-market' in str(p.get('url', ''))]
    rows.append(('자기도메인 오염', '✅' if not ours else '❌', f'{len(ours)}건'))
    detail['우리 도메인을 가리키는 url'] = ours

    badproc = [p for p in P if p.get('process') and p['process'] not in PROC_CLS]
    rows.append(('가공방식 값', '✅' if not badproc else '❌',
                 f'미정의 {len(badproc)}건' + (f' {sorted({p["process"] for p in badproc})[:4]}' if badproc else '')))

    outlier = [p for p in P if not isinstance(p.get('price'), (int, float))
               or not (PRICE_MIN <= p['price'] <= PRICE_MAX)]
    rows.append(('가격 이상치', '✅' if not outlier else '⚠️',
                 f'{len(outlier)}건 (기준 {PRICE_MIN:,}~{PRICE_MAX:,}원)'))
    detail[f'가격 이상치 (1kg 기준 {PRICE_MIN:,}~{PRICE_MAX:,}원 밖)'] = outlier

    unknown_origin = [p for p in P if p.get('origin') in (None, '', '알수없음')]
    rows.append(('원산지 미상', '✅' if not unknown_origin else '⚠️', f'{len(unknown_origin)}건'))

    miss_new = [p for p in P if not p.get('is_new')
                and any(h.lower() in p['name'].lower() for h in NEW_HINTS)]
    rows.append(('isNew 일관성', '✅' if not miss_new else '⚠️', f'의심 {len(miss_new)}건'))
    detail['상품명에 신작 표기가 있으나 is_new=false'] = miss_new

    miss_sp = [p for p in P if not p.get('is_special')
               and any(h in (p['name'] + ' ' + str(p.get('notes', ''))).lower() for h in SPECIAL_HINTS)]
    rows.append(('isSpecial 일관성', '✅' if not miss_sp else '⚠️', f'의심 {len(miss_sp)}건'))
    detail['희귀 품종명이 있으나 is_special=false'] = miss_sp

    dirty = [p for p in P if re.search(r'\d{1,3},\d{3}\s*원|\d+%|SALE|SOLD ?OUT|\[재입고\]', p['name'], re.I)]
    rows.append(('상품명 오염', '✅' if not dirty else '⚠️', f'{len(dirty)}건 (가격·배지 혼입)'))
    detail['상품명에 가격·할인율·배지가 섞임'] = dirty

    return rows, detail


def store_table(P):
    by = defaultdict(list)
    for p in P:
        by[p['store']].append(p)
    out = []
    for s, items in sorted(by.items(), key=lambda kv: -len(kv[1])):
        prices = [p['price'] for p in items if isinstance(p.get('price'), (int, float))]
        unk = sum(1 for p in items if p.get('origin') in (None, '', '알수없음'))
        out.append((s, len(items),
                    f'{min(prices):,}' if prices else '-',
                    f'{max(prices):,}' if prices else '-',
                    f'{round(sum(prices)/len(prices)):,}' if prices else '-',
                    unk))
    return out


# ─────────────────────────── 스크래퍼 규칙 점검 ───────────────────────────
# common.to_products() 는 내부에서 alloc_ids·clean_name·is_non_bean·guess_process 를,
# common.update_json() 은 guard_store_replacement 를 이미 수행한다(common.py 확인).
# naver_smartstore.save() 는 그 둘을 대신 호출한다.
# 따라서 이 래퍼를 쓰면 해당 규칙은 충족으로 본다 — 이 매핑이 오탐을 없애는 핵심이다.
COVERED_BY = {
    'guard':    r'guard_store_replacement|update_json\s*\(|(?:^|\W)save\s*\(',
    'ID발급':    r'alloc_ids\s*\(|to_products\s*\(|(?:^|\W)save\s*\(',
    '절대URL':   r'abs_url\s*\(|(?:^|\W)save\s*\(',
    '가공방식':  r'guess_process|to_products\s*\(|(?:^|\W)save\s*\(',
}
FORBIDDEN = [(r'id_start\s*\+\s*i\b|START_ID\s*\+\s*i\b', '순차 ID 부여(금지 패턴)')]


def check_scrapers():
    rows, viol = [], []
    files = sorted(list((ROOT / 'scrapers').glob('scraper_*.py')))
    for f in files:
        src = f.read_text(encoding='utf-8', errors='ignore')
        cells = ['✅' if re.search(pat, src) else '⚠️' for pat in COVERED_BY.values()]
        for pat, why in FORBIDDEN:
            for n, line in enumerate(src.splitlines(), 1):
                if re.search(pat, line):
                    viol.append((f'scrapers/{f.name}', n, line.strip(), why))
        rows.append((f.name, *cells, '✅' if all(c == '✅' for c in cells) else '⚠️'))

    for f in sorted((ROOT / 'scripts').glob('*.js')):
        src = f.read_text(encoding='utf-8', errors='ignore')
        for pat, why in FORBIDDEN:
            for n, line in enumerate(src.splitlines(), 1):
                if re.search(pat, line):
                    viol.append((f'scripts/{f.name}', n, line.strip(), why))
    return rows, viol


def check_docs_drift(P):
    """CLAUDE.md 기재값과 실제 데이터의 차이."""
    md = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
    stores = {p['store'] for p in P}
    out = []
    m = re.search(r'총\s*([\d,]+)개\s*상품', md)
    if m:
        doc_n = int(m.group(1).replace(',', ''))
        if doc_n != len(P):
            out.append(('총 상품 수', f'{doc_n:,}개', f'{len(P):,}개'))
    m = re.search(r'ID\s*범위\s*(\d+)~(\d+)', md)
    if m:
        real_max = max(p['id'] for p in P)
        if int(m.group(2)) != real_max:
            out.append(('ID 범위 상한', m.group(2), str(real_max)))
    m = re.search(r'(\d+)개\s*공급사', md)
    if m and int(m.group(1)) != len(stores):
        out.append(('공급사 수', f'{m.group(1)}개', f'{len(stores)}개'))
    undocumented = sorted(s for s in stores if s not in md)
    if undocumented:
        out.append(('문서에 없는 공급사', '—', ', '.join(undocumented)))
    return out


# ─────────────────────────── 보고서 작성 ───────────────────────────
def grade(rows):
    if any(s == '❌' for _, s, _ in rows):
        return '❌ 문제 있음'
    if any(s == '⚠️' for _, s, _ in rows):
        return '⚠️ 주의'
    return '✅ 정상'


def sample_table(items, n=10):
    if not items:
        return '_해당 없음_\n'
    head = '| id | 공급사 | 상품명 | 값 |\n|---|---|---|---|\n'
    body = ''.join(
        f'| {p.get("id")} | {p.get("store")} | {str(p.get("name",""))[:52]} | {p.get("price","")} |\n'
        for p in items[:n])
    more = f'\n_외 {len(items)-n}건_\n' if len(items) > n else ''
    return head + body + more


def write_data_report(P, rows, detail, today):
    bad = [r for r in rows if r[1] != '✅']
    drift = check_docs_drift(P)
    L = [
        '# 생두 데이터 검증 리포트',
        '',
        f'**작성일**: {today} · **담당**: qa_report.py (자동·토큰 0) · **신뢰도**: 상 (로컬 데이터 직접 검사)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. 총 **{len(P):,}개** 상품 / **{len({p["store"] for p in P})}개** 공급사 · 종합 판정 **{grade(rows)}**',
        f'2. 치명 항목(필수필드·중복ID·URL·가공방식): '
        f'**{"이상 없음" if not [r for r in rows[:5] if r[1]=="❌"] else "문제 발견"}**',
        f'3. 주의 항목 {len([r for r in rows if r[1]=="⚠️"])}종 · 문서 불일치 {len(drift)}건',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
    ]
    L.append('- [ ] CLAUDE.md 기재값 갱신 (아래 문서 불일치 표 참조)' if drift else '- 없음')
    L += ['', '## 검사 결과', '', '| 항목 | 상태 | 상세 |', '|---|---|---|']
    L += [f'| {k} | {s} | {d} |' for k, s, d in rows]

    L += ['', '## 공급사별 현황', '',
          '| 공급사 | 상품 수 | 최저가 | 최고가 | 평균가 | 원산지 미상 |', '|---|---|---|---|---|---|']
    L += [f'| {s} | {n} | {lo} | {hi} | {avg} | {unk} |' for s, n, lo, hi, avg, unk in store_table(P)]

    if drift:
        L += ['', '## ⚠️ CLAUDE.md 문서 불일치', '',
              '새 스크래퍼 작성자가 낡은 값을 참고하면 중복 ID 사고로 이어질 수 있습니다.', '',
              '| 항목 | 문서 기재 | 실제 |', '|---|---|---|']
        L += [f'| {a} | {b} | {c} |' for a, b, c in drift]

    if bad:
        L += ['', '## 상세 — 확인이 필요한 항목', '']
        for title, items in detail.items():
            if items:
                L += [f'### {title} ({len(items)}건)', '', sample_table(items)]

    L += ['', '## 출처', '',
          '- `data/products.json` — 1차 (로컬 데이터 직접 검사)',
          '- `CLAUDE.md` — 1차 (문서 대조)', '']
    (DAILY / f'{today}-데이터검증.md').write_text('\n'.join(L), encoding='utf-8')


def write_scraper_report(rows, viol, today):
    warn = [r for r in rows if r[-1] != '✅']
    L = [
        '# 스크래퍼 안전장치 점검',
        '',
        f'**작성일**: {today} · **담당**: qa_report.py (자동·토큰 0) · **신뢰도**: 상 (소스 직접 검사)',
        '',
        '## 📌 결론 3줄',
        '',
        f'1. 스크래퍼 **{len(rows)}개** 점검 · 금지 패턴 위반 **{len(viol)}건**',
        f'2. 규칙 미검출(주의) 스크래퍼 **{len(warn)}개**',
        '3. 이 점검은 정규식 기반입니다 — ⚠️ 표시가 곧 위반은 아니며, 사람/AI 확인이 필요합니다',
        '',
        '## ⏳ 사장님 결정 필요',
        '',
        ('- [ ] 아래 금지 패턴 위반 수정' if viol else '- 없음'),
        '',
        '## 규칙 준수 현황',
        '',
        '| 스크래퍼 | guard | ID발급 | 절대URL | 가공방식 | 판정 |',
        '|---|---|---|---|---|---|',
    ]
    L += ['| ' + ' | '.join(r) + ' |' for r in rows]

    if viol:
        L += ['', '## ❌ 금지 패턴 위반', '', '| 파일 | 줄 | 코드 | 사유 |', '|---|---|---|---|']
        L += [f'| {f} | {n} | `{c[:60]}` | {w} |' for f, n, c, w in viol]

    L += ['', '## 출처', '', '- `scrapers/*.py`, `scripts/*.js` — 1차 (소스 직접 검사)',
          '- `CLAUDE.md` 데이터 안전장치 규칙 — 1차', '']
    (DAILY / f'{today}-스크래퍼점검.md').write_text('\n'.join(L), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='보고서를 쓰지 않고 문제 유무만 판정')
    a = ap.parse_args()

    P = load()
    rows, detail = check_data(P)
    srows, viol = check_scrapers()
    today = datetime.date.today().isoformat()

    crit = [r for r in rows if r[1] == '❌'] + ([('금지패턴', '❌', str(len(viol)))] if viol else [])
    warn = [r for r in rows if r[1] == '⚠️']

    if a.check:
        print(f'데이터 {len(P):,}개 · 치명 {len(crit)}건 · 주의 {len(warn)}건 · 금지패턴 {len(viol)}건')
        sys.exit(1 if crit else 0)

    DAILY.mkdir(parents=True, exist_ok=True)
    write_data_report(P, rows, detail, today)
    write_scraper_report(srows, viol, today)
    print(f'✓ 보고서 2건 생성 (토큰 0) — 치명 {len(crit)}건 · 주의 {len(warn)}건 · 금지패턴 {len(viol)}건')
    if crit or viol:
        print('  → AI 검수 필요: data-validator / scraper-checker 호출 권장')
    else:
        print('  → 이상 없음: AI 호출 불필요')


if __name__ == '__main__':
    main()
