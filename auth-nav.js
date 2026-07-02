/* ── 홈 헤더 로그인/로그아웃 네비게이션 ──
   Supabase 세션 상태에 따라 로그인 버튼 또는 사용자 이름 + 로그아웃 버튼을 렌더링한다.
   기본값은 '로그인' 버튼이며, 세션이 확인되면 사용자 이름 + 로그아웃으로 전환한다. */
(function () {
  const area = document.getElementById('authArea');
  if (!area) return;

  let sb = null;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function displayName(session) {
    const m = session.user.user_metadata || {};
    if (m.nickname) return m.nickname;
    if (m.username) return m.username;
    return session.user.email ? session.user.email.split('@')[0] : '사용자';
  }

  function renderLoggedOut() {
    area.innerHTML = `<a class="login-btn" href="auth.html?next=index.html">로그인</a>`;
  }

  function renderLoggedIn(name) {
    area.innerHTML =
      `<span class="user-name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>` +
      `<button class="logout-btn" id="logoutBtn">로그아웃</button>`;
    document.getElementById('logoutBtn').addEventListener('click', async () => {
      if (sb) await sb.auth.signOut();
      location.href = 'index.html';
    });
  }

  // 기본 상태: 로그인 버튼 (CDN/네트워크 실패 시에도 항상 노출)
  renderLoggedOut();

  if (typeof supabase === 'undefined' || typeof SUPABASE_URL === 'undefined') return;
  sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON);

  async function refresh() {
    try {
      const { data: { session } } = await sb.auth.getSession();
      if (session) renderLoggedIn(displayName(session));
      else renderLoggedOut();
    } catch (e) {
      renderLoggedOut();
    }
  }

  refresh();
  sb.auth.onAuthStateChange(() => refresh());
})();
