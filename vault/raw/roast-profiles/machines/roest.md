# ROEST 샘플 로스터 (노르웨이) — 확인된 모델: S100, S200, L200

<!-- 신규 등록 (2026-09-01). 사장님 보유 기기는 아니지만, 학술 논문(PMC8854711)이
     기기명을 명시한 실제 로스팅 파라미터를 제공해 등록했다. 실측 이미지 검증은 아직 없어
     verified: no. -->

- heat_source: 하이브리드 — 열풍(대류)을 주 열원으로 쓰되 원두를 띄우지 않고(NOT fluid-bed)
  회전 드럼으로 교반하는 "stirred-drum" 방식. 제조사(및 판매처) 설명: "hot air roaster +
  conventional open drum의 결합", "fluid-bed와 drum roaster의 장점을 결합한 하이브리드"
- temp_probe: BT+ET 추정 + inlet(유입 공기) 센서 + 자동 1차크랙 감지 센서 — 검색 요약 기준,
  이 세션에서 공식 페이지 원문 직접 확인은 못함(아래 '검증 대기' 참고)
- typical_total_time: 6–7분 (n=1 학술 논문 기준, ROEST 공식 typical range 아님 — 아래 판독 규칙 참고)
- chart_app: ROEST 자체 앱(터치 컨트롤러+클라우드 프로파일 라이브러리로 알려짐, 세부 미확인)
- verified: no

## 모델 표기 근거 (2026-09-01, verify_machines.py 가 잡아냄)

- **S100** — Zarebska et al. 2022 (Sci Rep, PMC8854711) 본문에 "ROEST S100 sample roaster"로
  명시. 우리 profiles/roest-guatemala-*.json 2건의 근거이기도 하다.
- **S200 / L200** — 2026-09-01 수집한 ROEST 공식 페이지에 등장하는 현행 모델.
- 최초 등록 시 제목에 적었던 "S100 Plus", "L100" 은 **논문에도 공식 페이지에도 없다.**
  출처 없이 쓴 것이라 제거했다. 모델 라인업을 추측으로 넓히지 말 것.
- 우리가 가진 실측 프로파일 2건은 **S100 한 대 기준**이다. S200/L200 에 그대로 적용해도
  되는지는 확인된 바 없다.

## 판독 규칙

- This is a SMALL-BATCH ELECTRIC sample roaster (batch capacity reported as 50–200g), NOT a
  commercial drum roaster. Do not apply Probat/Loring/Giesen-scale batch or timing assumptions.
- Heat transfer is described (by manufacturer/reseller sources) as a HYBRID: primarily hot-air
  convection, but beans are tumbled by a rotating drum rather than fluidized/lifted by airflow
  the way IKAWA's fluid-bed works. Treat this as its OWN category — do not apply IKAWA's
  fluid-bed rules (e.g. "no BT probe") automatically; ROEST is reported to have both BT and ET
  probes plus an inlet-air sensor, unlike IKAWA which has no bean probe.
- OBSERVED PROFILE RANGE (n=1 documented profile config, single academic source, applied to 2
  origins — see profiles/roest-guatemala-*.json): roast start (read) temperature ~165°C, drop
  temperature ~205°C, total roast time 6–7 min, development time (first-crack-to-drop) fixed at
  53 sec by the researchers' controlled protocol. Do NOT treat 6–7 min as ROEST's universal
  range — this is ONE lab's fixed settings for ONE study, not a manufacturer-published range.
  If a chart shows a very different total time (e.g. 3 min or 12+ min), do not force it toward
  6–7 min — ROEST profiles are fully user-programmable and vary widely between users.
- Because this is a low-thermal-mass small-batch machine, expect FASTER BT response to heater/
  airflow changes than a multi-kg drum roaster, but slower than IKAWA's fluid-bed (which has
  no drum mass at all).
- No confirmed proprietary chart color scheme was found — read on-image legend, do not assume
  fixed BT/ET colors.
- When in doubt, prefer "미확인" over inventing a number — this machine has no verified chart
  test yet (see 검증 대기 below).

## 근거

- [The effect of roast profiles on the dynamics of titratable acidity during coffee roasting — Anokye-Bempah et al. 2024, Scientific Reports (PMC11002029)](https://europepmc.org/article/PMC/PMC11002029)
  — 이 논문은 Probat P5 를 썼다(무관). ROEST 근거는 아래 별도 논문.
- [Comparison of chemical compounds and their influence on the taste of coffee depending on green
  beans storage conditions — Zarebska et al. 2022, Scientific Reports (PMC8854711)](https://europepmc.org/article/PMC/PMC8854711)
  — "A ROEST S100 sample roaster ... maintained the following conditions: roasting start
  temperature: 165 °C, final temperature: 205 °C, roasting time: 6–7 min with a fixed airflow
  and heater setting, and development time: 53 s." 원문 직접 인용, vault/raw/papers/fulltext/
  에 이미 받아둔 논문에서 확인.
- 검색 요약(세션 WebFetch 차단, 원문 미확인) — 하이브리드 드럼/50–200g 배치/BT+ET+inlet+1차크랙
  감지 서술은 ROEST 공식 페이지·리셀러 페이지에서 반복 확인되나, 이 세션에서 원문을 직접 열지
  못했다. 대기열(_수집대기.md)에 공식 페이지 등록.
- 검증 대기 — 실제 ROEST 차트 이미지로 아직 테스트하지 못함. heat_source/temp_probe 세부는
  공식 원문 확인 전까지 "검색 요약 기반"으로 취급할 것.
