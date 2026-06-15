-- Supabase SQL Editor에서 실행하세요
-- https://supabase.com/dashboard/project/txnpbzukavajwbmggpfk/sql

-- 1. profiles 테이블
CREATE TABLE IF NOT EXISTS public.profiles (
  id          UUID        REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  username    TEXT        UNIQUE NOT NULL,
  nickname    TEXT        NOT NULL,
  email       TEXT,                          -- 실제 이메일 (선택)
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Row Level Security 활성화
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. 정책: 누구나 username/nickname 조회 가능 (로그인 시 username→email 변환용)
CREATE POLICY "profiles_select" ON public.profiles
  FOR SELECT USING (true);

-- 4. 정책: 본인만 수정 가능
CREATE POLICY "profiles_update" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- 5. 정책: 회원가입 시 insert 허용
CREATE POLICY "profiles_insert" ON public.profiles
  FOR INSERT WITH CHECK (true);

-- 6. username 중복 체크용 함수 (anon 접근 허용)
CREATE OR REPLACE FUNCTION public.username_exists(uname TEXT)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (SELECT 1 FROM public.profiles WHERE username = uname);
$$ LANGUAGE sql SECURITY DEFINER;

-- 7. username으로 auth_email 조회 함수 (로그인용)
CREATE OR REPLACE FUNCTION public.get_auth_email(uname TEXT)
RETURNS TEXT AS $$
  SELECT
    CASE
      WHEN email IS NOT NULL THEN email
      ELSE username || '@users.greenbean.market'
    END
  FROM public.profiles WHERE username = uname;
$$ LANGUAGE sql SECURITY DEFINER;
