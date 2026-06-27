"""
모모스커피 생두 스크래퍼
URL: https://momos.co.kr/product/list.html?cate_no=64
플랫폼: Cafe24 (서버렌더링)
"""
import re, json, time, os
import requests
from bs4 import BeautifulSoup

STORE   = '모모스커피'
BASE    = 'https://momos.co.kr'
CAT_URL = BASE + '/product/list.html?cate_no=64&page={page}'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

ORIGIN_MAP = {
    '에티오피아':'에티오피아','케냐':'케냐','탄자니아':'탄자니아','르완다':'르완다',
    '우간다':'우간다','콩고':'콩고민주공화국','브라질':'브라질','콜롬비아':'콜롬비아',
    '과테말라':'과테말라','코스타리카':'코스타리카','파나마':'파나마',
    '엘살바도르':'엘살바도르','온두라스':'온두라스','멕시코':'멕시코',
    '자메이카':'자메이카','페루':'페루','볼리비아':'볼리비아','에콰도르':'에콰도르',
    '니카라과':'니카라과','인도네시아':'인도네시아','인도':'인도',
    '베트남':'베트남','예멘':'예멘','중국':'중국','파푸아뉴기니':'파푸아뉴기니','하와이':'하와이',
    # 영문
    'Ethiopia':'에티오피아','Kenya':'케냐','Tanzania':'탄자니아','Rwanda':'르완다',
    'Uganda':'우간다','Brazil':'브라질','Colombia':'콜롬비아','Guatemala':'과테말라',
    'Costa Rica':'코스타리카','Panama':'파나마','El Salvador':'엘살바도르',
    'Honduras':'온두라스','Mexico':'멕시코','Jamaica':'자메이카','Peru':'페루',
    'Bolivia':'볼리비아','Ecuador':'에콰도르','Nicaragua':'니카라과',
    'Indonesia':'인도네시아','India':'인도','Vietnam':'베트남','Yemen':'예멘',
    'China':'중국','Papua New Guinea':'파푸아뉴기니','Hawaii':'하와이',
}
REGION_MAP = {
    '에티오피아':'아프리카','케냐':'아프리카','탄자니아':'아프리카','르완다':'아프리카',
    '우간다':'아프리카','콩고민주공화국':'아프리카',
    '브라질':'중남미','콜롬비아':'중남미','과테말라':'중남미','코스타리카':'중남미',
    '파나마':'중남미','엘살바도르':'중남미','온두라스':'중남미','멕시코':'중남미',
    '자메이카':'중남미','페루':'중남미','볼리비아':'중남미','에콰도르':'중남미','니카라과':'중남미',
    '인도네시아':'아시아/태평양','인도':'아시아/태평양','베트남':'아시아/태평양',
    '예멘':'아시아/태평양','중국':'아시아/태평양','파푸아뉴기니':'아시아/태평양','하와이':'아시아/태평양',
}

def guess_origin(name):
    for k, v in ORIGIN_MAP.items():
        if k in name:
            return v, REGION_MAP.get(v, '기타')
    return '알수없음', '기타'

def guess_process(name):
    n = name.lower()
    if any(x in n for x in ['anaerobic', '무산소', '카보닉', 'carbonic', 'infused', '인퓨즈드']): return '무산소발효'
    if any(x in n for x in ['honey', '허니', 'red honey', 'yellow honey', 'white honey']): return '허니'
    if any(x in n for x in ['pulped natural', 'pulped', '펄프드']): return '펄프드내추럴'
    if any(x in n for x in ['natural', '내추럴', 'reposado', '레포사도']): return '내추럴'
    if any(x in n for x in ['washed', 'fully washed', '워시드', 'wet process']): return '워시드'
    if any(x in n for x in ['wet hulled', 'wet hul', '웻훌']): return '웻훌드'
    return '알수없음'

def fetch(url, session):
    r = session.get(url, timeout=15)
    r.raise_for_status()
    return r.text

def is_soldout_block(el):
    """품절 감지 — 이미지 오버레이만 신뢰 (CSS 클래스는 숨겨진 템플릿 버튼도 매칭되어 오탐 발생)"""
    if el is None: return False
    if el.select_one('img[alt*="품절"], img[alt*="SOLD OUT"], img[src*="soldout"], img[src*="sold_out"]'): return True
    return False


