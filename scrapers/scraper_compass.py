"""콤파스커피 생두 스크래퍼 — Sixshop (JS렌더링) Playwright 사용
URL: https://compasscoffee.kr/greencoffee
"""
import re, json, time, sys, os
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from common import *

STORE = '콤파스커피'
BASE  = 'https://compasscoffee.kr'
URL   = BASE + '/greencoffee'

def scrape_playwright():
    from playwright.sync_api import sync_playwright
    from bs4 import BeautifulSoup

    print(f"[{STORE}] Playwright 시작...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.goto(URL, wait_until='networkidle', timeout=30000)
        time.sleep(3)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    items = []
    seen = set()

    for a in soup.select('a[href*="/product/"]'):
        href = a.get('href', '')
        if href in seen:
            continue
        seen.add(href)

        text = a.get_text(strip=True)
        # 상품명: 가격 앞 부분 (예: "New[생두] 에티오피아 예가체프 콩가 G2 워시드18,500원장바구니에 담기")
        # 가격 패턴으로 분리
        m = re.search(r'^(.*?)([\d,]+)원', text)
        if not m:
            continue
        name_raw = m.group(1).strip()
        price = int(m.group(2).replace(',', ''))
        if price < 1000:
            continue

        # 이름 정리: New, [생두] 등 접두어 제거
        name = re.sub(r'^New\s*', '', name_raw, flags=re.IGNORECASE).strip()
        name = re.sub(r'^\[생두\]\s*', '', name).strip()
        if not name or len(name) < 3:
            continue

        url = BASE + href if href.startswith('/') else href
        items.append({'name': name, 'price': price, 'url': url})

    print(f"[{STORE}] 총 {len(items)}개")
    return items

if __name__ == '__main__':
    try:
        items = scrape_playwright()
    except ImportError:
        print("❌ playwright 미설치. 실행: pip install playwright && playwright install chromium")
        sys.exit(1)

    root = os.path.join(os.path.dirname(__file__), '..')
    with open(os.path.join(root, 'data', 'products.json'), encoding='utf-8') as f:
        data = json.load(f)
    kept = [p for p in data['products'] if p['store'] != STORE]
    existing_ids = {p['id'] for p in kept}
    id_start = 351
    while id_start in existing_ids: id_start += 1
    update_json(STORE, to_products(items, STORE, id_start))
