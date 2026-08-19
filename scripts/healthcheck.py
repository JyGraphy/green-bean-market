"""
배포 후 라이브 사이트 자동 헬스체크 (재발 방지).

매일 갱신·배포가 끝난 뒤 GitHub Actions가 실제 라이브 사이트를 점검한다.
하나라도 실패하면 종료코드 1 → 워크플로 빨간 X → 저장소 소유자에게 알림 메일.
즉 사용자가 사이트에서 직접 발견하기 전에 자동으로 잡는다.

검사 항목:
  1. 사이트 루트가 HTTP 200 (사이트 다운/403 인증게이트 감지)
  2. products_web.json 로드 가능 + 상품 수가 임계치 이상 (데이터 소멸/급감 감지)
  3. **상품 url이 전부 외부 절대경로** — 상대경로거나 우리 도메인을 가리키면 실패
     (커만사/지에스씨류 '클릭 시 우리 도메인 403' 재발의 결정적 신호)
  4. 기대 store가 모두 존재 (store 소멸 감지)
  5. (경고) store별 상품 링크 표본을 실제로 찔러봐 404면 경고 (403/타임아웃은 무시)
  6. **Supabase 백엔드 생존 확인** — 로그인·원두 컬렉션·로스팅 프로파일이 전부 여기에 의존한다.
     무료 플랜은 일정 기간 요청이 없으면 프로젝트를 자동 일시정지(pause)하는데,
     그러면 정적 페이지는 멀쩡해 보이지만 위 기능들이 통째로 죽는다.
     2026-08-19에 실제로 이 일이 있었고, 정적 사이트만 보던 헬스체크는 초록불이었다.
     그래서 백엔드 점검을 여기에 추가한다.

사용법: python scripts/healthcheck.py <BASE_URL>
  예) python scripts/healthcheck.py https://green-bean-market.vercel.app
"""
import sys, json, time
from urllib.parse import urlparse
import requests

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
MIN_PRODUCTS = 800          # 이 아래면 데이터 소멸로 간주
OWN_DOMAIN_HINTS = ('green-bean-market', 'vercel.app', 'netlify.app')
EXPECTED_STORES = {
    '커피플랜트', '커피창고', '엠아이커피', '모모스커피', '코빈즈커피', '아얀투',
    '오월의숲', '커피리브레', '블레스빈', '콤파스커피', '커만사', '지에스씨(GSC)',
    '팔콘커피', '오로미아코리아',
}


SUPABASE_URL = 'https://txnpbzukavajwbmggpfk.supabase.co'
SUPABASE_ANON = 'sb_publishable_KeqUfylPUoX8YSCbKGjqEQ_pQCzFFBF'


def fail(msg, errs):
    errs.append(msg)


def check_supabase(errs, warns):
    """Supabase 프로젝트가 살아 있는지 확인한다.

    무료 플랜은 요청이 없으면 프로젝트를 일시정지하고, 그 상태에서는 로그인·
    원두 컬렉션·로스팅 프로파일이 전부 동작하지 않는다. 정적 페이지만 보는
    기존 검사로는 이걸 못 잡아서 별도 항목으로 둔다.

    부수 효과로 매일 1회 요청이 발생해 '무활동' 판정도 늦춰진다.
    """
    url = f'{SUPABASE_URL}/rest/v1/'
    try:
        r = requests.get(url, headers={**UA, 'apikey': SUPABASE_ANON}, timeout=15)
    except requests.RequestException as e:
        fail(f'Supabase 백엔드 연결 실패 ({type(e).__name__}) — '
             f'로그인/원두컬렉션/로스팅 프로파일이 동작하지 않습니다', errs)
        return
    # 일시정지된 프로젝트는 보통 503/540 또는 게이트웨이 오류를 돌려준다.
    if r.status_code in (503, 540) or 'paused' in r.text.lower():
        fail(f'Supabase 프로젝트가 일시정지(paused)로 보입니다 (HTTP {r.status_code}) — '
             f'대시보드에서 Resume 필요. 로그인/원두컬렉션/로스팅 프로파일 전부 중단 상태', errs)
    elif r.status_code >= 500:
        fail(f'Supabase 백엔드 오류 HTTP {r.status_code}', errs)
    elif r.status_code >= 400:
        # 401/404 등은 REST 루트 특성상 정상 응답일 수 있으나 기록은 남긴다.
        warns.append(f'Supabase 응답 HTTP {r.status_code} — 서버는 살아 있으나 확인 권장')


