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
import subprocess, sys, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRAPERS_DIR = os.path.dirname(os.path.abspath(__file__))

# ── 타임아웃 (초) ──────────────────────────────────────────────────
# **왜 필요한가** — 예전엔 어디에도 타임아웃이 없어서, 쇼핑몰 한 곳이 응답을 안 주면
# 매일 06시 파이프라인이 통째로 매달린다. GitHub 잡 상한이 6시간이라 그때까지 붙잡혀
# 있을 수 있고, 그 사이 정상 수집된 store 도 커밋되지 못한다(커밋이 맨 뒤라서).
#
# ⚠️ 정정 (2026-08-20): 이 방어는 **예방 조치**다. 실제로 매달린 적은 없다.
#    처음 이 코드를 넣을 때 "수집이 40분을 넘겨도 안 끝났다"고 적었는데 그건 오측이었다.
#    실제 실행은 4분 진행 중이었고, 관측자가 경과 시간을 잘못 셌을 뿐이다.
#    (참고 실측: 2026-08-19 정기 실행 전체 소요 16분 — GitHub 타임스탬프 기준)
#
# 값은 '평소보다 넉넉하되 하루를 잡아먹지는 않는' 선으로 잡았다.
# 시간이 초과되면 그 단계만 실패로 처리하고 다음으로 넘어간다 — 가드가 있으므로
# 덜 긁힌 데이터가 기존 데이터를 덮어쓰지는 않는다.
SCRAPER_TIMEOUT = 600      # store 1곳 (평소 수십 초~2분)
LINKCHECK_TIMEOUT = 1800   # 전 상품 링크 확인 (1,000건 이상 × HTTP 요청)
ENRICH_TIMEOUT = 1200      # '알수없음' 상품만 상세페이지 조회
SQL_TIMEOUT = 300          # 로컬 파일 생성 (네트워크 없음)


# 단계별 소요시간 기록 — [(라벨, 초, 성공여부), ...]
# **왜 재는가**: "어디가 오래 걸리나"를 짐작으로 답하면 엉뚱한 곳을 고치게 된다.
# 공급사가 늘수록 이 숫자가 판단 근거가 되어야 하므로 매 실행마다 남긴다.
TIMINGS = []


def run_step(argv, label, timeout):
    """하위 프로세스를 타임아웃과 함께 실행한다. (성공여부, 사유) 반환."""
    t0 = time.monotonic()
    try:
        r = subprocess.run(argv, capture_output=False, timeout=timeout)
        ok, why = (r.returncode == 0), ('' if r.returncode == 0 else f'종료코드 {r.returncode}')
    except subprocess.TimeoutExpired:
        print(f"⏱️  {label} 타임아웃 ({timeout}초 초과) — 중단하고 다음으로 넘어갑니다")
        ok, why = False, 'timeout'
    TIMINGS.append((label, time.monotonic() - t0, ok))
    return ok, why


def print_timings():
    """소요시간을 오래 걸린 순으로 출력한다."""
    if not TIMINGS:
        return
    total = sum(sec for _, sec, _ in TIMINGS)
    print(f"\n{'='*50}")
    print(f"⏱️  단계별 소요시간 (합계 {total/60:.1f}분)")
    for label, sec, ok in sorted(TIMINGS, key=lambda x: -x[1]):
        share = sec / total * 100 if total else 0
        mark = ' ' if ok else '✗'
        print(f"   {mark} {label:22} {sec:6.1f}초  {share:4.1f}%")

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
    ok, why = run_step([sys.executable, path], name, SCRAPER_TIMEOUT)
    if ok:
        print(f"✅ {name} 완료")
    else:
        print(f"❌ {name} 실패 ({why})")
        errors.append(f'{name}({why})' if why == 'timeout' else name)

print(f"\n{'='*50}")
print("▶ 상품 링크 연결성 검증 중...")
# 죽은 링크(404/410)만 제거. 체커 자체 오류는 비치명적(데이터 보존).
ok, why = run_step([sys.executable, os.path.join(ROOT, 'scripts', 'check_links.py')],
                   '링크 검증', LINKCHECK_TIMEOUT)
if not ok:
    print(f"⚠️  링크 검증 비정상 종료({why}) — 데이터는 보존됨(계속 진행)")

print(f"\n{'='*50}")
print("▶ 가공방식 보강 중 (상세페이지)...")
# 상품명으로 못 잡은 '알수없음'만 상세페이지에서 추출. 오류는 비치명적.
ok, why = run_step([sys.executable, os.path.join(ROOT, 'scripts', 'enrich_process.py')],
                   '가공방식 보강', ENRICH_TIMEOUT)
if not ok:
    print(f"⚠️  가공방식 보강 비정상 종료({why}) — 데이터는 보존됨(계속 진행)")

print(f"\n{'='*50}")
print("▶ database.sql 재생성 중...")
ok, why = run_step([sys.executable, os.path.join(ROOT, 'scripts', 'generate_sql.py')],
                   'database.sql 재생성', SQL_TIMEOUT)
if not ok:
    print("❌ database.sql 재생성 실패")
    errors.append('generate_sql')

print_timings()

print(f"\n{'='*50}")
if errors:
    print(f"⚠️  오류 발생: {', '.join(errors)}")
    sys.exit(1)
else:
    print("✅ 모든 스크래퍼 완료")
    sys.exit(0)
