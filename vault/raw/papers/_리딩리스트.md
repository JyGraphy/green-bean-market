# 커피 논문 리딩 리스트 (본문 접근이 열리면 정독할 후보)

> 최종 갱신: 2026-08-02
> 이 환경은 WebFetch/curl이 전 사이트 403으로 차단돼 있어 **초록·검색 요약 수준까지만** 확인했습니다.
> 아래 논문들은 전문(PDF/HTML) 접근이 가능해지면 정독·정리할 후보입니다.
> 상태 표기: `미착수` / `초록 확인` / `정리 완료`

---

## 이미 정리한 논문

| 논문 | 상태 | 정리본 |
|---|---|---|
| A universal color curve for roasted arabica coffee (Sci Rep, 2025) | 초록 기반 정리 완료 | [2026-08-02-roast-color-universal-curve.md](./2026-08-02-roast-color-universal-curve.md) |
| The effect of roast profiles on the dynamics of titratable acidity during coffee roasting (Sci Rep, 2024) | 초록 기반 정리 완료 | [2026-08-02-roast-profile-titratable-acidity.md](./2026-08-02-roast-profile-titratable-acidity.md) |

**두 정리본에서 반드시 보강해야 할 항목**
- 색 곡선 논문: 2차 크랙에서의 L\*a\*b\* 값, 다항 회귀식 계수, 색도계 기기·측정 조건, 홀빈/분쇄 구분
- TA 논문: 프로파일별 전체 TA 곡선 수치, 적정(titration) 프로토콜 상세, 관능평가 포함 여부, 프로파일별 1차 크랙 발생 시각

---

## 1. Developing Roast Color Standards for the Specialty Coffee Industry (SCA 백서, 2025-10-30)

- URL: https://static1.squarespace.com/static/584f6bbef5e23149e5522201/t/69033dc059316a64ee34b7c5/1761820096879/SCA_Roast+Color+White+Paper_Oct302025_SECURED.pdf
- 종류: SCA 발간 백서 (동료심사 논문 아님)
- 상태: `미착수`
- **왜 중요한가**: 위 "보편 색 곡선" 연구가 실제 **업계 표준**으로 옮겨가는 문서. SCA가 가시광 측정 기반 로스팅 레벨 표준을 준비 중이며 2025년 말 전문가 그룹 검토 예정. **우리 상품 페이지의 로스팅 레벨 표기·생두별 로스팅 가이드를 어떤 스케일로 적을지**가 여기서 결정된다. 확정 전에 미리 읽어두면 선제 대응 가능.

## 2. Predicting the flavor potential of green coffee beans with machine learning-assisted visible/near-infrared hyperspectral imaging (Vis-NIR HSI): Batch effect removal and few-shot learning framework

- 저널: Food Control (Elsevier), 2025
- URL: https://www.sciencedirect.com/science/article/abs/pii/S0956713525001793
- 라이선스: **구독 저널 추정 → 초록·공개 부분만 참고, 전문 번역 금지**
- 상태: `미착수`
- **왜 중요한가**: **생두를 볶지 않고** 초분광 영상으로 "맛 잠재력(flavor potential)"을 예측하는 프레임워크. 생두 소싱·품질 선별의 미래 도구. 배치 효과(batch effect) 제거와 few-shot 학습을 다뤄, 샘플 수가 적은 소규모 로스터리 환경에도 적용 여지가 있다.

## 3. Large dataset on Fourier transform near infrared (FT-NIR) spectroscopy of green and roasted specialty coffee

