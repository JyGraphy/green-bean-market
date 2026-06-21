# 생두 & 로스팅 전문 지식 + 로스팅 프로파일 페이지 설계 레퍼런스

> 로스팅 프로파일 업로드/피드백 페이지 제작을 위한 도메인 지식 정리.
> 출처: Scott Rao, Cropster, Mill City Roasters, Royal Coffee, Sweet Maria's, Perfect Daily Grind, World Coffee Research, Artisan/RoasTime 문서 등 (각 섹션 하단 Sources).

---

## PART 1. 생두(Green Coffee) 지식

### 1.1 품종(Variety)별 특성과 로스팅
품종은 콩의 **밀도·사이즈·당 함량**을 통해 로스팅 전략에 간접 작용한다. 실제로는 품종 단독보다 **고도·가공·밀도**가 더 직접적 결정 요인.

| 품종 | 콩 특성 | 컵 프로파일 | 로스팅 시사점 |
|------|---------|------------|--------------|
| 게이샤(Geisha) | 큰 사이즈, 고지대일수록 고밀도 | 재스민·베르가못, 티-라이크 플로럴 | 라이트~미디엄, 플로럴/산미 보존 |
| 버번(Bourbon) | 밀도 높음 | 단맛·복합성 우수 | 소량 배치 + 높은 charge temp + 짧은 시간 |
| 티피카(Typica) | 원종, 수율 낮음 | 클린한 단맛 | 균형 로스팅 |
| SL28 | Large(스크린 17~18=AA), 고밀도 | 강렬한 산미, 블랙커런트 | 견고, 1차 크랙 전 에너지 확보 |
| SL34 | 케냐, SL28 자매 | 산미 약·바디 무거움 | 바디 중심 디벨롭 |
| 파카마라(Pacamara) | Very Large | 크리미 바디, 트로피컬 | 대형콩 → 내부 침투 시간 필요 |
| 카투라(Caturra) | 소형·고생산성 | 밝은 시트릭 산미 | 표준 |
| 카투아이(Catuai) | 적/황 체리 | 클린·미디엄 바디 | 부드럽게 로스팅 |

### 1.2 가공방식(Processing)별 로스팅 거동
가공방식은 **잔류 당분·수분·다공성**을 바꿔 열전달과 갈변 속도를 좌우. 당분: 내추럴 > 허니 > 워시드 순으로 높고, 높을수록 **타기 쉬워 초반 열 절제** 필요.

| 가공 | 당분(°Brix)* | 밀도(g/mL)* | 수분%* | 중량손실%* | 로스팅 포인트 |
|------|-----------|-----------|--------|---------|--------------|
| 워시드 | 12–14 | 0.62–0.66 | 10–11 | 13–15 | 예측 가능, 단맛발달 "기준 커피" |
| 허니 | 13–15 | 0.60–0.64 | 11–12 | 14–16 | 잔류 점액↑→ scorch 위험, charge·gas 절제 |
| 내추럴 | 14–16 | 0.58–0.62 | 12–13 | 15–18 | 당분↑→ 낮은 투입온도, 느린 건조 |

(*단일 출처 참고치 — 현장 교차검증 필요)

- **무산소발효(Anaerobic)**: 세포벽 약화·고당분 → 투입온도 워시드보다 5~10°C 낮게(≈180~190°C), post-peak ROR 낮게, DTR 13~20%(전문가 16~17%↓, 종료 200°C 미만).
- **웻훌드(Wet-hulled)**: 인도네시아, 저밀도·청록빛·흙/허브/묵직 바디·낮은 산미 → 낮은 투입온도, 느린 초반.
- **펄프드내추럴**: 워시드·내추럴 중간 강도.

### 1.3 생두 물리 특성과 전략
- **밀도(1차 변수)**: 자유침강 저밀도 0.64 / 평균 0.67 / 고밀도 ≥0.69 g/mL. 고밀도(동아프리카·중미 고지대·워시드) → **hot drum / low flame** 투입 후 후반 모멘텀 유지(stall→baked 방지). 저밀도(브라질·수마트라·내추럴) → 낮은 투입온도, scorch/tipping 방지.
- **수분함량**: 허용 9~13%, 이상 ~11%. 내부 수분이 증기화하며 열전도 경로 형성.
- **수분활성도(aw)**: 이상 ≈0.60. 마이야르·캐러멜화는 aw 0.60~0.70에서 최대. 높으면 past-crop 풍미 가속.
- **스크린 사이즈**: 케냐 AA(17~18)/AB(15~16)/C(<15). 충분히 익히면(235°C·200초+) 사이즈 영향 거의 소멸하나, **사이즈 혼재(불균일)**는 언더디벨롭 원인.
- **고도(SHB/SHG)**: 고지대 → 조밀·단단한 콩, 더 높은 온도 견딤. 중미 SHB ≈1,350m+.

### 1.4 산지별
- **아프리카**(에티오피아·케냐): 고밀도·작은 스크린·복합 산미. 라이트~미디엄, 1차 크랙 진입 시 추가 에너지로 플로럴 발현.
- **중남미**(중미·콜롬비아): 고지대 워시드 = 로스팅 "기준 커피". hot drum/low flame. 브라질 내추럴은 반대로 낮은 투입온도.
- **아시아**(인도네시아): 웻훌드 저밀도, 낮은 투입온도·느린 초반, 진한 로스트와 조화.

---

## PART 2. 로스팅 이론

### 2.1 3단계
1. **드라잉(건조)**: charge~약 150~160°C. 수분 증발(흡열), 초록→노랑. 전체 시간 ~40%.
2. **마이야르(Maillard)**: ~150~200°C(옐로잉~1차 크랙 직전). 당+아미노산 반응 → 향미화합물·멜라노이딘. 154~177°C에서 정점. 캐러멜화 동반.
3. **디벨롭먼트(발현)**: 1차 크랙~배출(drop). 산미·단맛·바디 균형 결정. 미디엄 기준 1~2분.

### 2.2 크랙
- **1차 크랙**: ~196~205°C. 내부 수증기 압력으로 세포 파열, 발열 반응. 라이트~미디엄 기준점, DTR 계산 시작점.
- **2차 크랙**: ~220~232°C. 셀룰로오스 추가 붕괴, 오일 배어남. 다크 로스트 영역.
- (머신·프로브 보정에 따라 ±5°C 편차 흔함 — 절대값보다 범위로)

