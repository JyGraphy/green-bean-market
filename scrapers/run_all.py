"""
전체 스크래퍼 순서대로 실행 후 database.sql 재생성
GitHub Actions에서 호출됨

가나다 순:
- 더블유빈     → wbeans.com (클라이언트 렌더링, 현재 미지원)
- 모모스커피   ✅
- 블레스빈     🔜
- 아얀투       🔜
- 엠아이커피   🔜
- 오로미아코리아 🔜
- 오월의숲     🔜
- 지에스씨(GSC) 🔜
- 커만사       🔜
- 커피리브레   ✅ (생두소분 카테고리)
- 커피창고     🔜
- 커피플랜트   🔜
- 코빈즈커피   🔜
- 콤파스커피   🔜 (Sixshop, JS 필요)
- 팔콘커피     🔜
"""
import subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))

SCRAPERS = [
    # 가나다 순 (더블유빈 제외 — 클라이언트렌더링/차단)
    # 스마트스토어(루베르로스터리·아마티보)는 네이버가 데이터센터 IP를 차단하면
    # 스크래퍼가 스스로 스킵(정상 종료)하고 기존 데이터를 보존한다.
    ('scraper_ruber.py',       '루베르로스터리'),
    ('scraper_momos.py',       '모모스커피'),
    ('scraper_blessbean.py',   '블레스빈'),
    ('scraper_amativo.py',     '아마티보'),
    ('scraper_ayantu.py',      '아얀투'),
    ('scraper_micoffee.py',    '엠아이커피'),
    ('scraper_oromia.py',      '오로미아코리아'),
    ('scraper_mayforest.py',   '오월의숲'),
    ('scraper_gsc.py',         '지에스씨(GSC)'),
    ('scraper_comansa.py',     '커만사'),
    ('scraper_coffeelibre.py', '커피리브레'),
    ('scraper_coffeehouse.py', '커피창고'),
    ('scraper_coffeeplant.py', '커피플랜트'),
    ('scraper_cobeans.py',     '코빈즈커피'),
    # 콤파스커피: Sixshop JS렌더링 — 별도 처리 필요
    ('scraper_falcon.py',      '팔콘커피'),
]

errors = []

for filename, name in SCRAPERS:
    path = os.path.join(SCRAPERS_DIR, filename)
    print(f"\n{'='*50}")
    print(f"▶ {name} 스크래핑 중...")
    print(f"{'='*50}")
    result = subprocess.run([sys.executable, path], capture_output=False)
    if result.returncode != 0:
        print(f"❌ {name} 실패 (종료코드 {result.returncode})")
        errors.append(name)
    else:
        print(f"✅ {name} 완료")

print(f"\n{'='*50}")
print("▶ 상품 링크 연결성 검증 중...")
# 죽은 링크(404/410)만 제거. 체커 자체 오류는 비치명적(데이터 보존).
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, 'scripts', 'check_links.py')],
    capture_output=False
)
if result.returncode != 0:
    print("⚠️  링크 검증 비정상 종료 — 데이터는 보존됨(계속 진행)")

print(f"\n{'='*50}")
print("▶ 가공방식 보강 중 (상세페이지)...")
# 상품명으로 못 잡은 '알수없음'만 상세페이지에서 추출. 오류는 비치명적.
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, 'scripts', 'enrich_process.py')],
    capture_output=False
)
if result.returncode != 0:
    print("⚠️  가공방식 보강 비정상 종료 — 데이터는 보존됨(계속 진행)")

print(f"\n{'='*50}")
print("▶ database.sql 재생성 중...")
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, 'scripts', 'generate_sql.py')],
    capture_output=False
)
if result.returncode != 0:
    print("❌ database.sql 재생성 실패")
    errors.append('generate_sql')

print(f"\n{'='*50}")
if errors:
    print(f"⚠️  오류 발생: {', '.join(errors)}")
    sys.exit(1)
else:
    print("✅ 모든 스크래퍼 완료")
    sys.exit(0)
