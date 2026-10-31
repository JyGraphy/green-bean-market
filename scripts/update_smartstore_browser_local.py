"""스마트스토어 브라우저(Playwright) 로컬 수집 — 가정용 IP 전용.

네이버가 requests 호출을 429 로 막아(쿠키·헤더·재시도로도 불가, 2026-10-31 실측)
실제 브라우저로만 수집이 된다. 이 스크립트를 **집 PC**에서 실행하면 루베르·아마티보
스마트스토어를 브라우저로 수집해 커밋·푸시한다.

준비(1회):
    python3 -m pip install playwright
    python3 -m playwright install chromium

실행(크롬 창이 뜸 — 최초 1회 네이버 로그인 필요):
    python3 scripts/update_smartstore_browser_local.py

로그인 세션이 .pw-naver-profile 에 저장되므로, 이후에는 창에서 로그인할 필요가 없다.
스케줄러 등에서 창 없이 돌리려면(로그인 쿠키가 이미 저장된 뒤에만):
    HEADLESS=1 python3 scripts/update_smartstore_browser_local.py
"""
import os
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scrapers'))

from naver_smartstore import save  # noqa: E402
from naver_smartstore_browser import fetch_products_browser  # noqa: E402

# 기본은 창 띄움(headful) — 최초 1회 네이버 로그인이 필요하기 때문.
# 로그인 쿠키가 저장된 뒤 HEADLESS=1 로 창 없이 돌릴 수 있다.
HEADLESS = os.environ.get('HEADLESS') == '1'

# (STORE, STORE_ID, category, ID_START, landing_url)
TARGETS = [
    ('루베르로스터리', 'ruberroastery', '8ae390149e7b4d428507d79d4c1818c8', 950,
     'https://smartstore.naver.com/ruberroastery/category/8ae390149e7b4d428507d79d4c1818c8?cp=1'),
    ('아마티보', 'amativo', 'ALL', 900, None),
]

COMMIT_FILES = [
    'data/products.json', 'database.sql', 'data/product_dates.json',
    'data/update_log.json', 'data/products_web.json',
]


def run(cmd, **kw):
    print('$', ' '.join(cmd))
    return subprocess.run(cmd, cwd=ROOT, **kw)


def main():
    if run(['git', 'pull', '--ff-only', 'origin', 'main']).returncode != 0:
        print('⚠️  git pull 실패 — 로컬 변경/충돌 정리 후 다시 실행하세요.')
        return 1

    ok = 0
    for store, sid, cat, id_start, landing in TARGETS:
        print(f'\n▶ {store} 브라우저 수집... (headless={HEADLESS})')
        try:
            items = fetch_products_browser(sid, category=cat, landing_url=landing,
                                           headless=HEADLESS)
        except Exception as e:
            print(f'❌ {store} 실패: {type(e).__name__}: {e}')
            continue
        print(f'[{store}] 총 {len(items)}개')
        if not items:
            print(f'⏭️  {store}: 0개 — 기존 데이터 보존, 스킵')
            continue
        try:
            save(store, items, id_start)   # guard/ID충돌/비생두필터 내장
            ok += 1
        except SystemExit:
            print(f'⚠️  {store}: 가드가 교체를 막음(0개/급감) — 기존 데이터 보존')

    if ok == 0:
        print('\n⚠️  수집된 store 없음 — 커밋 없이 종료')
        return 1

    if run(['git', 'diff', '--quiet', 'data/products.json']).returncode == 0:
        print('📦 상품 변경 없음 — 커밋 스킵')
        return 0

    if run([sys.executable, os.path.join(ROOT, 'scripts', 'generate_sql.py')]).returncode != 0:
        print('❌ generate_sql 실패 — 커밋하지 않음')
        return 1
    if run([sys.executable, os.path.join(ROOT, 'scripts', 'validate_data.py')]).returncode != 0:
        print('❌ 데이터 무결성 검증 실패 — 커밋하지 않음')
        return 1

    run(['git', 'add'] + COMMIT_FILES)
    msg = f'스마트스토어 브라우저 수집(로컬): {date.today().isoformat()} 루베르·아마티보'
    if run(['git', 'commit', '-m', msg]).returncode != 0:
        print('📦 커밋할 변경 없음')
        return 0
    if run(['git', 'push', 'origin', 'main']).returncode != 0:
        print('⚠️  push 실패 — git push origin main 을 직접 실행하세요.')
        return 1
    print('✅ 스마트스토어 브라우저 수집 완료')
    return 0


if __name__ == '__main__':
    sys.exit(main())