def check_detail_soldout(url, session):
    """상품 상세 페이지 JSON 데이터에서 품절 여부 확인"""
    try:
        r = session.get(url, timeout=10)
        html = r.text
        # Cafe24 상품 데이터 JSON: "soldout_yn":"Y" 패턴만 확인
        # 클래스/버튼 기반 감지는 display:none 숨겨진 요소로 인한 오탐 발생
        if re.search(r'"soldout_yn"\s*:\s*"Y"', html): return True
        if re.search(r"'soldout_yn'\s*:\s*'Y'", html): return True
    except Exception:
        pass
    return False

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []

    # prdList__item 안에 상품명([생두] 포함)과 가격이 있음
    for card in soup.select('li.xans-record- div.prdList__item, li.xans-record- div.custom-prdList__item'):
        # 상품명
        name_el = card.select_one('.description a[href*="/product/"]')
        if not name_el:
            name_el = card.select_one('a[href*="/product/"][title]')
        if not name_el:
            # 상품명 텍스트 직접 찾기
            desc = card.select_one('.description')
            if desc:
                a_tags = desc.select('a[href*="/product/"]')
                name_el = a_tags[0] if a_tags else None

        if not name_el:
            continue

        name = name_el.get('title') or name_el.get_text(strip=True)
        # [생두] 태그가 있는 것만 (원두/드립백 제외)
        if not ('[생두]' in name or 'green' in name.lower()):
            continue
        # "상품명:" 레이블 및 [생두] 접두어 제거
        name = re.sub(r'^상품명:\s*', '', name).strip()
        name = re.sub(r'^\[생두\]\s*', '', name).strip()

        href = name_el.get('href', '')
        url = BASE + href if href.startswith('/') else href

        # 품절 감지 — img overlay만 신뢰 (li 전체 검색)
        li_el = card.find_parent('li')
        soldout = is_soldout_block(card) or is_soldout_block(li_el)

        # 가격
        price = 0
        for span in card.select('span'):
            m = re.search(r'([\d,]+)원', span.get_text())
            if m:
                price = int(m.group(1).replace(',', ''))
                break

        if not name: continue
        if not price and not soldout: continue

        items.append({'name': name, 'price': price, 'url': url, 'is_soldout': soldout})
    return items

def get_total_pages(html):
    pages = re.findall(r'page=(\d+)', html)
    return max((int(p) for p in pages), default=1)

def scrape():
    print(f"[{STORE}] 스크래핑 시작...")
    session = requests.Session()
    session.headers.update(HEADERS)

    all_items = []
    page = 1
    total_pages = None

    while True:
        url = CAT_URL.format(page=page)
        print(f"  페이지 {page}: {url}")
        try:
            html = fetch(url, session)
        except Exception as e:
            print(f"  ❌ 오류: {e}")
            break

        if total_pages is None:
            total_pages = get_total_pages(html)
            print(f"  총 {total_pages}페이지")

        items = parse_page(html)
        if not items and page > 1:
            print(f"  ⚠️ 상품 없음 — 종료")
            break

        all_items.extend(items)
        print(f"  → {len(items)}개 생두")

        if page >= total_pages:
            break
        page += 1
        time.sleep(1.0)

    # 중복 제거 (URL 기준)
    seen, unique = set(), []
    for i in all_items:
        if i['url'] not in seen:
            seen.add(i['url'])
            unique.append(i)

    # 목록 페이지에서 품절 감지 못한 경우 상세 페이지 fallback 확인
    not_detected = [it for it in unique if not it['is_soldout']]
    print(f"[{STORE}] 상세 페이지 품절 확인: {len(not_detected)}개...")
    soldout_count = sum(1 for it in unique if it['is_soldout'])
    for it in not_detected:
        if check_detail_soldout(it['url'], session):
            it['is_soldout'] = True
            soldout_count += 1
        time.sleep(0.3)

    print(f"[{STORE}] 총 {len(unique)}개 수집 (품절 {soldout_count}개)")
    return unique

def to_products(items, id_start):
    results = []
    for i, item in enumerate(items):
        origin, region = guess_origin(item['name'])
        name = item['name']
        results.append({
            "id":         id_start + i,
            "store":      STORE,
            "name":       name,
            "price":      item['price'],
            "origin":     origin,
            "region":     region,
            "process":    guess_process(name),
            "notes":      "",
            "url":        item['url'],
            "is_new":     any(x in name for x in ['2026', '25/26', '2025/26', '2025/2026']),
            "is_decaf":   '디카페인' in name.lower() or 'decaf' in name.lower(),
            "is_special": any(x in name for x in ['게이샤','Geisha','파카마라','Pacamara','에스메랄다']) or item['price'] >= 50000,
            "is_soldout": item.get('is_soldout', False),
        })
    return results

if __name__ == '__main__':
    items = scrape()

    root = os.path.join(os.path.dirname(__file__), '..')
    json_path = os.path.join(root, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    kept = [p for p in data['products'] if p['store'] != STORE]
    existing_ids = {p['id'] for p in kept}

    # 모모스 ID 범위: 101~250
    id_start = 101
    while id_start in existing_ids:
        id_start += 1

    new_products = to_products(items, id_start)

    # 안전장치: 스크래핑 일시 실패로 빈/부분 결과면 기존 데이터 보존
    old_count = sum(1 for p in data['products'] if p['store'] == STORE)
    new_count = len(new_products)
    if new_count == 0 and old_count > 0:
        print(f"⚠️  {STORE}: 0개 수집됨 — 스크래핑 실패로 판단, 기존 {old_count}개 보존")
        raise SystemExit(1)
    if old_count >= 10 and new_count < old_count * 0.5:
        print(f"⚠️  {STORE}: {old_count}개 → {new_count}개로 급감 — 부분 실패 의심, 기존 데이터 보존")
        raise SystemExit(1)

    data['products'] = kept + new_products

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ products.json 업데이트: {STORE} {new_count}개 (이전 {old_count}개)")