### 2.3 Rate of Rise (ROR / 승온율)
- **정의**: 단위시간당 콩(BT) 온도 상승률. Scott Rao 대중화.
- **계산**: ROR = (T2−T1)/(t2−t1). 측정 간격 30~60초가 균형(짧으면 노이즈, 길면 둔감).
- **핵심 원칙**: 좋은 로스트 = ROR이 **지속적으로 매끄럽게 감소**. crash/flick/정체 회피.
- **크래시(Crash)**: 1차 크랙 부근 수분 방출로 ROR 급락 → **베이킹** 유발(hollow/flat).
- **플릭(Flick)**: 크래시 후 ROR 급반등(보통 1차 크랙 ~2분 후, DTR 16~17% 부근). 원인: **1차 크랙 중 가스 상승**. → char 풍미. 크래시 중 절대 가스 올리지 말 것.

### 2.4 터닝포인트 / 차지온도 / DTR
- **차지온도(Charge Temp)**: 투입 직전 안정화 온도, ~150~200°C. 배치 클수록 높게.
- **터닝포인트(TP)**: 투입 후 온도 최저점→반등 시점, 보통 45~75초.
- **DTR(Development Time Ratio)** = 디벨롭먼트 타임 ÷ 총 로스팅 타임 × 100.
  - Rao 권장 **20~25%**(상위 로스트의 다수가 이 범위). 노르딕/라이트 18~22%. 큰 머신+소량은 15%도 가능.
  - **⚠ 논쟁**: 목표 범위가 출처마다 16~25%로 상이. "DTR↑→바디↓"는 Rao가 부정. **ROR 형태가 DTR 숫자보다 우선**이라는 데 다수 동의.

### 2.5 컨트롤 변수
- **가스/열**: ROR 직접 좌우 1차 변수. 점진적 감소로 매끄러운 ROR 유지.
- **공기흐름(Airflow)**: 대류 열전달·채프·연기 제어. Mill City 권장 — 드라잉=Low, 중반=Medium, 1차크랙 30초전~종료=High. 과도하면 stall.
- **드럼속도**: 빠름→대류↑/전도↓, 느림→전도↑(scorch 위험)·측정 정확. 현대 드럼 ≈ 대류:전도 70:30.

### 2.6 결함 진단
| 결함 | 커브/외관 신호 | 컵 | 원인·조치 |
|------|--------------|-----|----------|
| 베이킹(Baking) | ROR 크래시 후 정체 | flat·종이맛·hollow, 식으며 산미↓ | 발현 에너지 유지, FC→drop 2분 내 |
| 언더디벨롭 | 빠른 로스트/낮은 DTR, 내부 밝음 | grassy·peanut·sour | FC 후 45~60초 연장 |
| 오버디벨롭 | 늦은 배출 | ashy·burnt·bitter | 일찍 배출 |
| 스코칭(Scorching) | 콩 **평평한 면** 탄자국 | harsh·burnt | charge↓, 드럼속도↑ |
| 티핑(Tipping) | 콩 **끝/모서리** 탄자국 | harsh·burnt | 초반 화력↓, 드럼 과속↓ |

### 2.7 평가 표준
- **Agtron(애그트론)** SCA Gourmet 스케일: #25(다크)~#95(라이트). 라이트 75~95 / 미디엄 55~65 / 다크 25~45.
- **무게손실%**(Rob Hoos): 라이트 11~13 / 라이트-미디엄 13~16 / 다크 17~18 / 매우다크 19~21. **배치 간 ±0.5% 벗어나면 일관성 결함 신호.**

---

## PART 3. 로스팅 프로파일 데이터 모델 (기존 소프트웨어)

### 3.1 Artisan (.alog)
- `.alog`는 **Python dict 직렬화**(엄밀 JSON 아님: `None`, 작은따옴표) → 파싱 시 전처리(`None→null`, `'→"`) 또는 dict-literal 파서 필요.
- 시계열: `timex`(시간 배열 초), `temp1`(ET), `temp2`(BT), `extratimex/extratemp*`(추가 채널).
- 이벤트: `timeindex` = **8개 인덱스 배열** 순서 고정: `[CHARGE, DRYe, FCs, FCe, SCs, SCe, DROP, COOL]`. 값 0 = 미마킹. 이벤트 시각 = `timex[timeindex[n]]`.
- 커스텀 이벤트(가스/공기): `specialevents`, `specialeventstype`, `specialeventsvalue`, `specialeventsStrings`.
- 메타: `roastdate`, `beans`, `weight[green,roasted,unit]`, `density`, `moisture_greens`, `ambientTemp`, `ambient_humidity`, `mode`('C'/'F').
- **설계 시사점**: raw BT/ET만 저장하고 ROR은 로드 시 계산(Artisan 방식). Export는 CSV/JSON 지원.

### 3.2 Cropster
- ET/BT/ROR 실시간, gas/airflow 자동추적, 이벤트(옐로잉/FC/SC), green batch 정보.
- **Roast Compare Report**: 최대 10개 오버레이, ★로 레퍼런스 지정, 큐핑 점수 연결.

### 3.3 RoasTime (Aillio Bullet)
- JSON 구조. `beanTemperature`, `drumTemperature`(IBTS), `beanDerivative`(ROR).
- 이벤트는 sample index: `indexYellowingStart`, `indexFirstCrackStart/End`, `indexSecondCrackStart/End`, `roastStartIndex/EndIndex`.
- 제어: `actions.actionTimeList[]={ctrlType(0=Power/1=Fan/2=Drum), index, value}`.
- 메타: `weightGreen/Roasted`, `beanChargeTemperature`, `beanDropTemperature`, `totalRoastTime`, `sampleRate`, `ambient`, `humidity`.

### 3.4 공통 스키마 권장 (우리 앱)
```
series: { timex[], bt[], et[] }            # raw, ROR은 계산
events: { charge, tp, dryend, fcs, fce, scs, sce, drop }   # 시간(초) 또는 인덱스
meta:   { beanId, roastery, roastDate, greenWeight, roastedWeight,
          weightLossPct, chargeTemp, dropTemp, totalTime, dtr,
          ambientTemp, ambientHumidity, agtron, rating }
extra:  { channels[] }                     # 가스/공기/드럼 (선택)
```
- 파생값(ROR, DTR, weightLoss%, phase 비율)은 **서버/클라이언트 계산**.

---

## PART 4. 시각화 & 페이지 설계