- 저자: Andrés F. Bahamón-Monje, Ever M. Morales-Angulo, Gentil A. Collazos-Escobar, Nelson Gutiérrez-Guzmán
- 저널: Data in Brief, 2025년 5월 (접수 2025-02-20, 게재확정 2025-04-25)
- URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC12142347/
- 라이선스: 오픈액세스 (Data in Brief, 통상 CC BY — 확인 필요)
- 상태: `미착수`
- **왜 중요한가**: **생두 스펙트럼으로 로스팅 후 관능 점수를 예측**하려는 공개 데이터셋. SCA 프로토콜 기반 관능 점수가 함께 제공된다. 기기: Spectrum Two N-FT-NIR(InGaAs 검출기), 12,000~4,000 cm⁻¹. 전처리(SNV, MSC, 미분) 데이터 포함 → **직접 모델을 돌려볼 수 있는 실물 데이터**라 우리 사이트에 "생두 품질 예측" 기능을 붙일 때 출발점이 된다.

## 4. Natural versus *Saccharomyces boulardii* self-induced anaerobic coffee fermentation: Effects on physicochemical properties and microbial ecology, and their influence on volatile profiles and sensory attributes across roast levels

- 발행: 2025 (PubMed ID 40413948)
- URL: https://pubmed.ncbi.nlm.nih.gov/40413948/
- 상태: `초록 확인` (초록 수준 수치 일부 확보)
- 확보된 수치: 휘발성 화합물 **207종** 검출, 라이트 로스팅에서 두 처리 간 유의차 화합물이 가장 많음. 커핑 점수 — 라이트 로스팅에서 **NSIAF 82.08 ± 0.14 vs SSIAF 81.58 ± 0.14** (둘 다 스페셜티 기준 80점 이상)
- **왜 중요한가**: 우리 사이트의 `무산소발효(anaerobic)` 가공방식 배지가 실제로 무엇을 의미하는지 설명할 근거. **자연발효 vs 스타터(효모) 접종 발효**의 차이를 "복합성 vs 일관성"으로 정리해준다. 또한 **로스팅 레벨에 따라 발효 차이가 드러나는 정도가 다르다**는 점은 무산소발효 생두를 어느 로스팅 레벨로 볶아야 하는지에 직결된다.

## 5. Unraveling the impact of coffee fermentation: Interactions among processing variables and their effects on sensory quality

- 저널: Trends in Food Science & Technology (Elsevier), 2025
- URL: https://www.sciencedirect.com/science/article/abs/pii/S0924224425002870
- 라이선스: **구독 저널 추정 → 요약 번역만**
- 상태: `초록 확인`
- 확보된 수치: 자연발효·스타터 접종 발효 모두 **SCA 점수를 0.6~1.4점 상승**시킴. 최대 개선은 **장시간(≥121시간) 세미카보닉(semicarbonic) 발효 + 아스퍼전(aspersion) 시스템 + 세미드라이/웻 프로세스** 조합
- **왜 중요한가**: 가공 변수(시간·온도·용기·접종)의 **상호작용**을 정리한 리뷰. 생두 상세 설명에 "왜 이 가공이 비싼가"를 설명할 근거 자료로 유용.

## 6. Review of Factors Affecting Development of Sensory Attributes of Coffee

- 저자: Nguyen 외
- 저널: Journal of Sensory Studies (Wiley), 2025
- URL: https://onlinelibrary.wiley.com/doi/10.1111/joss.70098
- 라이선스: **구독 저널 추정**
- 상태: `미착수`
- **왜 중요한가**: 로스팅이 향미를 결정하는 최대 요인임을 전제로, **등온(isothermal) 프로파일 vs 동적으로 변하는 RoR 프로파일**의 반응속도론(kinetics)과 관능 영향을 정리한 리뷰. IKAWA 프로파일 설계의 이론적 배경을 한 번에 훑기 좋다.

## 7. The Effect of Roast Development Time Modulations on the Sensory Profile and Chemical Composition of the Coffee Brew as Measured by NMR and DHS-GC–MS

