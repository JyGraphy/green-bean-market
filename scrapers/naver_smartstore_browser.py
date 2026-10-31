"""네이버 스마트스토어 — 진짜 브라우저(Playwright) 기반 수집 (가정용 IP 전용).

왜: 네이버 안티봇이 requests 호출을 429 로, 페이지 내 fetch 를 "Failed to fetch"
(로그인 리다이렉트/CSP)로 막는다(2026-10-31 실측). 그래서 실제 브라우저로:
  (A) 내부 API 주소로 **직접 이동(navigate)** 해 응답 JSON 을 읽고(페이지 CSP·서비스워커
      를 안 타고, 실제 쿠키·헤더가 실린다),
  (B) 그래도 안 되면 렌더된 **카테고리 페이지 DOM** 에서 상품 카드를 긁는다
      (사람이 보는 화면 그대로라 가장 막기 어렵다).
둘 다 실패하면 진단 정보(상태코드·최종 URL·본문 일부)를 담아 올린다.

CI(데이터센터 IP)는 브라우저로도 로그인 월에 막히므로 로컬 전용.

준비(1회):  python3 -m pip install playwright && python3 -m playwright install chromium
"""
import json
import re
import sys

from naver_smartstore import normalize_price_1kg  # noqa: E402

BASE = 'https://smartstore.naver.com'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

_LABELS = ('적립', '리뷰', '구매', '배송', '광고', '쿠폰', '할인', '찜', '관심',
           '브랜드', '스토어찜', '톡톡', 'BEST', 'NEW')


def _nav_json(page, url):
    """API URL 로 이동해 응답을 (status, json|None, 진단문자열) 로 반환."""
    try:
        resp = page.goto(url, wait_until='domcontentloaded', timeout=30000)
    except Exception as e:
        return None, None, f'goto 실패: {type(e).__name__}: {e}'
    status = resp.status if resp else None
    final = page.url
    if 'nid.naver.com' in final:
        return status, None, f'로그인 리다이렉트({final[:60]})'
    try:
        return status, resp.json(), ''
    except Exception:
        body = (resp.text() if resp else '') or ''
        return status, None, f'JSON 아님 (status={status}, url={final[:50]}, 본문[:120]={body[:120]!r})'


def _collect_via_api(page, store_id, category):
    """API 직접 이동으로 상품 수집. (raw_products, 진단) 반환."""
    st, info, diag = _nav_json(page, f'{BASE}/i/v1/smart-stores?url={store_id}')
    if not isinstance(info, dict) or not info.get('id'):
        return [], f'채널ID 실패(status={st}): {diag or info}'
    chid = info['id']
    ctype = 'STDCATG' if category == 'ALL' else 'DISPCATG'
    raw, pg, total = [], 1, 0
    while pg <= 50:
        url = (f'{BASE}/i/v2/channels/{chid}/categories/{category}/products'
               f'?categorySearchType={ctype}&sortType=TOTALSALE&page={pg}&pageSize=40')
        st, data, diag = _nav_json(page, url)
        if not isinstance(data, dict):
            return raw, f'상품 조회 실패(page {pg}, status={st}): {diag}'
        prods = data.get('simpleProducts') or data.get('products') or []
        total = data.get('totalCount', 0)
        raw.extend(prods)
        if pg * 40 >= total or not prods:
            break
        pg += 1
    return raw, f'API 성공 (total {total})'


def _map_api(raw, store_id):
    items, seen = [], set()
    for pr in raw:
        name = (pr.get('name') or '').strip()
        if not name:
            continue
        benefits = pr.get('benefitsView') or {}
        price = benefits.get('discountedSalePrice') or pr.get('salePrice') or 0
        if not price:
            continue
        prod_no = pr.get('id') or pr.get('productNo')
        url = f'{BASE}/{store_id}/products/{prod_no}'
        if url in seen:
            continue
        seen.add(url)
        items.append({
            'name': name,
            'price': normalize_price_1kg(name, int(price)),
            'url': url,
            'is_soldout': pr.get('productStatusType') == 'OUTOFSTOCK',
        })
    return items


_DOM_JS = r"""
() => {
  const out = [], seen = new Set();
  document.querySelectorAll('a[href*="/products/"]').forEach(a => {
    const m = (a.getAttribute('href') || '').match(/\/products\/(\d+)/);
    if (!m) return;
    const id = m[1];
    if (seen.has(id)) return;
    seen.add(id);
    const card = a.closest('li') || a.closest('div') || a;
    out.push({id, href: a.href, text: (card.innerText || '').trim()});
  });
  return out;
}
"""


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


def _collect_via_dom(page, store_id, landing):
    page.goto(landing, wait_until='domcontentloaded', timeout=60000)
    try:
        page.wait_for_selector('a[href*="/products/"]', timeout=15000)
    except Exception:
        return [], 'DOM: 상품 링크가 안 나타남'
    prev = -1
    for _ in range(25):                 # lazy-load 스크롤
        n = page.evaluate("() => document.querySelectorAll('a[href*=\"/products/\"]').length")
        if n == prev:
            break
        prev = n
        page.mouse.wheel(0, 24000)
        page.wait_for_timeout(700)
    cards = page.evaluate(_DOM_JS)
    items, seen = [], set()
    for c in cards:
        name, price, soldout = _parse_card(c.get('text', ''))
        if not name or not price:
            continue
        url = c.get('href') or f'{BASE}/{store_id}/products/{c["id"]}'
        if url in seen:
            continue
        seen.add(url)
        items.append({'name': name, 'price': normalize_price_1kg(name, price),
                      'url': url, 'is_soldout': soldout})
    return items, f'DOM 파싱 {len(items)}개 (카드 {len(cards)}개)'


def fetch_products_browser(store_id, category='ALL', landing_url=None, headless=True):
    """실제 브라우저로 스토어 상품 수집 → [{'name','price','url','is_soldout'}]."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            'playwright 미설치. 먼저:\n    python3 -m pip install playwright\n'
            '    python3 -m playwright install chromium')

    landing = landing_url or f'{BASE}/{store_id}'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(locale='ko-KR', user_agent=UA,
                                  viewport={'width': 1280, 'height': 900})
        page = ctx.new_page()
        # 세션·쿠키 확립
        page.goto(landing, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(2000)

        raw, api_diag = _collect_via_api(page, store_id, category)
        items = _map_api(raw, store_id)
        print(f'  [API] {api_diag} → 생두추출 {len(items)}개')

        dom_diag = '(건너뜀)'
        if not items:
            items, dom_diag = _collect_via_dom(page, store_id, landing)
            print(f'  [DOM] {dom_diag}')
        browser.close()

    if not items:
        raise RuntimeError(f'{store_id}: 수집 0개 — API:{api_diag} / DOM:{dom_diag}')
    return items


if __name__ == '__main__':
    sid = sys.argv[1] if len(sys.argv) > 1 else 'ruberroastery'
    cat = sys.argv[2] if len(sys.argv) > 2 else 'ALL'
    for it in fetch_products_browser(sid, cat, headless=False):
        print(f"  {it['price']}원 {'[품절]' if it['is_soldout'] else ''} {it['name'][:55]}  {it['url']}")