### 4.1 표준 시각화
- **듀얼 Y축 라인차트**: 좌축 온도(°C, BT+ET), 우축 ROR(°C/min). X축 시간 `mm:ss`(CHARGE=0:00).
- ROR은 노이즈 심해 **스무딩 필수**(delta span + polyfit).
- **이벤트 마커**: CHARGE/TP/DRY END/FCs/FCe/DROP를 수직선+라벨 또는 곡선 위 점.

### 4.2 비교/오버레이
- **고스트/레퍼런스**: 기준 프로파일을 회색/점선 배경, 현재는 진한 색 전경.
- **이벤트 기준 재정렬(realign)**: CHARGE(기본) 또는 FCs 기준 time-align. (temp-align 토글 옵션)

### 4.3 추천 스택
- **차트**: **Chart.js v4 + chartjs-plugin-annotation** (듀얼축 쉬움, 이벤트 수직선 선언적, 오버레이 직관적, vanilla JS·문서 풍부). 성능 극한 필요시 uPlot, Plotly/ECharts는 과함.
- **시간축**: linear(경과 초) + tick 콜백 `mm:ss`.
- **입력**: ① Artisan JSON/CSV 업로드(전처리 파서) ② 수동 키포인트 폼(CHARGE/TP/DRY/FC/DROP의 time,temp) 둘 다.
- **저장**: Supabase에 위 공통 스키마 JSON.

### 4.4 업로드+피드백 UX
- 드래그앤드롭 + 클릭, 즉시 클라이언트 검증, **미리보기**(곡선 썸네일 + 인식 이벤트/DTR 요약), 명확한 에러, 성공 후 뷰 링크.
- **피드백 엔진**: raw에서 ROR/DTR/phase%/weightLoss% 계산 → 레퍼런스(이상 곡선) 대비 비교 + 결함 룰 적용:
  1. FC에서 ROR 크래시 → "화력을 더 일찍 줄이세요"
  2. 종료 직전 ROR 스파이크(flick) → "1차 크랙 중 가스 올리지 마세요"
  3. ROR 30초당 2°C 미만 정체 → 베이킹 경고
  4. DTR < 16~18% + 풋내 → "발현 45~60초 연장"
  5. 무게손실 배치 간 ±0.5% 초과 → 일관성 경고

---

## PART 5. 로스팅 디펙트 심화

> 출처: Scott Rao, Rob Hoos (Hoos Coffee Consulting), Morten Münchow (CoffeeMind), Cropster, Giesen, PMC4914823(GC-MS 연구), Perfect Daily Grind, SCA 프로토콜

### 5.1 디펙트 분류 체계 (Rob Hoos)

- **객관적 디펙트(Objective)**: 육안으로 확인 가능한 이진(있음/없음) 결함. 선호도와 무관.
  → Scorching, Tipping, Facing, Quakers, Chipping
- **주관적 디펙트(Subjective)**: 컵핑으로만 감지. 로스터의 목표 프로파일 해석에 의존.
  → Baked, Underdeveloped, Over-roasted, Overdeveloped

---

### 5.2 주요 디펙트 상세

#### Scorched (스코칭 / 표면 과열)
- **원인**: 투입온도 과다(실험치 275°C vs 표준 210°C), 드럼 회전 느림, 과충전, 저밀도·내추럴 원두(열충격에 취약)
- **발생 시점**: 로스팅 **초기** — 원두가 수분을 충분히 흡수하기 전에 드럼 접촉열이 과도하게 전달될 때
- **외관**: 원두 **평평한 면**에 검은 반점 (탄색이 원두 전체 색보다 먼저 나타남 = 초기 손상 신호)
- **컵핑**: 스모키·재·연기 향, 쓴 뒷맛. 외부는 탄 맛인데 내부는 오히려 날것(내부가 밀봉되어 발달 불가)
- **화학 마커(GC-MS)**: 4-ethyl-2-methoxyphenol, 피리딘, 페놀 급증
- **조치**: charge temp 낮춤, 드럼 회전수 증가, 충전량 줄임

#### Baked (베이킹 / 열 정체 결함)
- **원인 (Scott Rao 정의)**: 열 과다가 아닌 **ROR의 급격한 하락(crash)**. 1차 크랙 시점에 내부 수분이 방출되며 프로브 냉각 → ROR 급락. 이를 만회하려 가스를 올리면 오히려 악화.
- **ROR 임계**: ROR이 30초당 2°C 미만으로 떨어지면 경고. 0 또는 마이너스 = 강한 baked 신호. 크랙 이전 크래시일수록 더 심각.
- **외관**: 없음 — **육안으로 식별 불가**. 가장 위험한 이유.
- **컵핑**: 밀가루·오트·종이·맥아 향, 단맛·산미 급감, **식을수록 맛이 급격히 떨어짐**(핵심 판별 포인트), 낮은 산도
- **화학 마커(GC-MS)**: 말톨(maltol), 디퍼퍼릴에테르, 피리딘 증가 / 퍼퍼릴메틸에테르 감소
- **조치**: 1차 크랙 전 사전에 화력 낮춤. 크래시 발생 중 절대 가스 올리지 말 것.

#### Underdeveloped (언더디벨롭 / 발달 부족)
- **원인**: 너무 이른 배출, DTR < 15%, 낮은 charge temp(실험치 135°C → 20분 로스팅에도 발달 부족), 낮은 에너지로 원두 내부에 열이 도달 못함
- **외관**: 밝은 내부, 컵핑 크러스트 얇거나 미형성(CO₂ 부족)
- **컵핑**: 풀내·짚내·완두콩 향, 신맛-생내, 단맛·바디 부족, 금속성·생곡물 향
- **화학 마커(GC-MS)**: 2,5-dimethylfuran 급증 (미완성 발달 지표)
- **최소 발달 기준**: 1차 크랙 후 최소 45~60초 이상

#### Over-roasted / Overdeveloped (과발달)
- **Over-roasted**: 배출온도 과다
- **Overdeveloped**: 1차 크랙 후 시간 과다 (DTR > 30%+ / 라이트 기준)
- **외관**: 매우 어둡고 기름짐(표면 오일 이행 가속)
- **컵핑**: 연기·재·탄 향, 쓴맛 지배, 산미·복잡성 소멸, 산지 특성 완전 상실

#### Tipping (티핑)
- **원인**: 초반 고밀도 원두에 빠른 급속 가열 → 콩 끝부분이 몸통보다 수분을 먼저 잃고 과열
- **외관**: 콩 **끝(뾰족한 부분)이나 얇은 모서리**에만 검은 점 (Scorching과 구별: Scorching은 평면, Tipping은 끝)
- **컵핑**: Scorching과 유사 — 탄 뒷맛

