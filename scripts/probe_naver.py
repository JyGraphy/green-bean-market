"""[임시] 네이버 스마트스토어 Playwright 프로브 — GitHub Actions 러너에서 실행.

requests는 429로 차단됨. 실제 브라우저로 상점 페이지가 열리는지,
__PRELOADED_STATE__와 페이지 내 fetch로 상품 API 접근이 되는지 확인한다.
확인 후 삭제 예정.
"""
import json
from playwright.sync_api import sync_playwright

RUBER_CAT_A = '8ae390149e7b4d428507d79d4c1818c8'  # 사용자 제공 href
RUBER_CAT_B = '60dc93d44b0e477c91b84a18aaefc200'  # 사용자 제공 링크 텍스트

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        locale='ko-KR',
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    )
    page = ctx.new_page()

    for store in ('amativo', 'ruberroastery'):
        print(f"\n===== {store} =====")
        resp = page.goto(f'https://smartstore.naver.com/{store}', wait_until='domcontentloaded', timeout=45000)
        print('page status:', resp.status if resp else None, '| title:', page.title())
        if resp and resp.status != 200:
            print('body head:', page.content()[:300].replace('\n', ' '))
            continue
        page.wait_for_timeout(2500)

        state = page.evaluate("() => window.__PRELOADED_STATE__ ? Object.keys(window.__PRELOADED_STATE__) : null")
        print('state keys:', state)
        ch = page.evaluate("""() => {
            const s = window.__PRELOADED_STATE__;
            if (!s) return null;
            const ch = (s.smartStoreV2 && s.smartStoreV2.channel) || (s.smartStore && s.smartStore.channel) || null;
            return ch ? {id: ch.id, channelNo: ch.channelNo, name: ch.channelName || ch.name, uid: ch.channelUid} : Object.keys(s);
        }""")
        print('channel:', json.dumps(ch, ensure_ascii=False))

        chid = ch.get('id') if isinstance(ch, dict) else None
        if not chid:
            continue

        cats = [('ALL', 'STDCATG')]
        if store == 'ruberroastery':
            cats += [(RUBER_CAT_A, 'DISPCATG'), (RUBER_CAT_B, 'DISPCATG')]
        for cat, ctype in cats:
            api = (f'https://smartstore.naver.com/i/v2/channels/{chid}/categories/{cat}'
                   f'/products?categorySearchType={ctype}&sortType=TOTALSALE&page=1&pageSize=40')
            out = page.evaluate("""async (url) => {
                const r = await fetch(url, {headers: {accept: 'application/json'}});
                const t = await r.text();
                return {status: r.status, body: t.slice(0, 2000)};
            }""", api)
            print(f'\n--- cat={cat} ({ctype}) → {out["status"]}')
            print('body:', out['body'][:1800])

        # 카테고리 목록 (루베르 생두 카테고리 확인용)
        catapi = page.evaluate("""async (chid) => {
            const r = await fetch(`https://smartstore.naver.com/i/v1/channels/${chid}/categories?withSpecialProducts=true`, {headers: {accept: 'application/json'}});
            return {status: r.status, body: (await r.text()).slice(0, 1500)};
        }""", chid)
        print(f'\n--- categories api → {catapi["status"]}')
        print('body:', catapi['body'])

    browser.close()

print('\nDONE')
