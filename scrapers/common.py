"""공통 유틸리티: ORIGIN_MAP, REGION_MAP, guess_origin, guess_process, fetch, to_products"""
import re, json, os
import requests
from urllib.parse import urljoin


def abs_url(base, href):
    """상품 링크를 항상 절대 URL로 변환.

    href가 '../goods/...', '/goods/...', 'goods_view.php?...' 등 상대경로여도
    base 기준으로 절대화한다. 상대경로 그대로 저장되면 우리 사이트 도메인으로
    해석되어(예: green-bean-market.vercel.app/goods/...) 403이 난다 — 이를 방지.
    """
    return urljoin(base, (href or '').strip())

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
    '세인트헬레나':'세인트헬레나',
    # 커만사 등에서 등장하는 추가 산지 / 오타 보정
    '동티모르':'동티모르','East Timor':'동티모르','Timor':'동티모르','티모르':'동티모르',
    '태국':'태국','Thailand':'태국','치앙라이':'태국','치앙마이':'태국',
    '라오스':'라오스','Laos':'라오스','미얀마':'미얀마','Myanmar':'미얀마',
    '르와다':'르완다','르완':'르완다',  # '르완다' 오타 보정 (앞 항목보다 뒤에 와도 무방)
    # 영문
    'Ethiopia':'에티오피아','Kenya':'케냐','Tanzania':'탄자니아','Rwanda':'르완다',
    'Uganda':'우간다','Congo':'콩고민주공화국','Brazil':'브라질','Colombia':'콜롬비아',
    'Guatemala':'과테말라','Costa Rica':'코스타리카','Panama':'파나마',
    'El Salvador':'엘살바도르','Honduras':'온두라스','Mexico':'멕시코',
    'Jamaica':'자메이카','Peru':'페루','Bolivia':'볼리비아','Ecuador':'에콰도르',
    'Nicaragua':'니카라과','Indonesia':'인도네시아','India':'인도',
    'Vietnam':'베트남','Yemen':'예멘','China':'중국',
    'Papua New Guinea':'파푸아뉴기니','Hawaii':'하와이',
}
REGION_MAP = {
    '에티오피아':'아프리카','케냐':'아프리카','탄자니아':'아프리카','르완다':'아프리카',
    '우간다':'아프리카','콩고민주공화국':'아프리카','세인트헬레나':'아프리카',
    '브라질':'중남미','콜롬비아':'중남미','과테말라':'중남미','코스타리카':'중남미',
    '파나마':'중남미','엘살바도르':'중남미','온두라스':'중남미','멕시코':'중남미',
    '자메이카':'중남미','페루':'중남미','볼리비아':'중남미','에콰도르':'중남미','니카라과':'중남미',
    '인도네시아':'아시아/태평양','인도':'아시아/태평양','베트남':'아시아/태평양',
    '예멘':'아시아/태평양','중국':'아시아/태평양','파푸아뉴기니':'아시아/태평양','하와이':'아시아/태평양',
    '동티모르':'아시아/태평양','태국':'아시아/태평양','라오스':'아시아/태평양','미얀마':'아시아/태평양',
}

def guess_origin(name):
    for k, v in ORIGIN_MAP.items():
        if k in name:
            return v, REGION_MAP.get(v, '기타')
    return '알수없음', '기타'

def is_soldout_block(el):
    """품절 감지 — 썸네일 위 품절 이미지 오버레이만 신뢰.
    주의: div.soldout / [class*=soldout] / 전체 텍스트 검색은 신뢰 불가.
      - Cafe24: 숨겨진 btnSoldout 템플릿이 모든 상품에 존재
      - godomall/Wisa(코빈즈 등): <div class="soldout">가 전 상품에 템플릿으로 출력됨
      (실측: 코빈즈 전 카테고리에서 상품 100%가 div.soldout 보유 → 템플릿 확정)
    따라서 품절만 렌더되는 이미지 오버레이(alt/src)만 사용한다."""
    if el is None:
        return False
    if el.select_one('img[alt*="품절"], img[alt*="SOLD OUT"], img[alt*="Sold out"], '
                     'img[src*="soldout"], img[src*="sold_out"], img[src*="icon_soldout"]'):
        return True
    return False

