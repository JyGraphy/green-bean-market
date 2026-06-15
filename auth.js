/* ── Supabase 클라이언트 초기화 ── */
const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON);

/* ── 상태 ── */
let currentTab   = 'login';   // 'login' | 'signup'
let pendingEmail = '';
let timerInterval = null;

/* ── 이미 로그인된 경우 리다이렉트 ── */
(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (session) redirectAfterLogin();
})();

/* ── 탭 전환 ── */
function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabLogin').classList.toggle('active',  tab === 'login');
  document.getElementById('tabSignup').classList.toggle('active', tab === 'signup');
  backToEmail();
  hideMsg();
}

/* ── 메시지 ── */
function showMsg(text, type = 'error') {
  const el = document.getElementById('authMsg');
  el.textContent = text;
  el.className = `auth-msg ${type}`;
  el.style.display = '';
}
function hideMsg() {
  document.getElementById('authMsg').style.display = 'none';
}

/* ── Step 1: 인증코드 발송 ── */
async function sendCode() {
  const email = document.getElementById('emailInput').value.trim();
  if (!email || !email.includes('@')) {
    showMsg('올바른 이메일 주소를 입력해 주세요.');
    document.getElementById('emailInput').classList.add('invalid');
    return;
  }
  document.getElementById('emailInput').classList.remove('invalid');

  const btn = document.getElementById('btnSendCode');
  btn.disabled = true;
  btn.textContent = '발송 중…';
  hideMsg();

  const { error } = await sb.auth.signInWithOtp({
    email,
    options: { shouldCreateUser: true }
  });

  btn.disabled = false;
  btn.textContent = '인증코드 받기';

  if (error) {
    showMsg('인증코드 발송에 실패했습니다: ' + error.message);
    return;
  }

  pendingEmail = email;
  document.getElementById('stepEmail').style.display = 'none';
  document.getElementById('stepOtp').style.display   = '';
  document.getElementById('otpInfo').innerHTML =
    `<strong>${email}</strong>로 8자리 인증코드를 발송했습니다.<br>메일함을 확인해 주세요 (스팸 폴더도 확인)`;
  document.getElementById('otpInput').value = '';
  document.getElementById('otpInput').focus();
  startTimer(300); // 5분
}

/* ── Step 2: OTP 검증 ── */
async function verifyCode() {
  const token = document.getElementById('otpInput').value.trim();
  if (!token || token.length !== 8) {
    showMsg('8자리 인증코드를 입력해 주세요.');
    return;
  }

  const btn = document.getElementById('btnVerify');
  btn.disabled = true;
  btn.textContent = '확인 중…';
  hideMsg();

  const { data, error } = await sb.auth.verifyOtp({
    email: pendingEmail,
    token,
    type: 'email'
  });

  btn.disabled = false;
  btn.textContent = '인증 확인';

  if (error) {
    showMsg('인증코드가 올바르지 않거나 만료되었습니다. 다시 시도해 주세요.');
    return;
  }

  clearTimer();
  showMsg('인증 완료! 이동 중…', 'success');
  setTimeout(redirectAfterLogin, 800);
}

/* ── 이전 단계로 ── */
function backToEmail() {
  clearTimer();
  pendingEmail = '';
  document.getElementById('stepEmail').style.display = '';
  document.getElementById('stepOtp').style.display   = 'none';
  document.getElementById('emailInput').value = '';
  document.getElementById('otpInput').value   = '';
  hideMsg();
}

/* ── 타이머 ── */
function startTimer(seconds) {
  clearTimer();
  let remain = seconds;
  updateTimerDisplay(remain);
  timerInterval = setInterval(() => {
    remain--;
    updateTimerDisplay(remain);
    if (remain <= 0) {
      clearTimer();
      showMsg('인증코드가 만료되었습니다. 이메일을 다시 입력해 주세요.', 'info');
      backToEmail();
    }
  }, 1000);
}

function updateTimerDisplay(sec) {
  const m = String(Math.floor(sec / 60)).padStart(2, '0');
  const s = String(sec % 60).padStart(2, '0');
  document.getElementById('otpTimer').textContent = `${m}:${s}`;
}

function clearTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
  const el = document.getElementById('otpTimer');
  if (el) el.textContent = '';
}

/* ── 로그인 후 리다이렉트 ── */
function redirectAfterLogin() {
  const next = new URLSearchParams(location.search).get('next') || 'roastery.html';
  location.href = next;
}
