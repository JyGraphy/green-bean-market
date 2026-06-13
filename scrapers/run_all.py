"""
전체 스크래퍼 순서대로 실행 후 data.js 재생성
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
    ('scraper_momos.py',       '모모스커피'),
    ('scraper_blessbean.py',   '블레스빈'),
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
print("▶ data.js 재생성 중...")
result = subprocess.run(
    [sys.executable, os.path.join(ROOT, 'scripts', 'generate_data_js.py')],
    capture_output=False
)
if result.returncode != 0:
    print("❌ data.js 재생성 실패")
    errors.append('generate_data_js')

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
