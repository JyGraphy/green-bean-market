# 실제 로스팅 프로파일 수집 — 규격과 원칙

기기 사양(`../machines/`)이 아니라 **실제로 로스팅한 결과 곡선**을 모으는 자리다.

## 왜 따로 모으나

`machines/*.md` 는 "이 기기는 이렇게 읽어라"는 **판독 규칙**이다.
여기 모으는 건 "실제로 이런 값이 나온다"는 **실측 분포**다. 둘은 쓰임이 다르다.

실측 분포가 있으면 AI가 판독 결과를 **자기 검증**할 수 있다.
예: "IKAWA Pro 50 인데 총 시간 18분으로 읽혔다" → 실측 분포와 크게 어긋나므로
confidence 를 낮추고 notes 에 근거를 적는다. 지금은 이 대조군이 없어서
말도 안 되는 판독도 그대로 통과한다.

## 절대 규칙

1. **곡선 수치를 지어내지 않는다.** 검색 요약에서 "대략 이렇다"로 추정한 값은
   저장 금지다. 한 번 들어가면 이후 모든 학습이 그 위에 쌓인다.
2. **기기를 모르면 저장하지 않는다.** 어떤 로스터기로 볶았는지 모르는 곡선은
   기기별 판독에 쓸 수 없다 — 이 프로젝트에서는 가치가 없다.
3. **출처 URL 이 없으면 저장하지 않는다.** 나중에 되짚을 수 없는 값은 증거가 아니다.
4. 그래프 이미지에서 눈으로 읽은 값은 `source_type` 에 `+chart-read` 를 붙이고
   판독 오차를 `notes` 에 명시한다.
5. 단위 변환(°F→°C)을 했으면 반드시 기록한다.
6. 저장 정책은 `../_수집대기.md` 의 '저장 정책' 절을 따른다 — 원문 전재 금지.

## 파일 규격

프로파일 1건 = JSON 파일 1개. 파일명 `<기기키>-<간단한식별자>.json`.

```json
{
  "source_url": "https://…",
  "source_type": "manufacturer-published | roaster-published | academic | community",
  "collected_at": "2026-09-01",
  "license_note": "재배포 가능 여부·인용 조건",
  "machine": "ikawa-pro",
  "machine_stated_as": "출처에 적힌 그대로의 기기명",
  "batch_size_g": 50,
  "bean": { "origin": "", "process": "", "variety": "" },
  "curve": [ { "t_sec": 0, "temp_c": 0, "ror": null } ],
  "events": { "charge": 0, "dry_end": null, "first_crack": null, "drop": 0 },
  "notes": "판독 방법·오차·불확실한 항목"
}
```

- `machine` 은 `../machines/<키>.md` 파일명과 **똑같이** 쓴다. 등록 안 된 기기면
  먼저 기기 문서를 만들거나, 최소한 `machine_stated_as` 에 원문 표기를 남긴다.
- `curve` 를 통째로 못 얻고 이벤트 시점·온도만 얻었다면 `curve` 는 비우고
  `events` 와 온도만 채운다. **부분 정보도 분포 산출에는 쓸모가 있다.**

## 수집 우선순위

1. **사장님 보유 기기** — IKAWA Pro 50 · Stronghold S7X · EASYSTER 800G.
   실물 차트로 검증까지 갈 수 있는 유일한 기기들이다.
2. 유명 로스터·대회(WCRC 등)가 **기기를 명시해** 공개한 프로파일
3. 학술 논문에 실린 곡선 (기기 명시 필수)
4. 커뮤니티 공개 프로파일 (기기 명시 + 수치 확인 가능할 때만)

## 여기서 나온 결과를 어떻게 학습에 쓰나

`scripts/build_roast_knowledge.py` 가 기기 문서를 프롬프트에 주입한다.
실측 분포는 그 기기 문서의 `## 판독 규칙` 에 **범위 문장**으로 옮겨 적는다.
예: "Observed IKAWA Pro 50 profiles: total 6–9 min, drop 195–225°C (n=4, sources
listed in profiles/)". 표본 수(n)와 출처를 반드시 함께 적어 과신을 막는다.
