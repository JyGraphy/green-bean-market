-- ET(드럼 내부 온도) + 교반(agitation) 시계열 컬럼 추가
alter table public.roasting_profiles
  add column if not exists et_series         numeric[],   -- 드럼 내부온도 배열 °C
  add column if not exists agitation_series  numeric[];   -- 교반 단계 배열 (0–10)

-- 추가 컬럼
alter table public.roasting_profiles
  add column if not exists et_drop_temp    numeric,
  add column if not exists charge_weight   numeric,
  add column if not exists drop_weight     numeric,
  add column if not exists weight_loss     numeric,
  add column if not exists et_ror_series   numeric[];
