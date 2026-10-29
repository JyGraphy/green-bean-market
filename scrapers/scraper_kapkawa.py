"""
캅카와(kapkawa.com) 생두 스크래퍼 — cafe24

    python3 scrapers/scraper_kapkawa.py --dry-run   # 저장 없이 실사만
    python3 scrapers/scraper_kapkawa.py             # 수집 후 저장

**아직 등록 전이다.** 사장님 컨펌 전까지 `run_all.py` 에 넣지 않는다.
(CLAUDE.md: 새 공급사는 보고 → 컨펌 → 추가 순서)

플랫폼: cafe24. 목록 `/product/list.html?cate_no=25`, 상세 `/product/<슬러그>/<번호>/`.
`/category/생두/25/` 는 같은 목록의 사용자용 주소다.

**용량 정규화가 이 쇼핑몰의 핵심 문제다.**
캅카와는 같은 생두를 1kg / 5kg / 10kg 세 개 상품으로 따로 올린다. 그대로 넣으면
같은 콩이 우리 사이트에 3번 뜨고 가격 비교가 깨진다. 우리 스키마의 price 는
**1kg 기준**이므로, 같은 콩은 하나로 합치고 **kg당 단가**로 환산한다.
1kg 상품이 있으면 그 가격을 그대로 쓴다(가장 비교 가능한 값).
"""
import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (HEADERS, abs_url, clean_name, guess_process, is_non_bean,
                    to_products, update_json)

import requests
from bs4 import BeautifulSoup

STORE = '캅카와'
BASE = 'https://kapkawa.com'
LIST = BASE + '/product/list.html?cate_no=25&page={page}'
ID_START = 1400          # alloc_ids 가 충돌은 알아서 피한다
MAX_PAGES = 20

KG = re.compile(r'(\d+(?:\.\d+)?)\s*kg\b', re.I)
G = re.compile(r'(\d{3,4})\s*g\b', re.I)
NEWCROP = re.compile(r'\[\s*(\d{2})\s*new\s*crop\s*\]', re.I)
# 상품명이 "캅카와 에티오피아 ... 생두커피 1kg" 꼴이라 접두/접미를 떼야 읽힌다
PREFIX = re.compile(r'^\s*캅카와\s*')
SUFFIX = re.compile(r'\s*생두\s*커피\s*$')


def pack_kg(name: str) -> float | None:
    """상품명에서 포장 단위를 kg 로 읽는다. 못 읽으면 None."""
    m = KG.search(name)
    if m:
        return float(m.group(1))
    m = G.search(name)
    if m:
        return int(m.group(1)) / 1000
    return None


def parse_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for li in soup.select('li[id^="anchorBoxId_"], .xans-product-listnormal li, ul.prdList > li'):
        a = li.select_one('a[href*="/product/"]')
        if not a:
            continue
        nm_el = li.select_one('.name span:last-of-type, .name a, .description .name')
        name = (nm_el.get_text(' ', strip=True) if nm_el else a.get_text(' ', strip=True))
        name = re.sub(r'^\s*상품명\s*[:：]\s*', '', name).strip()
        if len(name) < 4:
            continue
        txt = li.get_text(' ', strip=True)
        m = re.search(r'([\d,]{4,})\s*원', txt)
        if not m:
            continue
        price = int(m.group(1).replace(',', ''))
        if price < 1000:
            continue
        items.append({'raw_name': name, 'raw_price': price,
                      'url': abs_url(BASE, a.get('href', ''))})
    return items


def fetch_all(session) -> list[dict]:
    out, seen = [], set()
    for page in range(1, MAX_PAGES + 1):
        try:
            r = session.get(LIST.format(page=page), timeout=30)
            r.raise_for_status()
        except requests.RequestException as e:
            print(f'  페이지 {page} 실패: {type(e).__name__}: {e}')
            break
        got = parse_list(r.text)
        fresh = [g for g in got if g['url'] not in seen]
        print(f'  페이지 {page}: {len(got)}개 (신규 {len(fresh)}개)')
        if not fresh:
            break
        seen.update(g['url'] for g in fresh)
        out.extend(fresh)
        time.sleep(0.8)
    return out


def bean_key(name: str) -> str:
    """용량을 뺀 '같은 콩' 식별자. 1kg/5kg/10kg 중복을 묶는 데 쓴다."""
    s = NEWCROP.sub('', name)
    s = KG.sub('', s)
    s = G.sub('', s)
    s = PREFIX.sub('', s)
    s = SUFFIX.sub('', s)
    return re.sub(r'[\s·,\-]+', '', s).lower()


