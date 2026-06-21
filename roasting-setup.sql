-- ════════════════════════════════════════════════════════════════
-- 로스팅 프로파일 테이블 (roasting_profiles)
-- 클릭 디지타이징으로 생성한 프로파일 + DTR + 로스팅 포인트 분석 저장
-- ════════════════════════════════════════════════════════════════

create table if not exists public.roasting_profiles (
  id                  bigint generated always as identity primary key,
  user_id             uuid references auth.users(id) on delete cascade not null,

  -- 필수
  bean_name           text not null,                 -- 생두 이름

  -- 선택 (메타)
  seller              text,                          -- 생두 판매사
  ambient_temp        numeric,                       -- 실내 온도 °C
  ambient_humidity    numeric,                       -- 실내 습도 %
  roast_date          date,
  memo                text,

  -- 계산/분석 결과
  charge_temp         numeric,                       -- 투입온도 °C
  drop_temp           numeric,                       -- 배출온도 °C
  total_time          numeric,                       -- 총 시간 (초)
  dtr                 numeric,                       -- Development Time Ratio %
  current_roast_point text,                          -- 분석된 현재 로스팅 포인트
  target_roast_point  text,                          -- 사용자가 원하는 다음 포인트

  -- 시계열 (디지타이징 결과, CHARGE 기준 초)
  time_series         numeric[],                     -- 시간 배열 (초)
  bt_series           numeric[],                     -- 원두온도 배열 °C

  -- 이벤트 (초 단위) — { charge, tp, dryend, fcs, fce, scs, drop }
  events              jsonb default '{}'::jsonb,

  created_at          timestamptz default now()
);

-- ── RLS ──
alter table public.roasting_profiles enable row level security;

create policy "users see own roasting profiles"
  on public.roasting_profiles for select
  using (auth.uid() = user_id);

create policy "users insert own roasting profiles"
  on public.roasting_profiles for insert
  with check (auth.uid() = user_id);

create policy "users update own roasting profiles"
  on public.roasting_profiles for update
  using (auth.uid() = user_id);

create policy "users delete own roasting profiles"
  on public.roasting_profiles for delete
  using (auth.uid() = user_id);
