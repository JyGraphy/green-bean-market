# 로스팅 프로파일 출처 카탈로그 (SOURCES.md)

- 작성일: 2026-08-02
- 작성 방법: **WebSearch 전용 조사**. 이 실행 환경은 WebFetch / curl이 전 사이트에서 403으로 차단되어
  본문 접근이 불가능했다. 따라서 아래 내용은 **검색 결과 요약 수준에서 확인된 사실**만 담았고,
  **곡선 수치(t/temp/ROR)는 단 한 건도 수집하지 않았다.**
- 원칙: 추정한 곡선을 저장하는 것은 학습 데이터 오염이므로 금지. 본 문서는 "네트워크가 열리면
  즉시 수집을 시작할 수 있는 지도"다.
- 표기 규칙:
  - `확인 필요` = 검색 요약만으로는 단정할 수 없어 본문 확인이 필요한 항목
  - `직접 확인 필요` = 로그인/유료/기기 소유 뒤에 있어 내용 저장이 불가능한 항목
  - 아래 "라이선스" 칸은 **모두 추정치**다. 실제 수집 전 반드시 해당 사이트의 이용약관을 읽고
    재배포 가능 여부를 재확인할 것.

---

## 1. 핵심 요약 — 가장 유망한 출처 3곳

1. **Artisan(오픈소스) 생태계 + Roastetta** — Artisan은 GPL 계열 오픈소스이며 `.alog`(JSON 기반)가
   사실상 업계 공용 교환 포맷이다. Roastetta(roastetta.com)는 **로그인 없이 공개 조회 가능한 개별
   로스트 상세 URL**을 제공하는 것으로 보여, 파싱 대상으로 구조가 가장 명확하다.
2. **ROEST 공개 프로파일 라이브러리 (front.roestcoffee.com/profilelibrary)** — 제조사가 운영하는
   **명시적 "Public" 라이브러리**다. 원산지·가공방식 메타데이터가 필터로 붙어 있어 스키마의
   `bean` 필드를 채우기에 가장 적합하다.
3. **학술 공개 데이터셋(Data in Brief / Mendeley Data / TU Wien 리포지터리)** — 유일하게
   **CC BY 등 재배포 라이선스가 문서로 확정되는** 계열이다. 건수는 적지만 데이터 신뢰도와
   법적 안전성이 가장 높아 "정답 기준(gold set)"으로 쓸 가치가 크다.

> 반대로 IKAWA Online Library, Roast.World, Cropster, Stronghold Square는 **기기 소유자 로그인
> 뒤**에 있어 이번 원칙상 내용 저장 대상이 아니다(URL만 기록).

---

## 2. 출처 카탈로그 표

