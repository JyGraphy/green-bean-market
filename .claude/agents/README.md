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

## ⚠️ 이 환경의 네트워크 제약 (2026-08-02 실측)

| 수단 | 상태 | 비고 |
|------|------|------|
| `WebSearch` | ✅ 정상 | Anthropic 서버에서 실행 — 샌드박스 프록시를 타지 않음 |
| `WebFetch` | ❌ 403 | 위키백과 포함 **모든 호스트** 차단 |
| `curl` / 직접 outbound | ❌ 403 | `CONNECT tunnel failed` — 환경 네트워크 정책 |
| GitHub (git push/pull) | ✅ 정상 | 전용 프록시 경유 |

**따라서 리서치팀은 WebSearch를 주력으로 쓴다.** 각 에이전트 정의의 "네트워크 제약 프로토콜"을 따를 것:
본문을 못 읽어 확인 불가한 값은 **"미확인(본문 접근 차단)"**으로 표기하고, **절대 지어내지 않는다.**
그래도 만들 수 있는 산출물(일정표, 후보 목록, 출처 카탈로그)은 반드시 만들어 낸다 — 빈손 퇴근은 실패다.

> 근본 해결: 환경의 네트워크 정책을 열면(허용 도메인 추가) WebFetch가 살아나고 리서치 품질이 크게 올라간다.
> 정책은 환경 생성 시 선택한 값이며 소유자만 변경할 수 있다.

## 🧠 세컨드 브레인 (vault/) — 산출물이 쌓이는 곳

모든 보고서는 **`vault/`** 에 저장한다. 옵시디언으로 열면 읽기는 완전 무료다.

| 폴더 | 역할 | 규칙 |
|------|------|------|
| `vault/raw/` | **IN** — 수집한 원본 | 수정 금지. 에이전트는 여기에만 쓴다 |
| `vault/wiki/` | **OUT** — 정리된 지식 | 주제당 파일 하나. 새 정보가 오면 **갱신** |

에이전트별 저장 위치: `raw/coe/` · `raw/stores/` · `raw/qa/` · `raw/papers/` · `raw/roast-profiles/`

정리 규칙은 **`vault/CLAUDE.md`** 에 있다. 목차는 스크립트가 만든다:

```bash
python3 scripts/build_wiki_index.py   # vault/wiki/index.md 재생성 — 토큰 0
```

> 토큰 절약 팁: raw 전체를 다시 읽히지 말고 **새로 들어온 문서만** 지정해 정리시킨다.
> `--check`는 wiki에 반영 안 된 raw가 있으면 exit 1을 낸다.

## 🥇 1순위 원칙 — 스크립트로 되는 일에 AI를 쓰지 않는다

**가장 큰 토큰 절감은 더 싼 모델이 아니라 "모델을 아예 안 부르는 것"이다.**

```bash
python3 scripts/qa_report.py     # 검수부서 보고서 2건 생성 — 토큰 0
```

이 스크립트가 데이터 검증(중복ID·URL·스키마·가격 이상치·문서 드리프트)과
스크래퍼 규칙 점검(guard·ID발급·절대URL·가공방식·금지패턴)을 전부 수행하고
REPORT-FORMAT 규격의 마크다운까지 써낸다. **AI 토큰 0.**

| 단계 | 수단 | 비용 |
|------|------|------|
| ① 기계적 검사 | `scripts/qa_report.py` | **0** |
| ② ①이 ❌를 뱉었을 때만 | data-validator / scraper-checker (haiku) | 소 |
| ③ 설계·판단이 필요할 때만 | 사장님과 대화 (opus) | 대 |

`qa_report.py --check`는 문제가 있을 때만 exit 1을 낸다. 루틴은 이 종료코드를 보고
**문제가 있을 때만** AI를 호출한다. 이상 없으면 그날 검수부서 토큰은 0이다.

> 새 검사 항목이 생기면 **먼저 "정규식·계산으로 되는가"를 묻고**, 된다면 에이전트가 아니라
> `qa_report.py`에 추가한다. AI는 "코드를 읽고 판단해야 하는 것"에만 쓴다.

## 💰 모델 배치 (토큰 비용 최적화)

작업 성격에 맞는 모델을 각 정의 파일의 `model:` 프런트매터로 지정한다.

| 모델 | 담당 | 이유 |
|------|------|------|
| **haiku** (저비용) | store-scout, roast-profile-collector, data-validator, frontend-reviewer | 검색·목록화·기계적 검사 — 판단보다 수집이 핵심 |
| **sonnet** (중간) | coe-auction-reporter, coffee-research-translator, scraper-checker, new-store-onboarder | 교차 검증·번역 품질·코드 판단이 필요 |
| **opus** | (기본 미배정) | 사장님이 직접 지시하는 설계·의사결정 세션에서만 |

**수집과 정리를 분리하면 비용이 크게 준다** — haiku가 원자료를 `research/raw/`에 모으고,
sonnet이 그걸 읽어 보고서로 정리하는 2단 구조가 기본이다.

## 📄 보고서 규격

모든 보고서는 **`.claude/agents/REPORT-FORMAT.md`** 규격을 따른다.
핵심: 결론 3줄 → 사장님 결정 필요 항목 → 표 중심 본문 → 출처(신뢰등급 표기).
본문 4,000자 상한, 원자료는 보고서에 붙이지 말고 `research/raw/`에 두고 링크만.

## 운영 원칙

- 발굴(scout)과 추가(onboarder)는 분리되어 있다. **scout 보고 → 사용자 컨펌 → onboarder 실행** 순서를 지킨다.
- 리서치 산출물은 `docs/`, 수집 데이터는 `research/`에 쌓인다.
- **현황판 갱신**: 에이전트가 산출물을 만들면 `agents.js`(AGENT HQ 현황판 명부)의 `LOGS` 맨 위에 기록을 한 줄 추가하고, 해당 에이전트의 `lastWork`를 갱신한다. 쓰기 도구가 없는 검수팀의 보고는 메인 세션이 대신 기록한다. 현황판은 `hq/agents.js` 명부 기반의 `hq/agents.html` — **운영자 내부 전용**으로 `.vercelignore`에 의해 유저 사이트에는 배포되지 않으며, 명부가 바뀌면 아티팩트로 재게시해 사용자에게 보여준다.
- 에이전트는 세션에서 호출될 때 실행된다. 정기 자동 보고(예: 매주 COE 체크)를 원하면 Claude Code의 스케줄 기능(Routine)에 연결할 수 있다.