def normalize(raw: list[dict]) -> tuple[list[dict], dict]:
    """용량별 중복을 합치고 kg당 단가로 환산한다. (상품목록, 실사통계)."""
    stat = {'raw': len(raw), 'no_kg': 0, 'non_bean': 0, 'packs': defaultdict(int)}
    groups: dict[str, list[dict]] = defaultdict(list)

    for it in raw:
        nm = it['raw_name']
        if is_non_bean(nm):
            stat['non_bean'] += 1
            continue
        kg = pack_kg(nm)
        if kg is None:
            stat['no_kg'] += 1
            kg = 1.0                      # 표기 없으면 1kg 으로 본다(대부분 1kg)
        stat['packs'][f'{kg:g}kg'] += 1
        it = dict(it, kg=kg, per_kg=round(it['raw_price'] / kg))
        groups[bean_key(nm)].append(it)

    products = []
    for key, variants in groups.items():
        # 1kg 상품이 있으면 그것을 대표로 (가장 비교 가능한 값)
        variants.sort(key=lambda v: (abs(v['kg'] - 1.0), v['kg']))
        rep = variants[0]
        # 순서가 중요하다 — 대괄호 태그를 먼저 떼야 '캅카와' 접두어가 문장 앞에 온다.
        # (안 그러면 "[26 New Crop] 캅카와 …" 상품만 접두어가 남아 이름이 들쭉날쭉해진다)
        nm = NEWCROP.sub('', rep['raw_name'])
        nm = re.sub(r'^\s*\[[^\]]*\]\s*', '', nm)
        nm = PREFIX.sub('', nm.lstrip())
        nm = KG.sub('', nm)
        nm = G.sub('', nm)
        nm = SUFFIX.sub('', nm).strip(' ·,-')
        nm = clean_name(re.sub(r'\s{2,}', ' ', nm))
        crop = NEWCROP.search(rep['raw_name'])
        products.append({
            'name': nm,
            'price': rep['per_kg'],
            'url': rep['url'],
            'isNew': bool(crop and int(crop.group(1)) >= 26),
            '_kg': rep['kg'],
            '_variants': len(variants),
            '_raw': rep['raw_name'],
        })
    stat['grouped'] = len(products)
    stat['packs'] = dict(stat['packs'])
    return products, stat


def report(products: list[dict], stat: dict) -> None:
    print('\n' + '=' * 60)
    print(f'실사 — {STORE}')
    print('=' * 60)
    print(f"목록에서 수집     : {stat['raw']}개")
    print(f"비생두 제외       : {stat['non_bean']}개")
    print(f"용량 표기 없음    : {stat['no_kg']}개 (1kg 으로 간주)")
    print(f"포장 단위 분포    : {stat['packs']}")
    print(f"**같은 콩으로 합친 뒤: {stat['grouped']}개**")
    if not products:
        return
    prices = sorted(p['price'] for p in products)
    n = len(prices)
    print(f"\nkg당 단가 — 최저 {prices[0]:,}원 / 중앙 {prices[n//2]:,}원 / "
          f"최고 {prices[-1]:,}원")
    print(f"26 뉴크롭 표기    : {sum(1 for p in products if p['isNew'])}개")
    multi = [p for p in products if p['_variants'] > 1]
    # f-string 안에 따옴표를 중첩하지 않는다(파이썬 3.11 에서 SyntaxError)
    sample = ', '.join('{}×{}'.format(p['name'][:24], p['_variants'])
                       for p in multi[:3])
    print(f"용량 여러 개인 콩 : {len(multi)}개 (예: {sample})")

    proc = defaultdict(int)
    for p in products:
        proc[guess_process(p['name'])] += 1
    print(f"가공방식 분포     : {dict(proc)}")

    print('\n--- 정규화 결과 표본 (사람이 눈으로 확인) ---')
    for p in sorted(products, key=lambda x: -x['price'])[:12]:
        print(f"  {p['price']:>7,}원/kg  [{p['_kg']:g}kg×{p['_variants']}]  "
              f"{p['name'][:46]}")
    print('\n--- 원본 상품명 표본 ---')
    for p in products[:5]:
        print(f"  {p['_raw'][:70]}")


def scrape(dry: bool = False):
    print(f'[{STORE}] 수집 시작...')
    s = requests.Session()
    s.headers.update(HEADERS)
    raw = fetch_all(s)
    products, stat = normalize(raw)
    report(products, stat)
    if dry:
        print('\n🧪 드라이런 — 저장하지 않았습니다.')
        out = os.path.join(os.path.dirname(__file__), '..', 'vault', 'raw', 'stores')
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, f'{time.strftime("%Y-%m-%d")}-캅카와-실사.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'store': STORE, 'fetched_at': time.strftime('%Y-%m-%d'),
                       'stat': stat, 'products': products},
                      f, ensure_ascii=False, indent=2)
        print(f'   실사 결과 → vault/raw/stores/{os.path.basename(path)}')
    return products


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    items = scrape(dry=a.dry_run)
    if a.dry_run:
        sys.exit(0 if items else 1)

    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    existing_ids = {p['id'] for p in data['products'] if p['store'] != STORE}
    # 내부용 필드(_kg 등)는 스키마에 없으므로 떼고 넘긴다
    clean = [{k: v for k, v in p.items() if not k.startswith('_')} for p in items]
    products = to_products(clean, STORE, ID_START, existing_ids)
    update_json(STORE, products)
