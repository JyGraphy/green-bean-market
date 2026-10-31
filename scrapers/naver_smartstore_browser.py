"""네이버 스마트스토어 — 진짜 브라우저(Playwright) 기반 수집 (가정용 IP 전용).

네이버 차단 양상(2026-10-31 실측):
  · requests 호출 → 429 (쿠키 워밍업·재시도로도 불가)
  · 페이지 내 fetch → "Failed to fetch"
  · 내부 API(/i/v1·/i/v2) 로 직접 이동 → **로그인 창(nid.naver.com)으로 리다이렉트**
    즉 내부 API 는 이제 로그인 세션을 요구한다.
그런데 **카테고리 페이지 자체는 사람에게 로그인 없이 상품이 보인다.** 그래서:
  (1) 로그인 세션을 프로필 폴더에 저장(한 번만 수동 로그인)해 자동화 탐지를 넘고,
  (2) 렌더된 카테고리 페이지 DOM 에서 상품 카드(이름·가격·품절)를 직접 긁는다.
내부 API 는 쓰지 않는다(로그인 벽을 띄우는 원인).

로그인 쿠키가 담기는 프로필 폴더(.pw-naver-profile)는 .gitignore 로 커밋 제외한다.

CI(데이터센터 IP)는 브라우저로도 막히므로 로컬 전용.
준비(1회):  python3 -m pip install playwright && python3 -m playwright install chromium
"""
import os
import re
import sys

from naver_smartstore import normalize_price_1kg  # noqa: E402

BASE = 'https://smartstore.naver.com'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
PROFILE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           '.pw-naver-profile')
_LABELS = ('적립', '리뷰', '구매', '배송', '광고', '쿠폰', '할인', '찜', '관심',
           '브랜드', '스토어찜', '톡톡', 'BEST', 'NEW', '단독', '기획')


def _parse_card(text):
    lines = [x.strip() for x in text.split('\n') if x.strip()]
    prices = []
    for x in lines:
        for m in re.finditer(r'([\d,]{3,})\s*원', x):
            v = int(m.group(1).replace(',', ''))
            if v >= 1000:
                prices.append(v)
    price = min(prices) if prices else 0          # 할인가(보통 더 낮음) 채택
    soldout = ('품절' in text) or ('일시품절' in text)
    name = ''
    for x in lines:
        if '원' in x or '%' in x:
            continue
        if re.fullmatch(r'[\d,.\s]+', x):
            continue
        if any(k in x for k in _LABELS):
            continue
        if len(x) >= 3:
            name = x
            break
    return name, price, soldout


def _set_cp(url, cp):
    if 'cp=' in url:
        return re.sub(r'cp=\d+', f'cp={cp}', url)
    return url + ('&' if '?' in url else '?') + f'cp={cp}'


def _count_products(page):
    """상품 링크 개수 — 로케이터 사용(eval 안 씀 → CSP 안전)."""
    try:
        return page.locator('a[href*="/products/"]').count()
    except Exception:
        return 0


def _scroll(page):
    prev = -1
    for _ in range(25):
        n = _count_products(page)
        if n == prev:
            break
        prev = n
        page.mouse.wheel(0, 24000)
        page.wait_for_timeout(600)


def _collect_cards(page):
    """상품 카드를 로케이터로 수집 → [{id, href, text}]. page.evaluate(eval) 미사용.

    네이버 일부 페이지는 CSP 로 unsafe-eval 을 막아 page.evaluate/wait_for_function 이
    터진다. 그래서 selector 엔진·inner_text(프로토콜 기반, CSP 무관)만 쓴다.
    """
    anchors = page.locator('a[href*="/products/"]')
    out, seen = [], set()
    for i in range(anchors.count()):
        a = anchors.nth(i)
        href = a.get_attribute('href') or ''
        m = re.search(r'/products/(\d+)', href)
        if not m or m.group(1) in seen:
            continue
        pid = m.group(1)
        seen.add(pid)
        text = ''
        for sel in ('xpath=ancestor::li[1]', 'xpath=ancestor::div[2]'):
            try:
                t = a.locator(sel).first.inner_text(timeout=800)
                if t and t.strip():
                    text = t.strip()
                    break
            except Exception:
                pass
        if not text:
            try:
                text = (a.inner_text(timeout=800) or '').strip()
            except Exception:
                text = ''
        out.append({'id': pid, 'href': href.split('?')[0], 'text': text})
    return out


