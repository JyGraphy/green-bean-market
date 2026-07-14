"""[임시] 네이버 스마트스토어 API 프로브 — GitHub Actions 러너에서 실행.

아마티보/루베르로스터리 스크래퍼 작성을 위해 러너 IP에서 접근 가능한
엔드포인트와 응답 구조를 확인한다. 확인 후 삭제 예정.
"""
import json
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Referer': 'https://smartstore.naver.com/',
}

RUBER_CAT_A = '8ae390149e7b4d428507d79d4c1818c8'  # 사용자 제공 href
RUBER_CAT_B = '60dc93d44b0e477c91b84a18aaefc200'  # 사용자 제공 링크 텍스트


def show(label, url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        print(f"\n### {label}\nGET {url}\n→ {r.status_code}, {len(r.content)}B, ct={r.headers.get('content-type','')}")
        if r.status_code != 200:
            print(r.text[:300].replace('\n', ' '))
            return None
        if 'json' in r.headers.get('content-type', ''):
            data = r.json()
            print('keys:', list(data.keys())[:30] if isinstance(data, dict) else f'list[{len(data)}]')
            return data
        # HTML이면 __PRELOADED_STATE__ 존재 여부만
        print('__PRELOADED_STATE__ in html:', '__PRELOADED_STATE__' in r.text)
        return r.text
    except Exception as e:
        print(f"\n### {label}\nGET {url}\n→ EXC {e}")
        return None


for store in ('amativo', 'ruberroastery'):
    info = show(f'{store} v1 store info', f'https://smartstore.naver.com/i/v1/smart-stores?url={store}')
    if isinstance(info, dict):
        print('store info sample:', json.dumps({k: info.get(k) for k in ('id', 'channelNo', 'name', 'url', 'representativeYn')}, ensure_ascii=False))
        chid = info.get('id')
        if chid:
            for cat, ctype in (('ALL', 'STDCATG'), (RUBER_CAT_A, 'DISPCATG'), (RUBER_CAT_B, 'DISPCATG')):
                if store == 'amativo' and cat != 'ALL':
                    continue
                data = show(
                    f'{store} products cat={cat}',
                    f'https://smartstore.naver.com/i/v2/channels/{chid}/categories/{cat}/products?categorySearchType={ctype}&sortType=TOTALSALE&page=1&pageSize=40')
                if isinstance(data, dict):
                    prods = data.get('simpleProducts') or data.get('products') or []
                    print('totalCount:', data.get('totalCount'), '| first page:', len(prods))
                    if prods:
                        print('product sample:', json.dumps(prods[0], ensure_ascii=False)[:1500])
    # 카테고리 목록도 확인 (루베르 생두 카테고리 이름 매칭용)
    show(f'{store} categories', f'https://smartstore.naver.com/i/v1/categories?url={store}')

print('\nDONE')