# 이름 앞에 붙는 상태 라벨 대괄호 (내용 어디든 키워드 포함 시 제거)
_NAME_LABELS = re.compile(
    r'^\s*\[[^\]]*(?:품절|재입고|예약|예정|품절임박|일시품절|SOLD ?OUT|NEW|BEST|MD)[^\]]*\]\s*', re.I)
# 품절/재고없음을 의미하는 접두어
# 주의: '재입고'(=재입고 완료, 재고 있음)와 '재입고 예정'(=현재 품절)은 다름 → '예정'이 함께 있을 때만 품절
_SOLDOUT_LABEL = re.compile(
    r'^\s*\[[^\]]*(?:품절|일시품절|SOLD ?OUT|재고없음|재입고[^\]]*예정|입고예정)[^\]]*\]', re.I)

def clean_name(name):
    """상품명 정제: '상품명:' 레이블, 상태 접두어, 'N kg 외 N종' 꼬리, 가격·배지 꼬리 제거"""
    if not name:
        return name
    name = re.sub(r'^\s*상품명\s*:\s*', '', name)
    # 선행 상태 라벨 반복 제거
    prev = None
    while prev != name:
        prev = name
        name = _NAME_LABELS.sub('', name)
    # imweb 등: 끝에 붙은 "12,300원 NEW" / "38,800원BESTMD" 가격+배지 꼬리 제거
    name = re.sub(r'\s*[\d,]{3,}원\s*(?:NEW|BEST|MD|품절|SOLD ?OUT|\s)*$', '', name, flags=re.I)
    # "외 24종" 묶음 상품 꼬리 제거
    name = re.sub(r'\s*외\s*\d+\s*종.*$', '', name)
    return name.strip()

def name_is_soldout(name):
    """상품명 접두어가 [품절] 류이면 True"""
    return bool(_SOLDOUT_LABEL.search(name or ''))


# 비생두 품목 차단 패턴 — 장비/도구/서적/굿즈/결제/식품 등.
# 모두 실전 데이터 전수 검증으로 정상 생두명과 충돌 0건 확인된 정밀 패턴만 포함.
# (주의: '컵','잔','세트','스틱' 등은 정상 생두명에도 흔히 등장해 사용 금지)
_NON_BEAN_PATTERNS = [
    '커핑스푼', '커핑 스푼', 'cupping spoon', '커핑보울', '커핑 보울', 'cupping bowl', '커핑볼',
    '컨테이너박스', '캐니스터', '보관용기',
    '샘플 튜브', '샘플튜브', '데스크 패드', '그레이딩 데스크', 'grading desk',
    'handbook', 'glossary', '매거진', 'magazine',
    '커피 퀄리티 part', '업체결제', '카다이프', '커피지도',
    '샘플 패키지', '샘플패키지',
    '그라인더', 'grinder', '드리퍼', 'dripper', '저울', '케틀', 'kettle',
    '텀블러', '머그컵', '에코백', '티셔츠', '스티커', '앞치마',
]

def is_non_bean(name):
    """생두가 아닌 품목(장비·서적·굿즈·결제 등)이거나 이름이 깨졌으면 True → 수집 제외."""
    if not name or not name.strip():
        return True
    # 상태 텍스트만 캡처된 깨진 이름 (예: GSC 'SOLD OUT') — 기호/공백 제거 후 판별
    stripped = re.sub(r'[\s\W_]+', '', name).lower()
    if stripped in ('soldout', '품절', 'sold', ''):
        return True
    low = name.lower()
    return any(pat.lower() in low for pat in _NON_BEAN_PATTERNS)


def guess_process(name):
    n = name.lower()
    if any(x in n for x in ['anaerobic','무산소','카보닉','carbonic','infused','인퓨즈드']): return '무산소발효'
    if any(x in n for x in ['honey','허니','레드허니','화이트허니','옐로우허니','yellow honey','red honey','white honey']): return '허니'
    if any(x in n for x in ['pulped natural','pulped','펄프드']): return '펄프드내추럴'
    if any(x in n for x in ['natural','내추럴','reposado','레포사도']): return '내추럴'
    if any(x in n for x in ['washed','fully washed','워시드']): return '워시드'
    if any(x in n for x in ['wet hulled','wet hul','웻훌']): return '웻훌드'
    return '알수없음'

