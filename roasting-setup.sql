-- roasting_profiles 테이블
create table if not exists public.roasting_profiles (
  id               bigint generated always as identity primary key,
  user_id          uuid references auth.users(id) on delete cascade not null,
  bean_name        text not null,
  roastery         text,
  roast_date       date,
  green_weight     numeric,      -- 투입량 g
  roasted_weight   numeric,      -- 배출량 g
  charge_temp      numeric,      -- 투입온도 °C
  drop_temp        numeric,      -- 배출온도 °C
  total_time       numeric,      -- 총 시간 초
  agtron           numeric,
  ambient_temp     numeric,
  ambient_humidity numeric,
  memo             text,
  -- 이벤트 포인트 (초)
  e_charge         numeric default 0,
  e_tp             numeric,
  e_dry_end        numeric,
  e_fcs            numeric,      -- 1차 크랙 시작
  e_fce            numeric,      -- 1차 크랙 종료
  e_scs            numeric,      -- 2차 크랙 시작
  e_drop           numeric,
  -- 시계열 데이터
  bt_series        numeric[],    -- Bean Temp array
  et_series        numeric[],    -- Env Temp array
  created_at       timestamptz default now()
);

-- RLS
alter table public.roasting_profiles enable row level security;

create policy "users see own profiles"
  on public.roasting_profiles for select
  using (auth.uid() = user_id);

create policy "users insert own profiles"
  on public.roasting_profiles for insert
  with check (auth.uid() = user_id);

create policy "users update own profiles"
  on public.roasting_profiles for update
  using (auth.uid() = user_id);

create policy "users delete own profiles"
  on public.roasting_profiles for delete
  using (auth.uid() = user_id);
