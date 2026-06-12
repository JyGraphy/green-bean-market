"""공통 유틸리티: ORIGIN_MAP, REGION_MAP, guess_origin, guess_process, fetch, to_products"""
import re, json, os
import requests

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
}

def guess_origin(name):
    for k, v in ORIGIN_MAP.items():
        if k in name:
            return v, REGION_MAP.get(v, '기타')
    return '알수없음', '기타'

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

def to_products(items, store, id_start):
    results = []
    for i, item in enumerate(items):
        origin, region = guess_origin(item['name'])
        name = item['name']
        results.append({
            "id":         id_start + i,
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
        })
    return results

def update_json(store, new_products):
    root = os.path.join(os.path.dirname(__file__), '..')
    json_path = os.path.join(root, 'data', 'products.json')
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    kept = [p for p in data['products'] if p['store'] != store]
    data['products'] = kept + new_products
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ {store}: {len(new_products)}개 저장완료")