def new_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def fetch(url, session=None):
    s = session or new_session()
    r = s.get(url, timeout=15)
    r.raise_for_status()
    return r.text

def get_total_pages(html):
    nums = re.findall(r'[?&]page=(\d+)', html)
    return max((int(n) for n in nums), default=1)

def alloc_ids(count, id_start, taken=None):
    """taken(이미 사용 중인 ID 집합)과 겹치지 않는 ID를 count개 순서대로 발급.

    기존엔 id_start+i 를 순차 부여해, 다른 store가 그 구간을 점유하면 ID가
    충돌(중복)했다. 이 함수는 점유된 ID를 건너뛰어 항상 고유 ID를 보장한다.
    """
    taken = set(taken or ())
    ids, nid = [], id_start
    for _ in range(count):
        while nid in taken:
            nid += 1
        ids.append(nid)
        taken.add(nid)
        nid += 1
    return ids


def to_products(items, store, id_start, taken=None):
    # 비생두 품목 제외 (정제된 이름 기준)
    items = [it for it in items if not is_non_bean(clean_name(it['name']))]
    results = []
    ids = alloc_ids(len(items), id_start, taken)
    for i, item in enumerate(items):
        raw = item['name']
        # 상품명 접두어가 [품절]이면 품절로 표시 후 정제
        soldout = item.get('is_soldout', False) or name_is_soldout(raw)
        name = clean_name(raw)
        origin, region = guess_origin(name)
        results.append({
            "id":         ids[i],
            "store":      store,
            "name":       name,
            "price":      item['price'],
            "origin":     origin,
            "region":     region,
            "process":    guess_process(name),
            "notes":      item.get('notes', ''),
            "url":        item['url'],
            "is_new":     any(x in name for x in ['2026','25/26','2025/26','2025/2026','-26CROP-']),
            "is_decaf":   '디카페인' in name or 'decaf' in name.lower(),
            "is_special": any(x in name for x in ['게이샤','Geisha','파카마라','Pacamara','에스메랄다']) or item['price'] >= 50000,
            "is_soldout": soldout,
        })
    return results

# 스크래핑 부분 실패 판정 임계값 (기존 대비 이 비율 미만이면 보존)
SUSPICIOUS_DROP_RATIO = 0.5
SUSPICIOUS_MIN_BASELINE = 10  # 기존이 이 개수 이상일 때만 급감 검사

def guard_store_replacement(store, old_count, new_count):
    """store 교체 전 안전성 검사 (단일 진실 공급원).

    스크래핑 일시 실패로 빈/부분 결과가 넘어오면 기존 데이터를 덮어쓰지 않도록
    SystemExit(1)을 던진다. 모든 저장 경로(common.update_json 및 자체 저장
    스크래퍼)는 반드시 이 함수를 거쳐야 한다.
    """
    # 1) 결과가 비었는데 기존 데이터가 있으면 = 스크래핑 실패로 간주 → 보존
    if new_count == 0 and old_count > 0:
        print(f"⚠️  {store}: 0개 수집됨 — 스크래핑 실패로 판단, 기존 {old_count}개 보존 (덮어쓰기 생략)")
        raise SystemExit(1)
    # 2) 기존이 충분히 많았는데 절반 미만으로 급감 = 부분 실패 의심 → 보존
    if old_count >= SUSPICIOUS_MIN_BASELINE and new_count < old_count * SUSPICIOUS_DROP_RATIO:
        print(f"⚠️  {store}: {old_count}개 → {new_count}개로 급감 — 부분 실패 의심, 기존 데이터 보존 (덮어쓰기 생략)")
        raise SystemExit(1)


def update_json(store, new_products):
    """해당 store의 상품을 새 목록으로 교체.

    안전장치: guard_store_replacement()가 빈/부분 결과를 막아 기존 데이터를 보존한다.
    """
    root = os.path.join(os.path.dirname(__file__), '..')
    json_path = os.path.join(root, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    old_count = sum(1 for p in data['products'] if p['store'] == store)
    new_count = len(new_products)

    guard_store_replacement(store, old_count, new_count)

    kept = [p for p in data['products'] if p['store'] != store]
    data['products'] = kept + new_products
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {store}: {new_count}개 저장완료" + (f" (이전 {old_count}개)" if old_count else ""))