| # | 출처 | 기계/대상 | 데이터 형태 | 공개 범위 | 라이선스(추정) | 로그인 필요? | 우선순위 |
|---|------|-----------|-------------|-----------|----------------|--------------|----------|
| 1 | Roastetta (roastetta.com) | Artisan 지원 전 기종 | `.alog` 업로드본, 인터랙티브 차트, 로스트 상세 페이지 | 공개 URL로 개별 로스트 조회 가능(추정) | 업로더 개인 저작물 · 재배포 조건 `확인 필요` | 조회는 불필요(추정) | ★★★★★ |
| 2 | ROEST 공개 프로파일 라이브러리 (front.roestcoffee.com/profilelibrary) | ROEST S100/L100/L200 샘플로스터 | 프로파일 파일 + 원산지·가공 메타데이터 | 제조사 명시 "public library" | 제조사 배포물 · `확인 필요` | 다운로드는 계정 필요 가능성 `확인 필요` | ★★★★★ |
| 3 | 학술 데이터셋 (Data in Brief, Mendeley Data, Zenodo/Figshare) | 실험용 로스터(파일럿·유동층 등) | Excel/CSV 부록, 시계열 | 완전 공개 | 다수 **CC BY 4.0**(논문별 확인) | 불필요 | ★★★★★ |
| 4 | Artisan 공식 리포/문서 (github.com/artisan-roaster-scope/artisan, artisan-scope.org) | 전 기종 | `.alog` 스키마(`src/artisan-alog.xml`), CSV/JSON 내보내기 규격, 변환기 문서 | 완전 공개 | 오픈소스(GPL 계열, SPDX `확인 필요`) | 불필요 | ★★★★★ (포맷 지식) |
| 5 | TU Wien 학위논문 "Analysis of Time Series Data and Optimization of Coffee Roasting" (repositum.tuwien.at) | 상업용 로스터(시계열) | PDF + 부록 데이터 `확인 필요` | 기관 리포지터리 공개 PDF | 대학 리포지터리 라이선스 `확인 필요` | 불필요 | ★★★★ |
| 6 | Sweet Maria's Coffee Library (library.sweetmarias.com) | Popper 등 가정용 + ROEST | 개별 커피별 **Artisan 로그 공개 게시글** | 공개 블로그 | 상업 사이트 저작물 · 재배포 금지 가능성 높음 `확인 필요` | 불필요 | ★★★★ |
| 7 | Kaffelogic 프로파일 페이지 + 커뮤니티 (kaffelogic.com/pages/profiles, community.kaffelogic.com) | Kaffelogic Nano 7 | `.kpro`(프로파일) / `.klog`(로그) 파일 첨부 | 공식 12 core 프로파일 + 포럼 첨부 | 공식 배포물 · 포럼은 개인 저작물 `확인 필요` | 포럼 첨부 다운로드에 계정 필요 가능성 | ★★★★ |
| 8 | Royal Coffee 로스팅 교육 블로그 (royalcoffee.com) | IKAWA Pro | 프로파일 설명 + IKAWA 앱 링크(딥링크) | 공개 블로그 | 회사 저작물 · 재배포 `확인 필요` | 프로파일 적용엔 IKAWA 앱 필요 | ★★★ |
| 9 | home-barista.com 로스팅 포럼 (다수 스레드) | Artisan/IKAWA/Bullet 등 | 포럼 첨부 `.alog`, 스크린샷 그래프 | 공개 포럼 | 개인 저작물 · 재배포 금지 가능성 `확인 필요` | 첨부 다운로드에 계정 필요 가능성 | ★★★ |
| 10 | jglogan/roastime-data (GitHub) | Aillio Bullet | RoasTime 데이터 분석 도구(코드) | 공개 리포 | 오픈소스 `확인 필요` | 불필요 | ★★★ (포맷 지식) |
| 11 | themcclure/bullet-time (GitHub) | Aillio Bullet | RoasTime/Roast.World 유틸리티 | 공개 리포 | 오픈소스 `확인 필요` | 불필요 | ★★★ (포맷 지식) |
| 12 | jacciz/coffee_roasting_profiles (GitHub) | Artisan 사용 기종 | `.alog` 임포트 Shiny 대시보드 (+개인 로스트 데이터 포함 가능성) | 공개 리포 | 오픈소스 `확인 필요` | 불필요 | ★★★ |
| 13 | nkraetzschmar/libikawa (GitHub) | IKAWA Home | IKAWA 통신 프로토콜 오픈소스 구현 | 공개 리포 | 오픈소스 `확인 필요` | 불필요 | ★★★ (포맷/프로토콜 지식) |
| 14 | Roastero/Openroast (GitHub) | FreshRoast SR700 | 오픈소스 로스팅 앱, 레시피/프로파일 포맷 | 공개 리포 | **GPL v3** (검색 확인) | 불필요 | ★★★ (포맷 지식) |
| 15 | RoastLink 변환기 (converter.roastlink.com) | Aillio Bullet → Artisan | Roast.World JSON → Artisan CSV 변환 | 공개 웹툴 | 서비스 약관 `확인 필요` | 불필요(입력은 Roast.World ID) | ★★★ (포맷 지식) |
| 16 | Loring 도움말 (loring.com/helpfiles/RA/RoastProfile.html) | Loring Smart Roast | 프로파일 개념·Anchor Point 구조 기술문서 | 공개 헬프페이지 | 제조사 저작물 · 재배포 금지 추정 | 불필요 | ★★ (개념 지식) |
| 17 | IKAWA Roast Profile Library (ikawacoffee.com/pro-sample-roaster-profiles) + 앱 Online Library | IKAWA Pro 50/100 | 프로파일(앱 내), 로스트 로그 CSV 내보내기 | 웹 페이지는 공개, 실제 프로파일은 앱 내부 | 재배포 조건 미확인 | **예 — 앱/계정 필요** | ☆ 기록만 (직접 확인 필요) |
| 18 | Roast.World (roast.world) + 커뮤니티 | Aillio Bullet R1/R2, AiO | 로스트 JSON, 메타데이터 API | 프로파일 공유 기능 존재 | 사용자 저작물 · 재배포 조건 미확인 | **예 — Aillio 계정 필요** | ☆ 기록만 (직접 확인 필요) |
| 19 | Stronghold Square (stronghold.coffee) | Stronghold S7 PRO / S9 / S9X | 프로파일 공유 플랫폼 | 열람은 무료, **업/다운로드는 기기 소유자 한정** | 재배포 금지 추정 | **예 — 기기 소유자 계정** | ☆ 기록만 (직접 확인 필요) |
| 20 | Cropster (help.cropster.com, cropster.com API) | 산업용 전반 | 프로파일 내보내기, 유료 API | 고객 전용 | **상업 라이선스 · 재배포 불가 추정** | **예 — 유료 고객 계정** | ☆ 기록만 (직접 확인 필요) |
| 21 | Probat Pilot 2020 / PILOT Roaster Shop (probat.com) | PROBATONE 등 | 레시피·아카이브 포맷(Artisan이 v1.4 임포트 지원) | 제품 페이지만 공개 | **상업 라이선스** | 예 (소프트웨어 소유) | ☆ 기록만 (직접 확인 필요) |
| 22 | RoastPATH (portal.roastpath.com) | US Roaster Corp | masterpath 프로파일 | 포럼 일부 공개 | `확인 필요` | 포럼 계정 필요 가능성 | ☆ 기록만 |

