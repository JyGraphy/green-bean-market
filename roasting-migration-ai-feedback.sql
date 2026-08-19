-- ════════════════════════════════════════════════════════════════
-- 로스팅 AI 자동 학습용 컬럼 추가
--
-- 목적: 지금은 AI(analyze-roast)가 차트에서 읽어낸 값이 마법사를 거치며 사용자에게
-- 수정된 뒤, **최종값만** 저장되고 AI의 원래 판독은 버려진다.
-- 그런데 "AI가 뭐라고 읽었는가"와 "사용자가 무엇을 고쳤는가"의 차이야말로
-- AI를 똑똑하게 만드는 유일한 학습 신호다. 그 신호를 보존하기 위한 컬럼들이다.
--
-- scripts/roast_feedback.py 가 이 컬럼들을 읽어 기기별 오차 패턴을 뽑아내고,
-- build_roast_knowledge.py 가 그 패턴을 판독 규칙으로 프롬프트에 주입한다.
-- ════════════════════════════════════════════════════════════════

alter table public.roasting_profiles
  -- AI가 반환한 원본 JSON 전체 (curves·events·labeled_points 포함)
  add column if not exists ai_raw          jsonb,
  -- AI가 스스로 매긴 신뢰도: high | medium | low
  add column if not exists ai_confidence   text,
  -- AI가 판독한 로스터기 (notes의 "machine: ..." 에서 추출). 사용자가 고른 roaster 와
  -- 다르면 그 자체가 기기 오인 사례다.
  add column if not exists ai_machine      text,
  -- 판독에 쓰인 입력 종류: photo | photo+datafile | datafile
  add column if not exists ai_input_kind   text;

-- 학습 분석 쿼리가 기기·날짜로 훑으므로 인덱스를 둔다.
create index if not exists roasting_profiles_ai_machine_idx
  on public.roasting_profiles (ai_machine, created_at desc);

comment on column public.roasting_profiles.ai_raw is
  'analyze-roast 원본 응답. 사용자 수정 전 값 — 학습 신호의 원천이므로 덮어쓰지 말 것.';
