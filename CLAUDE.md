# 생두 가격 비교 사이트 (Korean Green Bean Marketplace)

한국 주요 생두 쇼핑몰의 상품을 한 페이지에서 가격·원산지·가공방식으로 비교하는 정적 웹사이트.

## 파일 구조

```
coffeebeanweb/
├── index.html    # HTML 구조 (146줄) — <link>/<script src> 참조만 포함
├── styles.css    # 전체 CSS (358줄) — CSS 변수, 레이아웃, 배지, 반응형
├── data.js       # 상품 데이터 + 상수 (574줄) — PRODUCTS 배열, FLAG, STORE_CLS 등
└── app.js        # 앱 로직 (235줄) — 필터링, 렌더링, 정렬, 페이지네이션
```

## 상품 데이터 스키마

```js
{
  id: Number,           // 고유 ID (1~845 범위, 연속하지 않아도 됨)
  store: String,        // 공급사 이름 (STORE_CLS 키와 일치해야 함)
  name: String,         // 상품명
  price: Number,        // 1kg 기준 가격 (원)
  origin: String,       // 원산지 (FLAG 키와 일치)
  region: String,       // '아프리카' | '중남미' | '아시아' 등
  notes: String,        // 컵노트 (없으면 '' 또는 생략)
  url: String,          // 구매 링크
  isNew: Boolean,       // 2026 수확 신상품 여부
  isDecaf: Boolean,     // 디카페인 여부
  isSpecial: Boolean,   // 스페셜티 여부 (게이샤, 파카마라, 고가 희귀 품종 등)
  // process 필드는 extractProcess()가 자동 주입 — 직접 지정도 가능
}
```

### isNew 판별 기준
- 상품명에 "2026" 포함 (예: 커피리브레 케냐 2026 수확)
- 상품명에 "-26CROP-" 포함 (블레스빈 명명 규칙)
- 기타 쇼핑몰은 "2025/26", "2025/2026" 등 명시 시 `true`

### isSpecial 판별 기준
- 품종명: 게이샤, 파카마라, 자바, SL28, SL34 등 희귀 품종
- 가격이 50,000원/kg 이상인 고가 상품
- 상품명이나 노트에 "게이샤", "파카마라", "에스메랄다" 등 포함

## 12개 공급사 현황

| 공급사 | CSS 클래스 | 색상 | 상품 수 | URL |
|--------|-----------|------|---------|-----|
| 커피플랜트 | sp-cp | #dc2626 | 53 | coffeeplant.co.kr |
| 커피창고 | sp-cg | #16a34a | 16 | thecoffeehouse.co.kr |
| 엠아이커피 | sp-mi | #1d4ed8 | 33 | micoffee.co.kr |
| 모모스커피 | sp-momos | #c2410c | 55 | momos.co.kr |
| 코빈즈커피 | sp-cobeans | #0284c7 | 69 | cobeans.com |
| 아얀투 | sp-ayantu | #7c3aed | 13 | ayantu.co.kr |
| 오로미아코리아 | sp-oromia | #b45309 | 9 | oromiakorea.com |
| 지에스씨(GSC) | sp-gsc | #0d9488 | 6 | gsc.coffee |
| 오월의숲 | sp-mayforest | #15803d | 37 | mayforest.kr |
| 커피리브레 | sp-cl | #d97706 | 77 | coffeelibre.kr |
| 블레스빈 | sp-bb | #0e7490 | 84 | blessbean.co.kr |
| 콤파스커피 | sp-compass | #be185d | 48 | compasscoffee.kr |

**총 500개 상품, ID 범위 1~845**

## 가공방식 자동 추출 (`extractProcess`)

`data.js`의 `extractProcess(name)` 함수가 상품명 정규식으로 가공방식을 분류:

| 리턴값 | CSS 클래스 | 키워드 예시 |
|--------|-----------|------------|
| 워시드 | proc-washed | 워시드, washed |
| 내추럴 | proc-natural | 내추럴, natural, 레포사도 |
| 허니 | proc-honey | 허니, honey, 레드허니, 화이트허니 |
| 무산소발효 | proc-anaerobic | 무산소, anaerobic, 카보닉, 인퓨즈드 |
| 펄프드내추럴 | proc-pulped | 펄프드내추럴, pulped natural |
| 웻훌드 | proc-wethulled | 웻훌, wet hul |
| 알수없음 | proc-unknown | 위 패턴 미매칭 |