---

## 3. 출처별 짧은 설명

### 1) Roastetta — 최우선 타깃
Artisan `.alog` 파일을 업로드해 차트로 보고 공유·피드백 받는 웹앱. "Roast World for Aillio의
Artisan 판"으로 소개된다. 로스트별 상세 URL과 QR 코드를 제공하고, 태그/로스트레벨/원산지/
로스터 타입 필터가 있다.
- **가져오는 법(가설)**: 목록 → 개별 로스트 상세 URL → 차트 데이터(내부 JSON) 파싱.
- **조심할 점**: 업로드본은 **각 업로더의 저작물**이다. 사이트 약관에 재배포 허용 문구가 없으면
  `source_url`만 기록하고 곡선은 저장하지 않는 편이 안전하다. 수집 전 약관 확인 필수.
- **아직 미확인**: 로그인 없이 API/JSON에 접근되는지, robots.txt가 크롤링을 허용하는지.

### 2) ROEST 공개 프로파일 라이브러리
제조사(ROEST)가 웹 포털에 만든 명시적 공개 라이브러리. 프로파일 생성 시 설명·원산지·가공방식
메타데이터를 붙이게 되어 있어 필터 검색이 된다. Tim Wendelboe, Scott Rao, Matt Winton 등
유명 로스터의 프로파일이 포럼을 통해 공유되었다고 보도됨.
- **조심할 점**: "공개 라이브러리"라는 표현이 곧 재배포 허용은 아니다. 또한 유명 로스터 이름이
  붙은 프로파일은 저작·상표 이슈 가능성이 있으니 특히 보수적으로 다룰 것.
- **아직 미확인**: 다운로드에 ROEST 계정이 필요한지, 프로파일 파일 확장자와 내부 구조.

### 3) 학술 공개 데이터셋 — 법적으로 가장 안전
검색으로 확인된 후보:
- *Adsorption isotherms in roasted specialty coffee (Coffea arabica L.)* — 부록에
  **"roasting curves of specialty coffee" Excel 파일**이 포함된다고 기술됨 (PMC11748726).
  Data in Brief 계열이면 통상 CC BY 4.0.
- *Development of coffee bean porosity and thermophysical properties during roasting* —
  흡기온도 220/235/250/265/280°C, 배치 200/350/500 g 조건별 **time–temperature 프로파일**을
  측정했다고 기술됨. 다만 저널이 Elsevier 유료일 수 있어 `확인 필요`.
