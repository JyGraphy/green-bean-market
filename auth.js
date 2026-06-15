/* ── Supabase 클라이언트 ── */
const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON);

/* ── 이미 로그인된 경우 ── */
(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (session) redirectAfterLogin();
})();

/* ── 탭 전환 ── */
let currentTab = 'login';
function switchTab(tab) {
  currentTab = tab;
  document.getElementById('tabLogin').classList.toggle('active',  tab === 'login');
  document.getElementById('tabSignup').classList.toggle('active', tab === 'signup');
  document.getElementById('loginForm').style.display  = tab === 'login'  ? '' : 'none';
  document.getElementById('signupForm').style.display = tab === 'signup' ? '' : 'none';
  hideMsg();
  clearInvalid();
}

/* ── 메시지 ── */
function showMsg(text, type = 'error') {
  const el = document.getElementById('authMsg');
  el.innerHTML = text;
  el.className = `auth-msg ${type}`;
  el.style.display = '';
}
function hideMsg() { document.getElementById('authMsg').style.display = 'none'; }

/* ── 유효성 초기화 ── */
function clearInvalid() {
  document.querySelectorAll('.invalid').forEach(e => e.classList.remove('invalid'));
}
function markInvalid(id) {
  document.getElementById(id)?.classList.add('invalid');
}

/* ── 비밀번호 토글 ── */
function togglePw(inputId, btn) {
  const el = document.getElementById(inputId);
  if (el.type === 'password') { el.type = 'text';     btn.textContent = '🙈'; }
  else                        { el.type = 'password'; btn.textContent = '👁'; }
}

/* ── 아이디 중복 실시간 체크 ── */
let usernameTimer = null;
async function checkUsername(input) {
  const val = input.value.trim();
  const status = document.getElementById('usernameStatus');
  clearTimeout(usernameTimer);

  if (!val) { status.textContent = ''; status.className = 'auth-input-status'; return; }
  if (!/^[a-zA-Z0-9_]{4,20}$/.test(val)) {
    status.textContent = '영문·숫자·_ (4~20자)';
    status.className = 'auth-input-status bad';
    return;
  }

  status.textContent = '확인 중…';
  status.className = 'auth-input-status';

  usernameTimer = setTimeout(async () => {
    const { data } = await sb.rpc('username_exists', { uname: val });
    if (data) {
      status.textContent = '이미 사용 중인 아이디입니다';
      status.className = 'auth-input-status bad';
    } else {
      status.textContent = '사용 가능한 아이디입니다';
      status.className = 'auth-input-status good';
    }
  }, 400);
}

/* ── 회원가입 ── */
async function signup() {
  clearInvalid();
  hideMsg();

  const username = document.getElementById('signupUsername').value.trim();
  const nickname = document.getElementById('signupNickname').value.trim();
  const password = document.getElementById('signupPassword').value;
  const confirm  = document.getElementById('signupPasswordConfirm').value;
  const email    = document.getElementById('signupEmail').value.trim();

  /* 유효성 검사 */
  let valid = true;
  if (!/^[a-zA-Z0-9_]{4,20}$/.test(username)) {
    markInvalid('signupUsername');
    showMsg('아이디는 영문·숫자·_ 조합 4~20자로 입력해 주세요.');
    valid = false;
  }
  if (!nickname) {
    markInvalid('signupNickname');
    if (valid) showMsg('닉네임을 입력해 주세요.');
    valid = false;
  }
  if (password.length < 8) {
    markInvalid('signupPassword');
    if (valid) showMsg('비밀번호는 8자 이상이어야 합니다.');
    valid = false;
  }
  if (password !== confirm) {
    markInvalid('signupPasswordConfirm');
    if (valid) showMsg('비밀번호가 일치하지 않습니다.');
    valid = false;
  }
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    markInvalid('signupEmail');
    if (valid) showMsg('이메일 형식이 올바르지 않습니다.');
    valid = false;
  }
  if (!valid) return;

  const btn = setBtnLoading('signupForm', '가입 중…');

  /* 아이디 중복 최종 확인 */
  const { data: exists } = await sb.rpc('username_exists', { uname: username });
  if (exists) {
    showMsg('이미 사용 중인 아이디입니다.');
    markInvalid('signupUsername');
    btn.restore();
    return;
  }

  /* auth 이메일: 실제 이메일 or 내부 식별자 */
  const authEmail = email || `${username}@users.greenbean.market`;

  /* Supabase Auth 가입 */
  const { data: authData, error: authError } = await sb.auth.signUp({
    email: authEmail,
    password,
    options: { data: { username, nickname } }
  });

  if (authError) {
    const msg = authError.message;
    if (msg.includes('already registered') || msg.includes('already been registered')) {
      if (email) {
        showMsg('이미 사용 중인 이메일입니다.<br>이메일 칸을 비워두고 다시 시도해 주세요.');
        markInvalid('signupEmail');
      } else {
        showMsg('이미 가입된 계정입니다. 로그인해 주세요.');
      }
    } else if (msg.includes('Password should be')) {
      showMsg('비밀번호는 8자 이상이어야 합니다.');
      markInvalid('signupPassword');
    } else {
      showMsg('회원가입 중 오류가 발생했습니다: ' + msg);
    }
    btn.restore();
    return;
  }

  /* profiles 테이블에 저장 */
  const userId = authData.user?.id;
  if (userId) {
    await sb.from('profiles').insert({
      id: userId,
      username,
      nickname,
      email: email || null
    });
  }

  btn.restore();
  showMsg('🎉 회원가입이 완료되었습니다! 로그인해 주세요.', 'success');
  setTimeout(() => switchTab('login'), 1500);
}

/* ── 로그인 ── */
async function login() {
  clearInvalid();
  hideMsg();

  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;

  if (!username) { markInvalid('loginUsername'); showMsg('아이디를 입력해 주세요.'); return; }
  if (!password)  { markInvalid('loginPassword');  showMsg('비밀번호를 입력해 주세요.'); return; }

  const btn = setBtnLoading('loginForm', '로그인 중…');

  /* username → auth 이메일 변환 */
  const { data: authEmail, error: fnError } = await sb.rpc('get_auth_email', { uname: username });

  if (fnError || !authEmail) {
    showMsg('존재하지 않는 아이디입니다.');
    markInvalid('loginUsername');
    btn.restore();
    return;
  }

  /* 비밀번호 로그인 */
  const { error } = await sb.auth.signInWithPassword({ email: authEmail, password });

  if (error) {
    showMsg('비밀번호가 올바르지 않습니다.');
    markInvalid('loginPassword');
    btn.restore();
    return;
  }

  btn.restore();
  redirectAfterLogin();
}

/* ── 버튼 로딩 헬퍼 ── */
function setBtnLoading(formId, text) {
  const btn = document.querySelector(`#${formId} .auth-btn-primary`);
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = text;
  return { restore: () => { btn.disabled = false; btn.textContent = orig; } };
}

/* ── 로그인 후 리다이렉트 ── */
function redirectAfterLogin() {
  const next = new URLSearchParams(location.search).get('next') || 'roastery.html';
  location.href = next;
}