def _wait_leave_login(page, landing, headless):
    """로그인 창이면 사용자가 로그인할 때까지 URL 을 폴링(wait_for_function 금지 — 로그인
    페이지 CSP 가 eval 을 막아 터진다). headless 는 안내 후 중단."""
    import time
    if 'nid.naver.com' not in page.url:
        return True
    if headless:
        raise RuntimeError(
            '네이버 로그인 창으로 막혔습니다. 최초 1회는 창을 띄워 로그인해야 합니다:\n'
            '    python3 scripts/update_smartstore_browser_local.py  (창 모드)\n'
            '뜬 크롬 창에서 네이버에 로그인하면 세션이 .pw-naver-profile 에 저장되어, '
            '이후 자동 실행에서는 로그인이 필요 없습니다.')
    print('  🔑 네이버 로그인 창이 떴습니다 — 열린 크롬 창에서 직접 로그인해 주세요. '
          '(최대 300초 대기, 로그인되면 자동으로 이어집니다)')
    start = time.monotonic()
    while 'nid.naver.com' in page.url:
        if time.monotonic() - start > 300:
            raise RuntimeError('로그인 대기 300초 초과 — 로그인이 완료되지 않았습니다.')
        page.wait_for_timeout(1500)
    page.goto(landing, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(1500)
    return True


def fetch_products_browser(store_id, category='ALL', landing_url=None, headless=True):
    """실제 브라우저로 카테고리 페이지 DOM 을 긁어 상품 수집.

    → [{'name','price','url','is_soldout'}]
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            'playwright 미설치. 먼저:\n    python3 -m pip install playwright\n'
            '    python3 -m playwright install chromium')

    landing = landing_url or f'{BASE}/{store_id}'
    os.makedirs(PROFILE_DIR, exist_ok=True)
    all_cards = {}
    with sync_playwright() as p:
        # 영속 프로필 — 한 번 로그인하면 쿠키가 남아 다음부터 자동 통과.
        ctx = p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=headless, locale='ko-KR', user_agent=UA,
            timezone_id='Asia/Seoul', viewport={'width': 1280, 'height': 900},
            # 자동화 탐지 회피 1: AutomationControlled 플래그 끄기
            args=['--disable-blink-features=AutomationControlled',
                  '--no-sandbox', '--disable-dev-shm-usage'])
        # 자동화 탐지 회피 2: navigator.webdriver 등 봇 지문 제거(스텔스).
        # 네이버가 이 지문으로 자동 브라우저를 로그인 창으로 튕긴다 — 사람처럼 위장한다.
        ctx.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            window.chrome = window.chrome || {runtime: {}};
            const _q = window.navigator.permissions && window.navigator.permissions.query;
            if (_q) window.navigator.permissions.query = (p) =>
                p && p.name === 'notifications'
                    ? Promise.resolve({state: Notification.permission})
                    : _q(p);
        """)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(landing, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(1500)
        _wait_leave_login(page, landing, headless)

        for cp in range(1, 11):
            if cp > 1:
                page.goto(_set_cp(landing, cp), wait_until='domcontentloaded', timeout=60000)
                page.wait_for_timeout(1200)
            if 'nid.naver.com' in page.url:
                _wait_leave_login(page, _set_cp(landing, cp), headless)
            try:
                page.wait_for_selector('a[href*="/products/"]', timeout=12000)
            except Exception:
                break
            _scroll(page)
            cards = _collect_cards(page)
            new = 0
            for c in cards:
                if c['id'] not in all_cards:
                    all_cards[c['id']] = c
                    new += 1
            print(f'  cp={cp}: 카드 {len(cards)}개 (신규 {new}, 누적 {len(all_cards)})')
            if new == 0:
                break
        ctx.close()

    items, seen = [], set()
    for c in all_cards.values():
        name, price, soldout = _parse_card(c.get('text', ''))
        if not name or not price:
            continue
        url = c.get('href') or f'{BASE}/{store_id}/products/{c["id"]}'
        if url in seen:
            continue
        seen.add(url)
        items.append({'name': name, 'price': normalize_price_1kg(name, price),
                      'url': url, 'is_soldout': soldout})
    print(f'  DOM 수집: 상품 {len(items)}개 (카드 {len(all_cards)}개)')
    return items


if __name__ == '__main__':
    sid = sys.argv[1] if len(sys.argv) > 1 else 'ruberroastery'
    land = sys.argv[2] if len(sys.argv) > 2 else None
    for it in fetch_products_browser(sid, landing_url=land, headless=False):
        print(f"  {it['price']}원 {'[품절]' if it['is_soldout'] else ''} {it['name'][:55]}  {it['url']}")
