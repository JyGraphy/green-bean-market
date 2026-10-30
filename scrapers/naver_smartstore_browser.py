"""네이버 스마트스토어 — 진짜 브라우저(Playwright) 기반 수집.

왜 필요한가: 네이버 안티봇이 쿠키·헤더를 붙인 requests 호출까지 429 로 막는다
(2026-10-31 실측: 가정용 IP + 쿠키 워밍업 + 재시도에도 429). 사람이 크롬으로
스토어를 보는 건 멀쩡히 되므로, 실제 브라우저를 띄워 **그 페이지 컨텍스트 안에서**
스토어 내부 API(fetch)를 호출한다 — same-origin + 실제 세션이라 통과한다.

CI(GitHub Actions)는 데이터센터 IP라 브라우저로도 로그인 월로 막히므로 여기선 못 쓴다.
**가정용 IP 의 로컬 PC 전용**이다.

준비(1회):
    python3 -m pip install playwright
    python3 -m playwright install chromium

사용: scripts/update_smartstore_browser_local.py 가 호출한다.
"""
import sys

# requests 경로와 동일한 정규화를 재사용한다.
from naver_smartstore import normalize_price_1kg  # noqa: E402

BASE = 'https://smartstore.naver.com'

# 페이지 컨텍스트에서 실행할 JS — 채널ID 조회 후 상품 목록을 페이지네이션으로 모은다.
# 스토어 프론트가 쓰는 것과 동일한 내부 API 를 그 페이지의 세션으로 호출하므로 통과한다.
_JS = r"""
async ({storeId, category}) => {
  const base = 'https://smartstore.naver.com';
  const j = async (u) => (await fetch(u, {headers:{Accept:'application/json'},
                                          credentials:'include'})).json();
  const info = await j(`${base}/i/v1/smart-stores?url=${storeId}`);
  const chid = info && info.id;
  if (!chid) return {error: 'no_channel', keys: Object.keys(info||{})};
  const ctype = category === 'ALL' ? 'STDCATG' : 'DISPCATG';
  let page = 1, out = [], total = 0, guard = 0;
  while (guard++ < 50) {
    const data = await j(`${base}/i/v2/channels/${chid}/categories/${category}/products`
      + `?categorySearchType=${ctype}&sortType=TOTALSALE&page=${page}&pageSize=40`);
    const prods = (data && (data.simpleProducts || data.products)) || [];
    total = (data && data.totalCount) || 0;
    for (const p of prods) out.push(p);
    if (page*40 >= total || prods.length === 0) break;
    page++;
  }
  return {total, products: out};
}
"""


def fetch_products_browser(store_id, category='ALL', landing_url=None, headless=True):
    """실제 브라우저로 스토어를 열고, 페이지 안에서 내부 API 를 호출해 상품을 모은다.

    → [{'name','price','url','is_soldout'}]
    landing_url: 먼저 방문할 페이지(해당 카테고리 URL 권장). 없으면 스토어 홈.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            'playwright 가 설치돼 있지 않습니다. 먼저:\n'
            '    python3 -m pip install playwright\n'
            '    python3 -m playwright install chromium')

    landing = landing_url or f'{BASE}/{store_id}'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            locale='ko-KR',
            user_agent=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/124.0.0.0 Safari/537.36'),
            viewport={'width': 1280, 'height': 900},
        )
        page = ctx.new_page()
        # 실제 페이지를 먼저 띄워 세션·쿠키를 확립한다. networkidle 은 네이버 트래커
        # 때문에 안 끝날 수 있어 domcontentloaded + 짧은 대기로 쿠키만 확보한다.
        page.goto(landing, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(2000)
        result = page.evaluate(_JS, {'storeId': store_id, 'category': category})
        browser.close()

    if not isinstance(result, dict) or result.get('error'):
        raise RuntimeError(f'{store_id}: 브라우저 수집 실패 — {result}')

    raw = result.get('products') or []
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
    print(f'  브라우저 수집: {len(items)}개 (API total {result.get("total")})')
    return items


if __name__ == '__main__':
    # 단독 테스트: python3 scrapers/naver_smartstore_browser.py <storeId> [category]
    sid = sys.argv[1] if len(sys.argv) > 1 else 'ruberroastery'
    cat = sys.argv[2] if len(sys.argv) > 2 else 'ALL'
    for it in fetch_products_browser(sid, cat):
        print(f"  {it['price']}원 {'[품절]' if it['is_soldout'] else ''} {it['name'][:55]}  {it['url']}")
