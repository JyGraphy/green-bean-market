-- ET(드럼 내부 온도) 시계열 컬럼 추가
alter table public.roasting_profiles
  add column if not exists et_series numeric[];   -- 드럼 내부온도 배열 °C