- 저널: Beverages (MDPI), 2020, 6(4), 70
- URL: https://doi.org/10.3390/beverages6040070
- 라이선스: **오픈액세스 (MDPI, CC BY)** → 폭넓은 번역 가능
- 상태: `초록 확인`
- 확보된 내용: **짧은 개발시간(development time)은 과일향·단맛·산미를 높이고, 긴 개발시간은 로스티·너티·쓴맛 쪽으로 균형이 이동**한다
- **왜 중요한가**: 2020년으로 다소 오래됐지만 **개발시간(DTR) 미세 조정의 효과**를 관능+NMR+GC-MS로 삼중 검증한 드문 연구. 오픈액세스라 전문 번역이 가능해 **가성비가 가장 높은 후보**. IKAWA 프로파일에서 1차 크랙 이후 구간을 몇 초 늘릴지 결정하는 데 직접 쓰인다.

## 8. Effect of Roasting Level on the Development of Key Aroma-Active Compounds in Coffee

- 저널: Molecules (MDPI), 2024, 29(19), 4723
- URL: https://www.mdpi.com/1420-3049/29/19/4723
- 라이선스: **오픈액세스 (MDPI, CC BY)**
- 상태: `미착수`
- **왜 중요한가**: 로스팅 단계별로 **핵심 향기활성 화합물(aroma-active compounds)**이 어떻게 생성·소멸하는지 정리. 위 "보편 색 곡선"과 결합하면 **"L\* 몇에서 어떤 향이 정점인가"**를 연결할 수 있다.

## 9. Comprehensive evaluation of volatile compounds and sensory profiles of coffee throughout the roasting process

- 저널: Food Chemistry (Elsevier), 2025
- URL: https://www.sciencedirect.com/science/article/abs/pii/S0308814625008374
- 라이선스: **구독 저널 추정 → 요약 번역만**
- 상태: `초록 확인`
- 확보된 내용: 휘발성 화합물과 관능 속성으로 **최적 로스팅 시점**을 특정할 수 있으며, **알데하이드류(aldehydes)가 이상적 로스팅 포인트의 잠재적 지표**
- **왜 중요한가**: "언제 배출할 것인가"를 화학 지표로 판정하려는 시도. 실무에서 바로 쓰긴 어렵지만, 배출 판단 기준을 논리적으로 세우는 데 참고.

## 10. Sensory profiles of Robusta coffee (Coffea canephora) genetic resources from the Democratic Republic of the Congo

- 저널: Frontiers in Sustainable Food Systems, 2024
- URL: https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2024.1382976/full
- 라이선스: **오픈액세스 (Frontiers, CC BY)**
- 상태: `미착수`
- **왜 중요한가**: **IKAWA Sample Roaster V2 Pro로 미디엄 로스팅 프로파일을 개발하고 색도계로 검증**한 연구. 우리가 쓰는 장비와 동일 계열이라 **IKAWA 프로파일 설계·검증 방법론을 그대로 참고**할 수 있다. 또한 사이트에 콩고민주공화국 생두가 있으므로 상품 설명 근거로도 활용 가능.

## 11. Near-Infrared Spectroscopy-Based Discriminant Analysis for the Classification of Coffee Quality in Dry Parchment and Green Coffee

- 저널: Molecules (MDPI)
- DOI: 10.3390/molecules31091395
- 상태: `미착수` (발행연도·권호 재확인 필요)
- **왜 중요한가**: **파치먼트 단계에서 이미 품질 등급 분류가 가능한지**를 다룬다. 생두 구매 시점보다 앞선 단계의 품질 예측 → 소싱 리스크 관리 관점에서 유용.

---

## 다음 탐색 키워드 메모

- `coffee roasting fluid bed vs drum flavor comparison 2025` — IKAWA(유동층) 대 드럼 로스터의 향미 차이
- `development time ratio DTR sensory experiment sample roaster` — DTR 정량 연구
- `post-roast degassing maturation sensory days` — 로스팅 후 숙성 기간 (MDPI Proceedings 109(1), 8번 논문 관련)
- `green coffee moisture water activity storage quality Korea` — 생두 보관·수분활성도
- `coffee acrylamide roasting speed Coffea canephora` — 로스팅 속도와 아크릴아마이드 (MDPI Proceedings 109(1), 7)