- Mendeley Data / Zenodo / Figshare에서 "coffee roasting profile", "roast curve" 직접 검색 필요.
- **조심할 점**: 논문 데이터는 대부분 **실험실 로스터**라 상업 드럼로스터 곡선과 특성이 다르다.
  `machine` 필드에 실험 장비명을 정확히 적고, notes에 "실험실 조건"임을 반드시 명시.

### 4) Artisan 공식 리포지터리 — 포맷 지식의 원천
`src/artisan-alog.xml`(파일타입 정의)과 소스 코드가 공개되어 있다. Artisan은 Cropster,
Probat Pilot 1.4, RoastLogger, IKAWA CSV/URL 등 **다수 외부 포맷의 임포터**를 내장하고 있어,
그 임포터 소스 코드 자체가 각 벤더 포맷의 사실상 문서다.
- **가져오는 법**: 네트워크가 열리면 `git clone` 후 `src/` 내 import/export 모듈을 직접 읽는 것이
  가장 확실하다. (현재 환경엔 `gh`도 없고 curl도 403이라 불가)
- **조심할 점**: 리포에 포함된 샘플 프로파일이 실제 로스트인지 테스트용 더미인지 구분해야 한다.

### 5) Sweet Maria's Coffee Library
개별 생두 상품마다 Artisan 로그를 붙인 게시글이 존재한다(예: Ethiopia Dry Process Hambela Goro,
Popper 로스터). 로스터가 직접 공개한 데이터라 신뢰도는 높다.
- **조심할 점**: 상업 사이트 콘텐츠다. 그래프 이미지에서 값을 읽는 경우 `source_type`에
  `+chart-read`를 붙이고 판독 오차를 notes에 명시해야 한다. 대량 크롤링은 하지 말 것.

### 6) Kaffelogic
공식 12 core 프로파일(Wayne Burrows 제작)과 커뮤니티 포럼 첨부(`.kpro`, `.klog`)가 있다.
Artisan CSV 임포트, IKAWA 임포트 관련 스레드도 존재해 포맷 상호변환 정보의 창구가 된다.
- **조심할 점**: 공식 프로파일은 제품 부속물이라 재배포 조건이 별도일 가능성이 높다.

### 7) 로그인/유료 뒤 출처 — **내용 저장 금지, URL만 기록**
- **IKAWA Online Library**: 앱 햄버거 메뉴 → Online Library. 로스트 히스토리 공유 시
  color change, first crack, DTR, RoR 그래프, **초 단위 로스트 데이터 CSV**, 사진, 노트가
  함께 공유된다고 안내됨. 프로파일 공유는 이메일/SMS/링크 방식.
  → 실제 데이터는 앱 내부. **직접 확인 필요.**
- **Roast.World / RoasTime**: 다른 사용자의 프로파일을 발견해 자기 RoasTime으로 내려받아
  재생할 수 있다. settings에서 feature preview를 켜면 API가 보이지만,
  **API는 메타데이터만 주고 로그 데이터 포인트는 주지 않는다**는 커뮤니티 답변이 있다.
  CSV 내보내기는 기능 요청 스레드가 오래 이어져 온 것으로 보아 이력상 제한적이었다.
  → **직접 확인 필요.**
- **Stronghold Square**: 플랫폼 열람은 무료지만 **업/다운로드는 S7 PRO·S9 소유자 한정**.
  → **직접 확인 필요.**
- **Cropster / Probat Pilot**: 상업 소프트웨어. 고객 계정 내보내기 또는 유료 API.
  재배포 불가로 간주. → **직접 확인 필요.**

---

## 4. 데이터 포맷 메모

> 아래는 **검색 결과에서 확인된 범위**만 적은 것이다. 본문 접근이 막혀 스키마를 직접 검증하지
> 못했으므로, 실제 파서를 짜기 전에 반드시 실물 파일 1개로 검증할 것.

### `.alog` (Artisan Roast Profile)
- JSON "기반"이지만 **엄격한 JSON이 아니다.** Artisan 이슈 #219가 제목부터
  "poor JSON implementation"이고, 기본 문법 규칙이 여럿 지켜지지 않는다고 지적한다.
  → **표준 `json.loads()`로 바로 파싱되지 않을 수 있다.** Python `ast.literal_eval` 계열이나
  Artisan 자체 로더를 참고해야 할 가능성이 높다. **파서 작성 시 최우선 검증 항목.**
