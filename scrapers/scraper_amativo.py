"""아마티보 생두 스크래퍼 — 네이버 스마트스토어 (smartstore.naver.com/amativo)

⚠️ 네이버는 데이터센터 IP를 차단하므로 CI(run_all.py)에서 실행하지 않는다.
   가정용 IP의 로컬 PC에서 수동 실행 후 data/*.json을 커밋할 것:

       pip install requests
       python scrapers/scraper_amativo.py
       python scripts/generate_sql.py   # 파생 파일 재생성
"""
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from naver_smartstore import fetch_products, save

STORE = '아마티보'
STORE_ID = 'amativo'
ID_START = 900

if __name__ == '__main__':
    print(f'[{STORE}] 시작...')
    items = fetch_products(STORE_ID)  # 전체 상품 (생두 전문몰)
    print(f'[{STORE}] 총 {len(items)}개')
    save(STORE, items, ID_START)
