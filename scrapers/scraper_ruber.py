"""루베르 로스터리 생두 스크래퍼 — 네이버 스마트스토어 (smartstore.naver.com/ruberroastery)

'생두' 진열 카테고리만 수집한다 (원두·드립백 등 다른 카테고리 제외).

매일 자동 갱신(run_all.py)에 포함되어 있다. 단 네이버는 데이터센터 IP를
차단하는 경우가 많아, CI에서 차단(429/로그인 월) 감지 시 기존 데이터를
보존하고 스킵(정상 종료)한다 — 잡을 실패로 만들지 않는다.

초기 수집이나 차단 시 보강은 가정용 IP의 로컬 PC에서:

    pip install requests
    python scrapers/scraper_ruber.py
    python scripts/generate_sql.py   # 파생 파일 재생성
"""
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from naver_smartstore import NaverBlocked, fetch_products, save

STORE = '루베르로스터리'
STORE_ID = 'ruberroastery'
ID_START = 950

# 생두 진열 카테고리 후보 (사용자 제공 링크에서 확보한 두 ID — 첫 번째부터 시도)
CATEGORY_CANDIDATES = [
    '8ae390149e7b4d428507d79d4c1818c8',
    '60dc93d44b0e477c91b84a18aaefc200',
]

if __name__ == '__main__':
    print(f'[{STORE}] 시작...')
    items = []
    try:
        for cat in CATEGORY_CANDIDATES:
            print(f'  카테고리 {cat} 시도...')
            try:
                items = fetch_products(STORE_ID, category=cat)
            except NaverBlocked:
                raise  # 차단은 카테고리 문제가 아님 — 즉시 스킵 처리로
            except Exception as e:
                print(f'  실패: {e}')
                items = []
            if items:
                break
    except NaverBlocked as e:
        print(f'⏭️  {STORE}: {e}')
        print(f'⏭️  {STORE}: 기존 데이터 보존, 이번 갱신은 스킵')
        sys.exit(0)
    print(f'[{STORE}] 총 {len(items)}개')
    save(STORE, items, ID_START)
