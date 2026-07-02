/* ── 홈 헤더 로그인/로그아웃 네비게이션 ──
   Supabase 세션 상태에 따라 로그인 버튼 또는 사용자 이름 + 로그아웃 버튼을 렌더링한다.
   기본값은 '로그인' 버튼이며, 세션이 확인되면 사용자 이름 + 로그아웃으로 전환한다.

   세션 감지는 getSession() 단독이 아니라 onAuthStateChange(INITIAL_SESSION 포함)의
   세션을 권위 소스로 사용한다. getSession()은 클라이언트 생성 직후 저장된 세션이
   복원되기 전 null을 반환할 수 있어, 로그인 상태를 놓치는 원인이 되기 때문이다. */
(function () {
  const area = document.getElementById('authArea');
  if (!area) return;

  let sb = null;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function displayName(session) {
    const u = session && session.user;
    if (!u) return '사용자';
    const m = u.user_metadata || {};
    return m.nickname || m.username || (u.email ? u.email.split('@')[0] : '사용자');
  }

  function renderLoggedOut() {
    area.innerHTML = `<a class="login-btn" href="auth.html?next=index.html">로그인</a>`;
  }

  function renderLoggedIn(name) {
    area.innerHTML =
      `<span class="user-name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>` +
      `<button class="logout-btn" id="logoutBtn">로그아웃</button>`;
    const btn = document.getElementById('logoutBtn');
    if (btn) btn.addEventListener('click', async () => {
      try { if (sb) await sb.auth.signOut(); } catch (e) {}
      location.href = 'index.html';
    });
  }

  function apply(session) {
    if (session && session.user) renderLoggedIn(displayName(session));
    else renderLoggedOut();
  }

  // 기본 상태: 로그인 버튼 (CDN/네트워크 실패 시에도 항상 노출)
  renderLoggedOut();

  if (typeof supabase === 'undefined' || typeof SUPABASE_URL === 'undefined') return;
  sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

  // 저장된 세션을 즉시 반영(가능한 경우)
  sb.auth.getSession().then(({ data }) => apply(data.session)).catch(() => {});
  // 세션 복원·로그인·로그아웃 이벤트를 권위 소스로 반영 (INITIAL_SESSION 포함)
  sb.auth.onAuthStateChange((_event, session) => apply(session));
})();