#### Facing (페이싱 / 후반 접촉 과열)
- **원인**: 로스팅 후반부 드럼 벽 접촉 → Scorching과 달리 **후기** 발생
- **외관**: 원두 평면이 탄 채로 전체적으로 진한 색 (이미 발달된 색에서 추가 탄화)
- **컵핑**: 탄 맛·훈제 향

#### Quakers (퀘이커 / 미숙두)
- **원인**: 덜 익은 체리 사용 — 당분·아미노산 부족으로 마이야르 반응이 진행되지 않음
- **외관(배전 후)**: 배치 내 다른 원두보다 확연히 **연한 주황·카키색**
- **컵핑**: 오래된 땅콩 냄새(그라인드 시), 쓴맛·공허함
- **SCA 기준**: 스페셜티 등급 = 퀘이커 **0개** 허용 (1차 결함)

#### Chipping (치핑)
- **원인**: 다크 로스팅 중 취성 원두의 압력 집중
- **외관**: 파편·크레이터 형태
- **컵핑**: 감각적 영향 없음 — **시각적 결함만** (Rob Hoos)

---

### 5.3 ROR 디펙트 심화

#### ROR Crash
- 정의: ROR이 급격히 0 또는 음수로 하락
- 주요 발생 시점: 1차 크랙 (내부 수분이 프로브 주변 온도를 일시 냉각)
- 결과: Baked 결함. **크래시 폭과 baked 정도는 비례**
- 흔한 실수: 크래시 만회를 위한 가스 증가 → 오히려 악화

#### ROR Flick
- 정의: 크래시 이후 ROR이 다시 급반등
- 발생 시점: 보통 DTR 16~17% 부근 (1차 크랙 약 2분 후)
- 원인: **1차 크랙 중·후 가스 상승** (드럼 잔열이 전달되며 재가열)
- 결과: 라이트 로스팅에서도 로스티·탄 향, 섬세함 소실
- Cropster: AI 기반 플릭 예측 기능 제공
- 예방: 1차 크랙 전에 미리 화력 낮춤 / 크래시 중 가스 절대 올리지 않기

#### Flat ROR (정체 ROR)
- 정의: ROR이 일정 수준에서 하강하지 않고 정체 (plateau)
- 결과: 발생 시점에 따라 Baked 또는 Underdeveloped
- 원인: 프로파일 모멘텀 소실, 에너지 부족
- 주의: 프로브 전기 노이즈로 인한 인공적 평탄화 가능성도 확인 필요 (권장 프로브 ≤3~4mm, 샘플링 1초, ROR 계산 간격 ≤15초)

---

### 5.4 투입온도(Charge Temperature)별 디펙트

| 원두 유형 | 권장 투입온도 | 이탈 시 위험 |
|----------|------------|------------|
| 고밀도 고지대 워시드 | 205–220°C | 낮으면 → Baked/Under, 높으면 → Scorched |
| 중밀도 워시드 | 195–210°C | 동일 |
| 내추럴 (저밀도, 고당분) | 185–200°C | Scorching 발생 온도 낮아 주의 |
| 무산소발효 | 워시드보다 5~10°C 낮게 | 세포벽 약화·고당분 → 낮은 투입 |
| 로부스타 / 고수분 | 200–215°C | |

- 투입온도 275°C → Scorching (실험치)
- 투입온도 135°C → 20분 로스팅에도 Underdeveloped (실험치)

---

### 5.5 DTR 범위별 디펙트

| 로스팅 레벨 | 권장 DTR | DTR 미달 위험 | DTR 초과 위험 |
|------------|---------|------------|------------|
| 라이트 | 15–20% | 풀내·신맛·미성숙 | Baked·쓴맛 |
| 미디엄 라이트 | 18–22% | 동일 | 동일 |
| 미디엄 | 20–25% | 동일 | 복잡성 소멸 |
| 미디엄 다크 | 25–30% | | 탄 향·일차원 |
| 다크 | 30%+ | | |

**Morten Münchow(CoffeeMind) 연구**: 풍미에 영향을 미치는 변수 우선순위
1. **로스팅 색상(Agtron)** — 가장 큰 영향
2. **DTR** — 동일 색상 내 약 20% 풍미 변화 설명
3. 1차 크랙까지의 시간

→ DTR보다 **색상 관리가 더 근본적인 레버**. DTR 수치 집착보다 ROR 형태 우선.

---

### 5.6 마이야르 vs 캐러멜화 불균형 (New Wave Coffee Roasters 5 프로파일 참고)

New Wave Coffee Roasters 실험: **Agtron 값이 동일한 5개 프로파일**을 제작, 가스 조절만 달리함.

| 프로파일 | 가스 조절 | 결과 |
|---------|---------|------|
| Normal | 균형 | 최적 로스팅 |
| Gas Over | 캐러멜화 단계에서 과가스 | 캐러멜화 최대 — 단맛 강하나 평탄 |
| Too Fast | 초반 급속 승온 | 마이야르 최대 — 밝은 산미, 얕은 바디 |
| Gas Off | 캐러멜화 단계에서 가스 차단 | 캐러멜화 최소 — 단맛 부족, 시큼 |
| Too Slow | 전 구간 저온 | 마이야르 최소 — 베이킹·밋밋·짚내 |

**핵심 인사이트**: 색상(Agtron)이 동일해도 가스 타이밍에 따라 마이야르/캐러멜화 비율이 달라져 **컵 프로파일이 완전히 다름**. 컵핑이 유일한 검증 수단.

| 반응 | 온도 범위 | 반응물 | 풍미 |
|------|---------|------|------|
| 마이야르(Maillard) | ~150°C~ | 아미노산 + 환원당 | 견과류·초콜릿·흙·복잡성 |
| 캐러멜화(Caramelization) | ~170~180°C~ | 당류만 | 단맛·버터스카치·캐러멜 |

**불균형 패턴**:
- **Too Fast**: ROR 초반 급상승 → 마이야르 과활성, 유기산 미변환 → 날카로운 산미·얕은 바디
- **Too Slow / Flat ROR**: 마이야르 장기 정체 → 휘발성 향미 이미 형성된 화합물 소산 → Baked
- **과발달**: 형성된 마이야르 화합물 분해 → 멜라노이딘·탄화 지배 → 쓴맛·재 향
- **배출 후 냉각 지연**: 배출 후에도 마이야르·캐러멜화 60~90초 지속 → 라이트 → 미디엄으로 의도치 않게 진행