- 파일타입 정의는 리포의 `src/artisan-alog.xml`.
- 저장된 `.alog`와 내보낸 CSV의 값이 다를 수 있다는 이슈(#85)가 있다 → **둘 중 무엇을 원본으로
  볼지 정해야 한다.** 우리 스키마 notes에 어느 쪽에서 읽었는지 반드시 기록.

### Artisan CSV export
- 컬럼: `Time`, `Time1`, `Time2`, `BT`, `ET`, `Event` (검색 요약 기준, `확인 필요`)
  - `BT` = Bean Temperature(원두 온도), `ET` = Environmental Temperature(환경/배기 온도)
  - `Event`에 `Charge` 등 이벤트 마커가 들어간다
- 구분자가 **탭**이라는 언급이 있다(수동 작성 안내 기준). 확장자는 `.csv`지만 TSV일 수 있음
  → 파싱 시 sniffing 필요.
- 우리 스키마 매핑 제안: `curve[].temp_c` ← **BT**를 기본으로 하고, ET는 notes 또는 별도 필드로.
  어느 쪽을 썼는지 notes에 반드시 명시.

### Artisan 내보내기 지원 포맷
Excel, Probat Pilot 1.4, Artisan CSV, Artisan JSON, RoastLogger. 임포트 쪽은 Cropster,
IKAWA(CSV 및 IKAWA URL), Aillio 등 더 넓다. → **Artisan을 허브로 삼아 모든 벤더 포맷을
`.alog`/CSV로 정규화하는 전략**이 가장 현실적이다.

### IKAWA
- **로스트 로그**는 초 단위 CSV로 내보낼 수 있다("each second of the roast in CSV").
- **프로파일**(설정값 곡선)과 **로스트 로그**(실측)는 별개다. Artisan 문서에 따르면
  **IKAWA CSV는 로스트 로그에서만 생성**되고, 프로파일은 **IKAWA URL** 형태로 공유된다.
  → 우리 스키마의 `curve`에는 **로스트 로그(실측)**만 넣어야 한다. 프로파일(목표 곡선)을
  실측처럼 저장하면 학습 데이터 오염이다. **이 구분이 매우 중요.**
- exhaust 프로파일(빨간 선)은 모든 IKAWA Pro 기종 호환, inlet 프로파일(노란 선)은
  **배치 사이즈가 다르면 호환되지 않는다.** → `batch_size_g` 기록이 필수.
- 프로토콜 오픈소스 구현: `nkraetzschmar/libikawa` (IKAWA Home 대상).

### Aillio Bullet / RoasTime / Roast.World
- Roast.World에서 로스트를 **JSON**으로 내려받을 수 있다.
- 그 JSON은 **Artisan이 그대로 임포트하지 못한 이력**이 있다(이슈 #508) → 변환 필요.
- 변환 경로: RoastLink(`converter.roastlink.com`)가 Roast.World ID/URL → Artisan CSV 변환.
  ET/BT 스왑 옵션이 있다 → **온도 채널이 뒤바뀔 수 있다는 뜻.** 수집 시 BT/ET 라벨을 맹신하지 말고
  값의 물리적 타당성(BT가 ET보다 낮게 시작하는지 등)을 검증할 것.
- 참고 도구: `jglogan/roastime-data`, `themcclure/bullet-time`.

### Kaffelogic
- `.kpro` = 프로파일, `.klog` = 로스트 로그로 보인다(포럼 첨부 파일명 기준, `확인 필요`).
  IKAWA와 마찬가지로 **프로파일/로그 구분**에 주의.

### Loring
- 프로파일 = Bean Temperature 곡선을 **Anchor Point(시간·온도 쌍)** 로 정의한 것.
  즉 조밀한 시계열이 아니라 **희소한 제어점**이다. 우리 `curve` 스키마에 그대로 넣으면
  실측 곡선과 성격이 다르므로, 넣는다면 notes에 "anchor points, 실측 아님"을 반드시 명시.

### Probat
- PILOT Roaster Shop 1.4에서 프로파일 파일 포맷이 변경되어 하위 호환이 깨진 이력이 있다
  (Artisan 이슈 #228). → 버전 표기 필수.

---

## 5. 수집 로드맵 (네트워크가 열리면)

### 1단계 — 법적으로 안전하고 포맷이 확정된 것부터
1. Artisan 리포 클론 → `src/artisan-alog.xml` 및 import/export 모듈 정독 →
   **`.alog` 파서 작성 + 실물 1건으로 검증** (JSON 비표준 이슈 대응이 핵심)
2. 학술 데이터셋 확보: PMC11748726 부록 Excel, Mendeley/Zenodo/Figshare 직접 검색.
   **CC BY 명시된 것만** 수집. 논문별 라이선스 문구를 `license_note`에 원문으로 복사.
3. 이 단계 결과물로 스키마·단위변환·이벤트 추출 파이프라인을 완성한다.

### 2단계 — 공개 웹 라이브러리
4. Roastetta: robots.txt와 이용약관 확인 → 허용되면 소량(수십 건) 시범 수집 →
   메타데이터 품질 점검 후 확대
5. ROEST 공개 라이브러리: 로그인 없이 접근되는 범위 확인 → 원산지/가공 메타데이터가 붙은
   프로파일 우선 수집 (bean 필드 충실도가 높음)
6. Kaffelogic 공식 프로파일 페이지 + 포럼 첨부

### 3단계 — 개별 공개 게시물 및 그래프 판독
7. Sweet Maria's Coffee Library의 Artisan 로그 게시글 (건별 소량, 출처 명시)
8. Royal Coffee IKAWA 블로그 시리즈 (Part I~III) — 수치가 화면으로 검증 가능한 것만
9. home-barista 포럼 첨부 `.alog` — 게시자가 재배포를 허용한 경우에 한함
10. 그래프 이미지 판독은 **최후 수단**. `source_type`에 `+chart-read`, notes에 판독 오차 명시.

### 상시 원칙
- 로그인/유료 뒤 데이터(IKAWA Online Library, Roast.World, Stronghold Square, Cropster, Probat)는
  **끝까지 URL만 기록**한다. 계정을 만들어 우회 수집하지 않는다.
- 단위 변환(°F→°C)을 했다면 `notes`에 원본 단위와 변환식을 남긴다.
- 프로파일(목표 곡선)과 로스트 로그(실측)를 절대 섞지 않는다.

---

## 6. 출처 URL 목록

### 제조사 / 공식
- IKAWA Roast Profile Library: https://www.ikawacoffee.com/pro-sample-roaster-profiles/
- IKAWA Pro App Guide: https://www.ikawacoffee.com/pro-app-guide/
- IKAWA Professional FAQ: https://www.ikawacoffee.com/professional-faq/
- ROEST 공개 프로파일 라이브러리: https://front.roestcoffee.com/profilelibrary
- ROEST 라이브러리 소개 블로그: https://www.roestcoffee.com/blog/profile-library
- ROEST 프로파일 개요: https://www.roestcoffee.com/support/getting-started/about-roasting-profiles-v2
- Aillio Docs (Roasts): https://docs.aillio.com/roastime/five-tabs/roasts/
- RoasTime 4: https://roastime4.aillio.com/ / 문서: https://roastime4.aillio.com/docs
- Roast.World: https://old.aillio.com/?page_id=33366
- Kaffelogic 프로파일: https://www.kaffelogic.com/pages/profiles
- Kaffelogic 다운로드: https://www.kaffelogic.com/pages/downloads
- Kaffelogic 커뮤니티(공식 프로파일 게시판): https://community.kaffelogic.com/viewforum.php?f=3
- Loring Roast Profile 헬프: https://loring.com/helpfiles/RA/RoastProfile.html
- Probat 소프트웨어/제어시스템: https://www.probat.com/en/products/industry/products/software-controlsystems/
- Stronghold: https://stronghold.coffee/product/s9x.sq
- Stronghold Square 소개 기사: https://www.teaandcoffee.net/news/22245/introducing-stronghold-square-a-roast-profile-sharing-platform/
- Cropster 데이터 내보내기: https://help.cropster.com/3290630
- Cropster 프로파일 관리: https://help.cropster.com/en/knowledge/managing-profiles
- Cropster API: https://www.cropster.com/cropster-api-integration/

### 오픈소스 / 공개 도구
- Artisan (본체): https://github.com/artisan-roaster-scope/artisan
- Artisan `.alog` 파일타입 정의: https://github.com/artisan-roaster-scope/artisan/blob/master/src/artisan-alog.xml
- Artisan 이슈 #219 (.alog JSON 비표준): https://github.com/artisan-roaster-scope/artisan/issues/219
- Artisan 이슈 #85 (alog vs CSV 값 불일치): https://github.com/artisan-roaster-scope/artisan/issues/85
- Artisan 이슈 #228 (Probat Pilot 1.4 포맷 변경): https://github.com/artisan-roaster-scope/artisan/issues/228
- Artisan 이슈 #508 (Roast World JSON 임포트 실패): https://github.com/artisan-roaster-scope/artisan/issues/508
- Artisan 문서 — Profile Converter: https://artisan-scope.org/docs/converter/
- Artisan 문서 — Roast Reports: https://artisan-scope.org/docs/roast-reports/
- Artisan 문서 — Profile Analyzer: https://artisan-scope.org/docs/analyzer/
- Artisan 기종별 문서 (IKAWA): https://artisan-scope.org/machines/ikawa/
- Artisan 기종별 문서 (Aillio): https://artisan-scope.org/machines/aillio/
- Roastetta: https://www.roastetta.com/
- Roastetta 소개 (Artisan Discussion #1904): https://github.com/artisan-roaster-scope/artisan/discussions/1904
- RoastLink 변환기: https://converter.roastlink.com/
- jglogan/roastime-data: https://github.com/jglogan/roastime-data
- themcclure/bullet-time: https://github.com/themcclure/bullet-time
- jacciz/coffee_roasting_profiles: https://github.com/jacciz/coffee_roasting_profiles
- nkraetzschmar/libikawa: https://github.com/nkraetzschmar/libikawa
- Roastero/Openroast (GPL v3): https://github.com/Roastero/Openroast
- GitHub topic `coffee-roasting`: https://github.com/topics/coffee-roasting

### 학술 / 공개 데이터셋
- Adsorption isotherms in roasted specialty coffee (부록에 roasting curves Excel):
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11748726/
- Development of coffee bean porosity and thermophysical properties during roasting:
  https://www.sciencedirect.com/science/article/pii/S0260877424001626
- TU Wien — Analysis of Time Series Data and Optimization of Coffee Roasting:
  https://repositum.tuwien.at/bitstream/20.500.12708/13793/2/Brincoveanu%20Constantin%20-%202019%20-%20Analysis%20of%20time%20series%20data%20and%20optimization%20of...pdf
- Mendeley Data (검색 시작점): https://data.mendeley.com/

### 로스터 공개 / 커뮤니티
- Sweet Maria's — Artisan Roast Profile (Ethiopia DP Hambela Goro):
  https://library.sweetmarias.com/artisan-roast-ethiopia-dry-process-hambela-goro-7627/
- Sweet Maria's — Roast Profiling: https://library.sweetmarias.com/roast-profiling/
- Royal Coffee — Roasting On Ikawa (프로파일 소개):
  https://royalcoffee.com/roasting-on-ikawa-our-favorite-profiles-plus-some-tricks-tips-2/
- Royal Coffee — Roasting On The Ikawa Part II:
  https://royalcoffee.com/roasting-on-the-ikawa-updates-comments-part-ii/
- Royal Coffee — Roasting On The Ikawa Part III:
  https://royalcoffee.com/roasting-on-the-ikawa-updates-comments-part-iii/
- home-barista — A Place To Share Artisan Logs:
  https://www.home-barista.com/roasting/place-to-share-artisan-logs-t66210.html
- home-barista — Artisan Profile Database:
  https://www.home-barista.com/roasting/artisan-profile-database-t23808.html
- home-barista — IKAWA Home 오픈소스 라이브러리/프로토콜 분석:
  https://www.home-barista.com/roasting/ikawa-home-open-source-library-and-protocol-analysis-t92290.html
- Roast World Community — How to download your roast data:
  https://community.roast.world/t/how-to-download-your-roast-data-solved/9798
- Roast World Community — API Access to roast data:
  https://community.roast.world/t/api-access-to-roast-data/15883
- RoastPATH 포럼: https://portal.roastpath.com/forums/topic/any-way-to-load-profiles-from-artisan-as-masterpaths-
