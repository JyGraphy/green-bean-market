"""스마트스토어(아마티보·루베르로스터리) 로컬 자동 갱신 스크립트.

네이버는 데이터센터 IP를 차단하므로 CI에서는 이 두 store를 갱신할 수 없다.
이 스크립트를 가정용 IP의 PC에서 스케줄러로 매일 실행하면, CI가 못 하는
스마트스토어 갱신을 로컬이 대신 수행해 커밋·푸시한다.
(CI 쪽 스크래퍼는 차단 감지 시 스킵하므로 서로 충돌하지 않는다.)

1회 준비:
    pip install requests
    git clone https://github.com/JyGraphy/green-bean-market.git  # 이미 있으면 생략

수동 실행:
    python scripts/update_smartstore_local.py

매일 06:10 자동 실행 등록 (CI 06:00 갱신 직후 — 푸시 충돌 방지):
  · Windows (작업 스케줄러):
      schtasks /Create /TN "GreenBeanSmartstore" /SC DAILY /ST 06:10 ^
        /TR "python C:\\경로\\green-bean-market\\scripts\\update_smartstore_local.py"
  · macOS / Linux (crontab -e):
      10 6 * * * cd /경로/green-bean-market && python3 scripts/update_smartstore_local.py >> /tmp/greenbean.log 2>&1
"""
import os
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRAPERS = [
    ('scrapers/scraper_amativo.py', '아마티보'),
    ('scrapers/scraper_ruber.py', '루베르로스터리'),
]

COMMIT_FILES = [
    'data/products.json', 'database.sql', 'data/product_dates.json',
    'data/update_log.json', 'data/products_web.json',
]


def run(cmd, **kw):
    print('$', ' '.join(cmd))
    return subprocess.run(cmd, cwd=ROOT, **kw)


def main():
    # 최신 상태에서 시작 (CI의 06시 커밋을 먼저 받는다)
    if run(['git', 'pull', '--ff-only', 'origin', 'main']).returncode != 0:
        print('⚠️  git pull 실패 — 로컬 변경/충돌을 정리한 뒤 다시 실행하세요.')
        return 1

    ok = 0
    for path, name in SCRAPERS:
        print(f'\n▶ {name} 스크래핑...')
        if run([sys.executable, os.path.join(ROOT, path)]).returncode == 0:
            ok += 1
        else:
            print(f'❌ {name} 실패 — 기존 데이터는 보존됨')

    if ok == 0:
        print('⚠️  두 스크래퍼 모두 실패 — 커밋 없이 종료')
        return 1

    # 변경 여부 확인 (products.json 기준)
    if run(['git', 'diff', '--quiet', 'data/products.json']).returncode == 0:
        print('📦 상품 변경 없음 — 커밋 스킵')
        return 0

    # 파생 파일 재생성 후 검증 게이트 통과 시에만 커밋
    if run([sys.executable, os.path.join(ROOT, 'scripts', 'generate_sql.py')]).returncode != 0:
        print('❌ generate_sql 실패 — 커밋하지 않음')
        return 1
    if run([sys.executable, os.path.join(ROOT, 'scripts', 'validate_data.py')]).returncode != 0:
        print('❌ 데이터 무결성 검증 실패 — 커밋하지 않음')
        return 1

    run(['git', 'add'] + COMMIT_FILES)
    msg = f'스마트스토어 갱신(로컬): {date.today().isoformat()} 아마티보·루베르로스터리'
    if run(['git', 'commit', '-m', msg]).returncode != 0:
        print('📦 커밋할 변경 없음')
        return 0
    if run(['git', 'push', 'origin', 'main']).returncode != 0:
        print('⚠️  push 실패 — 네트워크 확인 후 git push를 직접 실행하세요.')
        return 1
    print('✅ 스마트스토어 갱신 완료')
    return 0


if __name__ == '__main__':
    sys.exit(main())