---

### 5.7 SCA 컵핑 디펙트 진단 프로토콜

**드라이 향(Fragrance)으로 감지**
- 풀내·짚내 → Underdeveloped
- 스모키·재 향 → Scorched 또는 Over-roasted
- 빵·곡물 향 → Baked
- 오래된 땅콩 냄새 → Quakers 포함

**습식 아로마(Wet Aroma / 크러스트 브레이크) 감지**
- 크러스트 두껍고 활발 → 잘 발달
- 크러스트 얇고 빈약 → Underdeveloped

**고온(71°C) 감지**
- 날카로운 미성숙 산미 → Underdeveloped
- 공허하고 밋밋 → Baked
- 연기·재 → Scorched / Tipping

**식으면서(~45°C) 감지 — Baked 핵심 판별**
- Baked: 식을수록 단맛·산미가 **급격히 떨어짐**
- 잘 로스팅된 커피: 식어도 풍미 유지 또는 향상
- Scorched: 식어도 탄 향 지속

**SCA 스페셜티 등급 기준 (생두)**
- 1차 결함(Category 1): 0개 — 완전 검은콩, 완전 신콩, 건조 체리, 곰팡이 손상, 이물질, 심각한 충해
- 2차 결함(Category 2): ≤5개 / 350g — 부분 검은콩, 파치먼트, 미숙두, 파손 등
- 퀘이커: 0개 허용

---

### 5.8 디펙트 빠른 참조표

| 디펙트 | 주요 원인 | ROR 패턴 | 외관 | 핵심 컵핑 묘사 |
|--------|---------|---------|------|--------------|
| Scorched | Charge temp 과다 | N/A (초기 손상) | 평면에 검은 반점 | 스모키·쓴맛·내부 날것 |
| Baked | ROR 크래시 | 급락 → 0 또는 음수 | 정상 (식별 불가) | 밀가루·종이·공허, 식으면 급락 |
| Underdeveloped | 이른 배출·DTR <15% | 저에너지·짧은 후크랙 | 내부 밝음, 크러스트 얇음 | 풀·짚·신맛-생내·쇳내 |
| Over-roasted | 배출온도 과다 | N/A | 매우 어둡고 기름짐 | 쓴맛·연기·재·일차원 |
| Overdeveloped | DTR 과다 | 후크랙 과연장 | 어둡고 기름짐 | 탄·쓴맛·산지 특성 소멸 |
| Tipping | 초반 급속 가열 | N/A | 끝·모서리만 검은 점 | 탄 뒷맛 |
| Facing | 후반 드럼 접촉 | N/A | 평면 탄화 (진한 베이스색) | 탄·훈제 향 |
| Quakers | 미숙두 생두 | N/A | 배전 후 연한 주황·카키 | 오래된 땅콩·쓴맛·공허 |
| ROR Flick | 크랙 중 가스 상승 | 크래시 후 급반등 | 없음 | 로스티·탄 향·섬세함 소실 |
| Flat ROR | 에너지 정체 | 정체 plateau | 없음 | Baked 또는 Underdeveloped |

---

### 5.9 주요 참고 인물 및 출처

| 참고 인물/기관 | 핵심 기여 |
|-------------|---------|
| **Scott Rao** | DTR 20~25% 가이드라인 정립, Baked를 ROR 크래시 현상으로 재정의, 지속 감소 ROR 원칙 |
| **Rob Hoos** | 객관적/주관적 디펙트 분류 체계, *Modulating the Flavor Profile of Coffee* |
| **Morten Münchow (CoffeeMind)** | 색상 > DTR 우선순위 연구, DTR이 풍미 변화의 약 20% 설명 |
| **Cropster** | ROR 플릭 AI 예측, 배치 비교 리포트, 플릭 방지 가이드 |
| **New Wave Coffee Roasters** | 5-프로파일 마이야르/캐러멜화 비교 실험 (Instagram) |
| **PMC4914823 (GC-MS 연구)** | Scorched·Baked·Underdeveloped의 화학 마커 규명 |

---

## 핵심 요약 (피드백 체크리스트)
1. ROR이 끝까지 매끄럽게 감소하는가? (crash/flick/정체 없음)
2. DTR이 목표 범위인가 (라이트 18~20%, 일반 20~25%) — 단 ROR 형태 우선
3. Agtron 색도가 목표 로스트와 일치하는가
4. 무게손실%가 로스트 정도에 맞고 배치 간 ±0.5% 이내인가
5. 컵노트가 언더(풀내·짚내)/베이크드(밀가루·공허)/오버(재·쓴맛) 신호인가
6. 시각적 결함 체크: 스코칭(평면 탄점) / 티핑(끝 탄점) / 퀘이커(연한 카키) 있는가
7. 색상(Agtron)이 동일해도 가스 타이밍에 따라 마이야르/캐러멜화 비율이 달라짐 — 컵핑으로 검증

---

## PART 6. 로스팅 프로파일 그래프 시각화 — 소프트웨어별 완전 분석

> 페이지 제작 시 어떤 소프트웨어의 프로파일이 입력되어도 동일하게 표시·해석할 수 있도록
> 각 소프트웨어의 그래프 문법(축·커브·색상·이벤트·페이즈)을 완전히 정리한다.

---

### 6.1 공통 그래프 문법 (모든 소프트웨어 공통)

**표준 듀얼 Y축 구조**
```
좌측 Y축 : 온도 (°C) — BT·ET 커브
우측 Y축 : ROR (°C/min 또는 °C/30s) — 델타 커브
X축      : 경과 시간 (mm:ss) — 기준점 = CHARGE 이벤트
```

**ROR 계산 공식 (공통)**
```js
RoR = (BT_현재 - BT_이전) / (t_현재 - t_이전) × 60   // °C/min
```
- 시간 지연(lag) = delta_span ÷ 2 (불가피) → span을 짧게 유지할수록 응답성 ↑, 노이즈 ↑
- Polyfit(최소제곱법) 사용 시 lag 없이 노이즈 감소 가능 (Artisan 권장)

**시간 기준점 (Time Zero)**
- 모든 소프트웨어 공통: **CHARGE 이벤트 = 0:00**
- 투입 전 예열 구간은 음수 시간으로 표시(선택적)

---

### 6.2 Artisan

