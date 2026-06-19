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

## 핵심 요약 (피드백 체크리스트)
1. ROR이 끝까지 매끄럽게 감소하는가? (crash/flick/정체 없음)
2. DTR이 목표 범위인가 (라이트 18~20%, 일반 20~25%) — 단 ROR 형태 우선
3. Agtron 색도가 목표 로스트와 일치하는가
4. 무게손실%가 로스트 정도에 맞고 배치 간 ±0.5% 이내인가
5. 컵노트가 언더(풋내·땅콩)/베이크드(플랫·종이)/오버(재·쓴맛) 신호인가
