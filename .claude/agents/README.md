# AI 직원 (Claude Code 서브에이전트)

이 폴더의 마크다운 파일 1개 = AI 직원 1명. Claude Code 세션에서 "OOO 시켜줘"라고 하면 해당 에이전트가 자기 프롬프트와 도구 권한으로 일한다.

## 검수팀 (읽기 전용 — 코드/데이터를 고치지 않고 보고만)

| 직원 | 역할 | 호출 예시 |
|------|------|-----------|
| `scraper-checker` | 스크래퍼가 안전장치 규칙(guard, alloc_ids, abs_url 등)을 지키는지 점검 | "scraper-checker로 새 스크래퍼 점검해줘" |
| `data-validator` | 상품 데이터 스키마·중복 ID·URL·급감 검사 | "data-validator 돌려줘" |
| `frontend-reviewer` | 배지 색상·필터·정렬·반응형 등 화면 변경 리뷰 | "frontend-reviewer로 이번 변경 리뷰해줘" |

## 실무팀

| 직원 | 역할 | 호출 예시 |
|------|------|-----------|
| `store-scout` | 새 생두 쇼핑몰 발굴 → 후보 보고서 작성. **데이터 추가는 안 함** | "store-scout로 새 생두사 찾아줘" |
| `new-store-onboarder` | 사용자가 **승인한** 공급사만 실제 추가(스크래퍼+프론트 3종 세트) | "OO몰 승인, onboarder로 추가해줘" |

## 리서치팀

| 직원 | 역할 | 호출 예시 |
|------|------|-----------|
| `coe-auction-reporter` | 각국 COE 옥션 일정·결과를 표로 정리 보고 | "COE 리포트 만들어줘" |
| `roast-profile-collector` | 로스터기 프로파일 학습 데이터 수집(출처·라이선스 검증 필수) | "IKAWA 프로파일 데이터 수집해줘" |
| `coffee-research-translator` | 커피 논문을 찾아 한글로 번역·정리 | "로스팅 관련 최신 논문 번역해줘" |

## 운영 원칙

- 발굴(scout)과 추가(onboarder)는 분리되어 있다. **scout 보고 → 사용자 컨펌 → onboarder 실행** 순서를 지킨다.
- 리서치 산출물은 `docs/`, 수집 데이터는 `research/`에 쌓인다.
- **현황판 갱신**: 에이전트가 산출물을 만들면 `agents.js`(AGENT HQ 현황판 명부)의 `LOGS` 맨 위에 기록을 한 줄 추가하고, 해당 에이전트의 `lastWork`를 갱신한다. 쓰기 도구가 없는 검수팀의 보고는 메인 세션이 대신 기록한다. 현황판은 `hq/agents.js` 명부 기반의 `hq/agents.html` — **운영자 내부 전용**으로 `.vercelignore`에 의해 유저 사이트에는 배포되지 않으며, 명부가 바뀌면 아티팩트로 재게시해 사용자에게 보여준다.
- 에이전트는 세션에서 호출될 때 실행된다. 정기 자동 보고(예: 매주 COE 체크)를 원하면 Claude Code의 스케줄 기능(Routine)에 연결할 수 있다.
