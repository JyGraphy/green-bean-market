"""아마티보 생두 스크래퍼 — 네이버 스마트스토어 (smartstore.naver.com/amativo)

매일 자동 갱신(run_all.py)에 포함되어 있다. 단 네이버는 데이터센터 IP를
차단하는 경우가 많아, CI에서 차단(429/로그인 월) 감지 시 기존 데이터를
보존하고 스킵(정상 종료)한다 — 잡을 실패로 만들지 않는다.

초기 수집이나 차단 시 보강은 가정용 IP의 로컬 PC에서:

    pip install requests
    python scrapers/scraper_amativo.py
    python scripts/generate_sql.py   # 파생 파일 재생성
"""
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from naver_smartstore import NaverBlocked, fetch_products, save

STORE = '아마티보'
STORE_ID = 'amativo'
ID_START = 900

if __name__ == '__main__':
    print(f'[{STORE}] 시작...')
    try:
        items = fetch_products(STORE_ID)  # 전체 상품 (생두 전문몰)
    except NaverBlocked as e:
        print(f'⏭️  {STORE}: {e}')
        print(f'⏭️  {STORE}: 기존 데이터 보존, 이번 갱신은 스킵')
        sys.exit(0)
    print(f'[{STORE}] 총 {len(items)}개')
    save(STORE, items, ID_START)