## 원산지 국기 (FLAG)

에티오피아 🇪🇹, 케냐 🇰🇪, 탄자니아 🇹🇿, 르완다 🇷🇼, 세인트헬레나 🌍, 브라질 🇧🇷, 콜롬비아 🇨🇴, 과테말라 🇬🇹, 코스타리카 🇨🇷, 파나마 🇵🇦, 엘살바도르 🇸🇻, 온두라스 🇭🇳, 멕시코 🇲🇽, 자메이카 🇯🇲, 페루 🇵🇪, 인도네시아 🇮🇩, 인도 🇮🇳, 베트남 🇻🇳, 하와이 🌺, 볼리비아 🇧🇴, 에콰도르 🇪🇨, 예멘 🇾🇪, 중국 🇨🇳, 파푸아뉴기니 🇵🇬, 니카라과 🇳🇮, 우간다 🇺🇬, 콩고민주공화국 🇨🇩

## 새 공급사 추가 방법

1. **`styles.css`**: `:root` 블록에 `--store-XXX: #색상;` 추가, `.sp-XXX` 배지 CSS 추가
2. **`index.html`**: 공급사 필터 버튼, 사이드바 범례 색상 도트 추가, 헤더 쇼핑몰 수 업데이트
3. **`data.js`**: `STORE_CLS`에 `'공급사명':'sp-XXX'` 추가, PRODUCTS 배열에 상품 추가

## 데이터 안전장치 (스크래핑 사고 방지)

매일 자동 갱신 시 데이터가 사라지거나 깨지는 것을 막는 다층 방어 구조.
**새 스크래퍼를 추가할 때 아래 규칙을 반드시 따를 것.**

1. **빈/부분 결과 보존** — 저장 직전 `common.guard_store_replacement(store, old_count, new_count)`를
   호출한다. 수집 0개거나 기존 대비 50% 미만 급감이면 `SystemExit(1)`로 기존 데이터를 보존한다.
   `common.update_json()`은 이미 내장. 자체 저장 로직을 쓰면 직접 호출해야 한다.
2. **ID 충돌 방지** — ID는 반드시 `common.alloc_ids(count, id_start, taken=existing_ids)` 또는
   `to_products(items, store, id_start, existing_ids)`로 발급한다. `id_start + i` 순차 부여는
   다른 store 구간과 겹쳐 중복 ID를 만든다(금지).
3. **비생두 품목 차단** — `to_products()`는 `common.is_non_bean(name)`으로 장비·서적·굿즈·
   결제·깨진 이름(예: 'SOLD OUT') 등을 자동 제외한다. 패턴은 `_NON_BEAN_PATTERNS`에 있으며,
   정상 생두명과 충돌 0건이 검증된 정밀 키워드만 추가할 것('컵','잔','세트','스틱' 등 금지).
4. **검증 게이트** — `scripts/validate_data.py`가 커밋 직전 워킹트리를 직전 커밋(HEAD)과 비교해
   스키마·중복ID·store 소멸·급감을 검사한다. 실패 시 워크플로가 커밋을 차단한다.
   의도적 대량 변경은 `FORCE_DATA_UPDATE=1`로 급감 검사만 우회(스키마·중복 검사는 유지).
5. **워크플로 동작** — 개별 스크래퍼 실패는 격리(`continue-on-error`)되어 정상 store는 커밋되고,
   실패/검증불가 시 잡이 빨간 X로 표시된다.

## 스크래핑 플랫폼 메모

| 플랫폼 | 스크래핑 방법 |
|--------|-------------|
| cafe24 / godomall | 서버 렌더링 → `web_fetch` 또는 curl로 직접 스크래핑 가능 |
| Sixshop | 클라이언트 렌더링 → Chrome MCP `javascript_tool` 필요 |
| aram (블레스빈) | 서버 렌더링 → `web_fetch` 가능 |

- 콤파스커피 Sixshop store ID: `224244`

## 향후 추가 가능 공급사

조사가 필요한 생두 전문 쇼핑몰 목록 (아직 미추가):
- wbeans.com (접근 불가 확인됨 — 클라이언트 렌더링/차단)
- 추가 조사 필요 업체들은 별도 확인 후 추가