#### 축 구성
| 축 | 내용 |
|----|------|
| X축 | 경과 시간 mm:ss (CHARGE = 0:00) |
| 좌측 Y축 | 온도 °C (사용자 설정, 보통 75~250°C) |
| 우측 Y축 | ROR °C/min (사용자 설정) |

#### 커브 & 기본 색상
| 커브 | 기본 색상 | 축 |
|------|-----------|-----|
| ET (환경온도) | **빨강 (red)** | 좌측 온도 |
| BT (원두온도) | **네이비 (#00007F)** | 좌측 온도 |
| ΔET (ET ROR) | **주황 (orange)** | 우측 ROR |
| ΔBT (BT ROR) | **파랑 (blue)** | 우측 ROR |
| 추가 채널 | **초록 (green)** | 선택 |

> ※ 모든 색상 사용자 변경 가능. ROR 커브는 CHARGE 이벤트 전까지 표시 안 됨.

#### 페이즈 배경 밴드 (핵심 특징)
| 페이즈 | 배경색 | 구간 |
|--------|--------|------|
| 건조(Drying) | **연초록** | CHARGE → DRY END |
| 마이야르(Maillard) | **연노랑** | DRY END → FCs |
| 발달(Development) | **연갈색** | FCs → DROP |
| 냉각(Cooling) | **연파랑** | DROP → COOL |

#### 이벤트 마커 표시 방식
- **CHARGE·TP·DRY END·FCs·FCe·SCs·SCe·DROP**: 수직선 + 짧은 라벨 플래그
- **커스텀 이벤트(가스·팬 조작)**: 5가지 스타일 중 선택
  - Flag: BT/ET 커브 위 마커
  - Bar: 그래프 하단 컬러 바 (첫 글자 + 값)
  - Step: 계단형 그래프
  - Step+: 계단형 + BT 위 설명
  - Combo: 계단형 + 별도 그래프

#### 레퍼런스 오버레이 (Background Profile)
- 배경에 반투명 커브로 표시 (기본 불투명도 2/10 = 매우 흐리게)
- CHARGE 시점 기준 자동 정렬 (DRY END·FCs 기준도 선택 가능)
- BT배경·ET배경·ΔBT배경·ΔET배경 모두 표시 가능

#### 자동 분석 표시
- **페이즈 비율(%)**: 건조/마이야르/발달 각 시간 및 비율 오른쪽 통계창
- **DTR%**: 1차 크랙 시작 ~ DROP ÷ 총 시간 × 100
- **평균 ROR**: 각 페이즈별
- **AUC**: 기준온도 이상 면적 (총 에너지 프록시)
- **무게 손실**: 투입·배출 중량 입력 시 자동 계산

#### ROR 계산 설정
- Delta Span: 최대 30초 (권장: 샘플링 간격 × 2)
- 단위: **°C/min**
- Polyfit 옵션: 최소제곱법으로 lag 없이 스무딩

---

### 6.3 Cropster Roasting Intelligence

#### 축 구성
| 축 | 내용 |
|----|------|
| X축 | 경과 시간 mm:ss (CHARGE = 0:00) |
| 좌측 Y축 | 온도 °C |
| 우측 Y축 | ROR °C/30s 또는 °C/60s (설정 가능) |

> Cropster의 기본 ROR 단위는 **°C/30s** (Artisan의 °C/min와 다름 — 수치가 절반).
> 단위 변경은 표시 라벨만 바뀌고 커브 형태는 동일.

#### 커브
- BT, ET, ROR(BT 기반) 표시
- 레퍼런스 프로파일을 라이브 로스팅 중 동일 차트에 오버레이

#### 이벤트
- Color Change(옐로잉), First Crack, Drop 등 수직 마커
- AI 예측: First Crack·Flick 예측 모달 (PLC 연결 기기만)

#### ROR 스무딩 3단계 프리셋
1. **Recommended** (기본): 균형
2. **Noise Smoothing**: 노이즈 심한 환경용, 응답성 낮음
3. **Sensitive**: 최대 응답성, 노이즈 많음

#### 데이터 내보내기 컬럼 (CSV/Excel)
```
Time(mm:ss), BT(°C), ET(°C), RoR(°C/min or /30s), [이벤트 어노테이션]
```

---

### 6.4 RoasTime (Aillio Bullet)

#### 축 구성
- X축: 시간 (초 인덱스, sampleRate=1Hz)
- Y축: 온도 °C (BT·Drum Temp)
- ROR: °C/min (`beanDerivative` 배열로 저장)

#### 커브
| 커브 | 설명 |
|------|------|
| BT (beanTemperature) | 일반 프로브 원두온도 |
| DT (drumTemperature) | IBTS 적외선 드럼온도 — 접촉 없이 측정 |
| ROR (beanDerivative) | BT의 ROR, **파일에 직접 저장** |

#### IBTS의 의미
- 드럼 내부 원두 표면을 적외선으로 직접 측정 → 프로브 지연 없음
- ROR이 더 즉각적·정확 → 다른 소프트웨어 ROR과 수치감 다를 수 있음

#### 이벤트 인덱스 (배열 인덱스로 저장)
```
roastStartIndex, indexYellowingStart,
indexFirstCrackStart, indexFirstCrackEnd,
indexSecondCrackStart, indexSecondCrackEnd,
roastEndIndex
```

#### 제어 액션 로그
```json
{ "ctrlType": 0, "index": 30, "value": 8 }  // 0=Power, 1=Fan, 2=Drum
```

---

### 6.5 Firescope (파이어스코프)

#### 기본 커브 색상
| 커브 | 기본 색상 |
|------|-----------|
| ET (환경온도) | **빨강** |
| BT (원두온도) | **초록** |
| BT RoR | **파랑** |
| ET RoR | **노랑** |

> ※ 모든 색상 사용자 변경 가능

#### 축 구성
- X축: 시간 (사용자 설정, 자동 연장 옵션)
- 좌측 Y축: 온도 (사용자 설정, 자동 연장 옵션)
- 우측 Y축: RoR (사용자 설정)
- **샘플링: 0.5초** (Artisan·Cropster의 2배 빠름)

#### 페이즈 표시
- **연노랑(light yellow) 구간**: 건조 종료온도 ~ 1차 크랙 직전 구간 배경 표시

#### 이벤트 자동 감지
- **투입(Charge)**: BT 하강 시작 자동 감지
- **터닝포인트(TP)**: BT 반등 자동 감지
- **건조 종료**: TP 이후 설정 온도 도달 시 자동
- **1차 크랙·2차 크랙**: 수동 입력

#### 레퍼런스 오버레이
- 이전 로스팅 로그를 배경에 고정 (배경 로그 핀)
- 현재 커브와 레퍼런스의 **온도 차이를 실시간 표시**
- 로스팅 중 레퍼런스 교체 가능

#### 예측선
- 현재 RoR 기반 BT·ET **점선 예측 궤적** 표시

---

### 6.6 Stronghold Roastware (S7/S9/S9X)

#### 화면 구성 (2분할)
```
상단 그래프: 온도 커브 (3개)
하단 그래프: ROR + 3가지 열원 제어 입력값
```

#### 상단 그래프 — 온도 커브
| 커브 | 색상 | Y축 | 범위 |
|------|------|-----|------|
| 열풍(Hot Air) 온도 | **빨강** | 우측 | 200–600°C |
| 원두(Internal) 온도 | **흰색** | 좌측 | 80–200°C |
| 드럼(Tower) 온도 | **초록** | 좌측 | 80–200°C |

#### 하단 그래프 — ROR + 제어값
- **흰색 커브**: ROR (원두온도 기반, **30초 간격** 측정, 초당 업데이트)
  - 터닝포인트 후 전형적 ROR: ~5°C/30s → 배출 시 ~3°C/30s
- **3가지 열원 제어 트레이스** (별도 라인으로 표시):
  1. Hot Air (대류열) 설정값
  2. Halogen (복사열/할로겐) 설정값
  3. Agitation (드럼 회전속도) 설정값

#### 3열원 시스템의 그래프 해석
- Hot Air ↑ → 상단 빨강 커브 상승 + 원두온도(흰색) 상승
- Halogen ↑ → 드럼온도(초록) 상승 (원두온도에 간접 영향)
- Drum Speed ↑ → ROR에 즉각적 영향 (열전달률 변화)

#### 이벤트
- 터닝포인트: 자동 표시
- 1차 크랙: 전용 아이콘 터치로 수동 마킹
- 2-핀치 줌 지원 (특정 구간 확대)

---

### 6.7 IKAWA App (열풍식 샘플 로스터)

> IKAWA는 드럼 로스터가 아닌 **열풍식(fluid bed)** 로스터 — 그래프 문법이 다름

#### 커브
| 커브 | 색상 | 의미 |
|------|------|------|
| Exhaust Temp | **빨강** | 원두 통과 후 배기온도 (≈BT 역할) |
| Inlet Temp | **노랑** | 유입 공기온도 (Pro V3 추가) |
| Fan Speed | **흰색** | 팬 속도 % (60–100%) |
| ROR | **노랑** | 실제 ROR (목표 ROR과 비교) |

#### 축 구성
- X축: 시간 (최대 12분)
- 좌측 Y축: 온도 °C (최대 290°C 안전 한계)
- 우측 Y축: 팬 속도 % (별도 축)

#### IKAWA 특수성 — 드럼 로스터와의 차이
- **BT 프로브 없음**: 배기온도로 간접 측정 (원두 접촉 없음)
- **팬속도 = 주요 로스트 컬러 제어 변수**: 팬↑ = 라이트, 팬↓ = 다크 (역직관적)
- 프로파일 = **공기온도 + 팬속도 처방전** (원두온도 처방전이 아님)
- 열적 질량이 매우 낮아 환경 변화에 민감

#### 프로파일 표시
- **목표 커브**(점선)와 **실제 커브**(실선) 동시 표시
- DTR(Development Time Ratio) 1차 크랙 마킹 후 실시간 표시

---

### 6.8 파일 포맷 비교 — 범용 파서 구현을 위한 핵심

#### Artisan .alog
```json
{
  "timex":     [0.0, 3.0, 6.0, ...],   // 초 (float, CHARGE가 아닌 START 기준)
  "temp1":     [...],                   // ET
  "temp2":     [...],                   // BT
  "timeindex": [i0, i1, i2, i3, i4, i5, i6, i7],
  // [CHARGE, DRY, FCs, FCe, SCs, SCe, DROP, COOL] — 배열 인덱스값
  // -1 또는 0 = 미마킹
  "specialevents":        [...],        // 가스/팬 이벤트 시간(초)
  "specialeventstype":    [...],
  "specialeventsvalue":   [...],
  "specialeventsStrings": [...]
}
```
- **ROR 미저장** — 로드 시 재계산 필요
- 파싱 전처리: `None→null`, `True→true`, `False→false`, `'→"`

#### RoasTime .json
```json
{
  "beanTemperature":      [...],   // BT 배열 (1초 간격)
  "drumTemperature":      [...],   // IBTS 드럼온도
  "beanDerivative":       [...],   // ROR (°C/min) — 직접 저장
  "roastStartIndex":      45,      // 배열 인덱스
  "indexFirstCrackStart": 380,
  "indexFirstCrackEnd":   430,
  "roastEndIndex":        600,
  "sampleRate":           1,       // 초당 샘플 수
  "weightGreen":          500,
  "weightRoasted":        420
}
// 시간(초) = 인덱스 ÷ sampleRate
```

#### Cropster CSV (내보내기)
```
Time(mm:ss), BT(°C), ET(°C), RoR(°C/min or /30s), [이벤트 컬럼]
```

---

### 6.9 범용 차트 구현을 위한 공통 스키마

어떤 소프트웨어의 프로파일을 입력받아도 동일하게 표시하려면 아래 스키마로 정규화:

```js
// 정규화된 공통 프로파일 스키마
{
  // 필수 시계열 (동일 길이 배열)
  timex: [0, 3, 6, ...],     // CHARGE 기준 경과 시간 (초)
  bt:    [185.0, 186.2, ...], // 원두온도 °C
  et:    [210.0, 211.0, ...], // 환경/배기온도 °C (없으면 null 배열)
  ror:   [null, null, 8.2, ...], // °C/min (null = 계산 불가 구간)

  // 이벤트 (CHARGE 기준 경과 시간, 초)
  events: {
    charge: 0,       // 항상 0
    tp:     null,    // 터닝포인트
    dry:    null,    // 건조 종료
    fcs:    420,     // 1차 크랙 시작
    fce:    480,     // 1차 크랙 종료
    scs:    null,    // 2차 크랙 시작
    sce:    null,
    drop:   720,     // 배출
    cool:   null
  },

  // 가스·팬·드럼 조작 로그
  controls: [
    { time: 60, type: 'gas', value: 8 },
    { time: 120, type: 'fan', value: 4 }
  ],

  // 메타
  meta: {
    samplingInterval: 3,   // 초
    tempUnit: 'C',
    title: '...',
    roastDate: '2024-04-15',
    greenWeight: 500,
    roastedWeight: 430,
    source: 'artisan' // 'artisan'|'roastime'|'cropster'|'firescope'|'stronghold'|'ikawa'
  }
}
```

#### 소프트웨어별 정규화 매핑

| 소프트웨어 | timex 변환 | BT 필드 | ET 필드 | ROR | 이벤트 |
|-----------|-----------|---------|---------|-----|--------|
| Artisan .alog | timex[] 그대로 (단, CHARGE 인덱스 기준 재조정) | temp2[] | temp1[] | 재계산 | timeindex[0~7] → 인덱스→초 변환 |
| RoasTime .json | index ÷ sampleRate | beanTemperature[] | drumTemperature[] | beanDerivative[] | indexFirstCrackStart 등 → 초 변환 |
| Cropster CSV | mm:ss → 초 변환 | BT 컬럼 | ET 컬럼 | RoR 컬럼 | 이벤트 컬럼 파싱 |
| IKAWA CSV | Time 컬럼 | Exhaust Temp | Inlet Temp | 재계산 | 이벤트 컬럼 |

#### ROR 재계산 함수 (공통)
```js
function calcRoR(timex, bt, spanSec = 30) {
  // spanSec: 델타 스팬 (Artisan 기본 30초, Cropster 60초)
  return bt.map((b, i) => {
    if (i === 0) return null;
    const dt = timex[i] - timex[i - 1];
    if (dt === 0) return null;
    return ((b - bt[i - 1]) / dt) * 60; // °C/min
  });
}
```

---

### 6.10 ROR 단위 통일 주의사항

| 소프트웨어 | 기본 ROR 단위 | 동일 로스팅 시 수치 예 |
|-----------|------------|-----------------|
| Artisan | **°C/min** | 8.0 |
| Cropster | **°C/30s** (기본) | 4.0 (= 절반) |
| RoasTime | **°C/min** | 8.0 |
| Stronghold | **°C/30s** | 4.0 |
| Firescope | **°C/min** (추정) | 8.0 |

→ 페이지에서 단위 선택 옵션 제공 권장. 내부 저장은 **°C/min** 통일 후 표시 시 변환.

---

### 6.11 Cropster 차트 심화

#### 시간 기준 (Time Zero)
- **Start 버튼 클릭 = 0:00** (Artisan의 CHARGE와 다름)
- CHARGE는 Start 이후 ~30초 내 발생하는 이벤트로 마킹
- → 파서 구현 시 주의: Cropster CSV의 Time 0은 투입 전일 수 있음

#### 커브 구성
| 커브 | 설명 |
|------|------|
| BT | 원두온도 (메인 커브) |
| ET | 환경/배기온도 |
| BT RoR | BT의 ROR (우측 Y축) |
| ET RoR | ET의 ROR — **1차 크랙 직전 ET RoR 트로프(최저점)** = 실제 FC 시작의 가장 신뢰할 수 있는 시각적 지표 (Scott Rao) |
| Bean Curve Prediction | **점선** — 현재 기준 2분 앞 BT 예측 궤적 (RI5, 로스팅 시작 60초 후부터) |
| RoR Prediction | 위와 함께 표시되는 점선 ROR 예측 |
| Reference Curve | **회색 실선** — 배경 레퍼런스 프로파일 |

#### 페이즈 표시 — 모듈레이션 차트 (Modulation Chart)
- 메인 차트 **하단에 별도 밴드**로 표시 (차트 내 배경 밴드가 아님!)
- 3개 구간 색상으로 구분:
  - 건조: CHARGE → Color Change(옐로잉)
  - 마이야르: Color Change → FCs
  - 발달: FCs → DROP
- 각 구간에 **시간(mm:ss)과 비율(%)** 표시
- 커서 호버 시 해당 구간의 roast area index 표시
- **Color Change와 First Crack 이벤트 마킹 후에만 표시**

#### 이벤트 마커
- **수직선 + 라벨**로 표시 (Scott Rao 분석 확인)
- 수동 마킹: 차트 아무 곳이나 클릭 → 코멘트 박스
- 자동 마킹: BT 임계온도 기반 (Color Change·FC·SC)

---

### 6.12 RoasTime 차트 심화 (Aillio Bullet 전용)

#### 핵심 특징: 듀얼 센서 = 4개 커브

RoasTime만의 독보적 특징 — BT 측정 센서가 2개:

| 커브 | 약어 | 색상(RT2) | 설명 |
|------|------|-----------|------|
| IBTS Temperature | I-Temp | **파랑** | 적외선 원두온도 (즉각 반응) |
| Bean Probe Temperature | B-Temp | **보라** | 접촉식 프로브 (30~60초 지연) |
| IBTS RoR | I-RoR | **주황**(RT4) / 빨강(RT2) | IBTS 기반 ROR |
| Bean Probe RoR | B-RoR | **초록** | 프로브 기반 ROR |

#### IBTS vs 접촉식 프로브의 차이

| 항목 | IBTS | 접촉 프로브 |
|------|------|-----------|
| 측정 방식 | 적외선 비접촉 | 열전대 접촉 |
| 응답 속도 | 즉각 | 30~60초 지연 |
| 터닝포인트 | **거의 없음** (선형에 가까운 상승) | 명확한 저점 존재 |
| FC 온도 (300g 기준) | **~204°C** | **~165°C** (약 40°C 차이) |
| 배치 크기 영향 | 거의 없음 | 30°C 이상 편차 가능 |

→ 800g 이상 대량 배치에서 B-Temp와 IBTS 커브가 **교차** 발생

#### 페이즈 바 (Phase Bar)
- 차트 **상단**에 가로 바 형태로 표시
- 옐로잉 + FC 마킹 후 자동 생성
- 건조/마이야르/발달 3구간 + 각 시간·비율

#### 컨트롤 액션 바
- 차트 **하단**에 P(Power)/F(Fan)/D(Drum) 변경 이력 표시
- 각 변경 시점을 색상으로 구분한 타임라인

#### IBTS 페이즈 (RoasTime 4 고급 기능)
- IBTS 온도 구간을 3개 레이어로 색상 구분
- 사용자 정의 온도 임계값으로 더 세밀한 시각화