def main(base):
    base = base.rstrip('/')
    errs, warns = [], []
    v = str(int(time.time()))  # 캐시 우회(라이브 최신 강제)

    # 1) 사이트 루트
    try:
        r = requests.get(base + '/?v=' + v, headers=UA, timeout=30, allow_redirects=True)
        if r.status_code != 200:
            fail(f"사이트 루트 비정상: HTTP {r.status_code} ({base})", errs)
    except Exception as e:
        fail(f"사이트 루트 요청 실패: {e}", errs)

    # 2) products_web.json
    products = None
    try:
        r = requests.get(base + '/data/products_web.json?v=' + v, headers=UA, timeout=30)
        if r.status_code != 200:
            fail(f"products_web.json HTTP {r.status_code}", errs)
        else:
            products = r.json()
    except Exception as e:
        fail(f"products_web.json 로드 실패: {e}", errs)

    if products is not None:
        # 상품 수
        if len(products) < MIN_PRODUCTS:
            fail(f"상품 수 급감: {len(products)}개 (< {MIN_PRODUCTS})", errs)

        # 3) url 검사 — 상대경로 또는 우리 도메인 가리키면 실패
        bad = []
        for p in products:
            u = str(p.get('url', ''))
            host = urlparse(u).netloc.lower()
            if not u.startswith('http') or any(h in host for h in OWN_DOMAIN_HINTS):
                bad.append((p.get('store'), u))
        if bad:
            from collections import Counter
            by = Counter(s for s, _ in bad)
            fail(f"잘못된 상품 url {len(bad)}건(상대경로/우리도메인): {dict(by)} 예) {bad[0][1]!r}", errs)

        # 4) store 소멸
        stores = {p.get('store') for p in products}
        missing = EXPECTED_STORES - stores
        if missing:
            fail(f"store 소멸: {sorted(missing)}", errs)

        # 5) 표본 링크 실제 연결성 — store별 여러 개를 찔러본다.
        #    한 개만 404면 단순 품절/삭제(경고), 표본 다수가 404면 store 전체 URL
        #    형식이 깨진 것(예: 경로 중복)으로 보고 실패시킨다.
        from collections import defaultdict
        per_store = defaultdict(list)
        for p in products:
            per_store[p.get('store')].append(p.get('url'))
        for store, urls in per_store.items():
            sample = urls[:3]
            dead = 0
            for u in sample:
                try:
                    rr = requests.head(u, headers=UA, timeout=15, allow_redirects=True)
                    if rr.status_code in (404, 410):
                        dead += 1
                except Exception:
                    pass  # 403/타임아웃 등은 봇차단/일시장애일 수 있어 무시
            if len(sample) >= 2 and dead == len(sample):
                fail(f"store 링크 전멸: '{store}' 표본 {dead}/{len(sample)} 404 — URL 형식 손상 의심 ({sample[0]})", errs)
            elif dead:
                warns.append(f"{store} 표본 링크 {dead}/{len(sample)} 404 (개별 품절/삭제 가능)")

    # 결과
    print("=" * 55)
    check_supabase(errs, warns)

    print(f"🩺 라이브 헬스체크: {base}")
    if products is not None:
        print(f"   상품 {len(products)}개")
    if warns:
        print("⚠️  경고:")
        for w in warns:
            print(f"   - {w}")
    if errs:
        print("❌ 실패:")
        for e in errs:
            print(f"   - {e}")
        print("\n→ 라이브 사이트에 문제가 있습니다. 위 항목을 확인하세요.")
        sys.exit(1)
    print("✅ 라이브 사이트 정상")
    sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'https://green-bean-market.vercel.app')
