/* ===== AGENT HQ 명부 =====
 * 이 파일이 현황판의 데이터 원본이다.
 * 에이전트가 일을 마치면 해당 항목의 status/lastWork와 LOGS에 기록을 추가한다.
 * status: 'active'(업무 중) | 'standby'(대기) | 'idle'(휴식) | 'offline'(오프라인)
 */
const HQ = {
  departments: [
    {
      id: 'qa', name: '검수부서', unit: 'UNIT QA', icon: '🛡️', accent: 'var(--qa)',
      desc: '코드·데이터가 안전장치 규칙을 지키는지 검사 (읽기 전용)',
      agents: [
        { id: 'scraper-checker',  emoji: '🕷️', role: '스크래퍼 안전 점검', status: 'standby', lastWork: null },
        { id: 'data-validator',   emoji: '🧪', role: '상품 데이터 검증',   status: 'standby', lastWork: null },
        { id: 'frontend-reviewer',emoji: '🎨', role: '화면 변경 리뷰',     status: 'standby', lastWork: null },
      ],
    },
    {
      id: 'ops', name: '실무부서', unit: 'UNIT OPS', icon: '🧭', accent: 'var(--ops)',
      desc: '신규 생두사 발굴·보고 → 사용자 승인 → 온보딩',
      agents: [
        { id: 'store-scout',        emoji: '🔎', role: '신규 생두사 발굴', status: 'standby', lastWork: null },
        { id: 'new-store-onboarder',emoji: '🏗️', role: '공급사 온보딩',   status: 'standby', lastWork: null },
      ],
    },
    {
      id: 'res', name: '리서치부서', unit: 'UNIT RES', icon: '📡', accent: 'var(--res)',
      desc: 'COE 옥션 · 로스팅 프로파일 데이터 · 논문 번역',
      agents: [
        { id: 'coe-auction-reporter',     emoji: '🏆', role: 'COE 옥션 리포트',     status: 'standby', lastWork: 'COE 2026 일정 리포트 제출' },
        { id: 'roast-profile-collector',  emoji: '🔥', role: '프로파일 데이터 수집', status: 'standby', lastWork: null },
        { id: 'coffee-research-translator',emoji: '📚', role: '논문 번역·정리',      status: 'standby', lastWork: null },
      ],
    },
  ],
  toolCount: 8, // 팀 전체가 쓰는 도구 종류: Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch
};

/* 업무 로그 — 최신이 위. 에이전트가 산출물을 만들면 여기에 추가 (report: 링크는 선택) */
const LOGS = [
  { date: '2026-08-02', dept: 'qa',  agent: 'data-validator', text: '데이터 전수 검증 — 위험 1건(모모스커피 링크 115개 전량 dead) · 주의 9건 · 중복ID/상대경로URL 0건', report: '../docs/daily/2026-08-02-데이터검증.md' },
  { date: '2026-08-02', dept: 'qa',  agent: 'scraper-checker', text: '스크래퍼 15종 전수 점검 — 규칙 위반 0건 · 주의 6건 · CLAUDE.md 문서 드리프트 발견(12→16개사, 500→1286개)', report: '../docs/daily/2026-08-02-스크래퍼점검.md' },
  { date: '2026-08-02', dept: 'ops', agent: 'store-scout', text: '신규 생두사 후보 15곳 발굴 — 1군 4곳(커피시스·캅카와·맥널티·나무사이로) ⏳ 승인 대기', report: '../docs/store-scout-report-2026-08-02.md' },
  { date: '2026-08-02', dept: 'res', agent: 'roast-profile-collector', text: '프로파일 출처 카탈로그 22곳 구축 — 곡선 수집 0건(본문 접근 차단, 날조 대신 보류)', report: '../research/roast-profiles/SOURCES.md' },
  { date: '2026-08-02', dept: 'res', agent: 'coffee-research-translator', text: '커피 논문 2편 한글 정리 (로스팅 색도 곡선 · 적정산도)', report: '../docs/research/' },
  { date: '2026-08-02', dept: 'res', agent: 'coe-auction-reporter', text: 'COE 2026 옥션 일정 리포트 제출 — 태국 옥션 D-2(8/4) 임박 알림 · 랏 상세는 접근 차단으로 미확인', report: '../docs/coe-report-2026-08-02.md' },
  { date: '2026-08-02', dept: 'qa',  agent: 'system', text: '환경 네트워크 실측: WebFetch·curl 전면 403 차단, WebSearch 정상 → 리서치팀 전원에 대체 프로토콜 배포' },
  { date: '2026-08-01', dept: 'qa',  agent: 'system', text: 'AI 직원 8명 채용 완료 — 검수·실무·리서치 3개 부서 편성' },
];

/* ===== 이하 렌더링 (데이터 수정 불필요) ===== */
const STATUS_KO = { active: '업무 중', standby: '대기', idle: '휴식', offline: '오프라인' };
const $ = (id) => document.getElementById(id);

function chip(status) {
  return `<span class="chip ${status}"><span class="chip-dot"></span>${STATUS_KO[status]}</span>`;
}

function render() {
  const all = HQ.departments.flatMap((d) => d.agents);
  const count = (s) => all.filter((a) => a.status === s).length;
  const reports = LOGS.filter((l) => l.agent !== 'system').length;

  $('hqAgentTotal').textContent = all.length;
  $('hqDeptTotal').textContent = HQ.departments.length;
  $('cmdNote').textContent = `${HQ.departments.length}개 부서 가동 · ${all.length}명 재직`;

  $('hqPills').innerHTML = [
    ['active', count('active'), 'ACTIVE'],
    ['standby', count('standby'), 'STANDBY'],
    ['idle', count('idle'), 'IDLE'],
    ['offline', count('offline'), 'OFFLINE'],
    ['reports', reports, 'REPORTS'],
    ['tools', HQ.toolCount, 'TOOLS'],
  ].map(([cls, num, label]) => `
    <div class="pill ${cls}">
      <div class="pill-top"><span class="pill-dot"></span><span class="pill-num">${num}</span></div>
      <div class="pill-label">${label}</div>
    </div>`).join('');

  $('deptGrid').innerHTML = HQ.departments.map((d) => {
    const working = d.agents.filter((a) => a.status === 'active').length;
    const ready = d.agents.filter((a) => a.status === 'active' || a.status === 'standby').length;
    const done = LOGS.filter((l) => l.dept === d.id && l.agent !== 'system').length;
    const pct = Math.round((ready / d.agents.length) * 100);
    return `
    <article class="dept-card" style="--accent:${d.accent}">
      <div class="dept-head">
        <div class="dept-icon">${d.icon}</div>
        <div>
          <div class="dept-name">${d.name}</div>
          <div class="dept-unit">${d.unit}</div>
        </div>
        <div class="dept-count">
          <div class="dept-count-num">${d.agents.length}</div>
          <div class="dept-count-label">배치 인원</div>
        </div>
      </div>
      <div class="dept-mini">
        <div class="mini"><div class="mini-num">${working}</div><div class="mini-label">업무 중</div></div>
        <div class="mini"><div class="mini-num">${done}</div><div class="mini-label">산출물</div></div>
        <div class="mini"><div class="mini-num">${d.agents.length - working}</div><div class="mini-label">대기</div></div>
      </div>
      <div class="dept-load">
        <div class="load-row"><span>가동 가능률</span><span class="load-pct">${pct}%</span></div>
        <div class="load-bar"><div class="load-fill" style="width:${pct}%"></div></div>
      </div>
      <div class="desks">
        <div class="desks-label"><span>LIVE DESKS</span><span>${d.agents.length}석</span></div>
        ${d.agents.map((a) => `
        <div class="desk-row">
          <div class="desk-avatar">${a.emoji}</div>
          <div class="desk-info">
            <div class="desk-name">${a.id}</div>
            <div class="desk-role">${a.role}</div>
          </div>
          <span class="desk-tag">GLOBAL</span>
          ${chip(a.status)}
        </div>`).join('')}
      </div>
    </article>`;
  }).join('');

  $('floorGrid').innerHTML = HQ.departments.flatMap((d) =>
    d.agents.map((a) => `
    <div class="desk-card ${a.status}" style="--accent:${d.accent}">
      <div class="desk-monitor"></div>
      <div class="desk-emoji">${a.emoji}</div>
      <div class="name">${a.id}</div>
      <div class="role">${a.lastWork || a.role}</div>
      ${chip(a.status)}
    </div>`)).join('');

  const accentOf = (id) => (HQ.departments.find((d) => d.id === id) || {}).accent || 'var(--dim)';
  $('logList').innerHTML = LOGS.map((l) => `
    <li class="log-item" style="--accent:${accentOf(l.dept)}">
      <span class="log-time">${l.date}</span>
      <span class="log-agent">${l.agent}</span>
      <span class="log-text">${l.report ? `<a href="${l.report}">${l.text}</a>` : l.text}</span>
    </li>`).join('');
}

/* 시계 + 세션 가동 시간 */
const bootAt = Date.now();
function tick() {
  const now = new Date();
  $('hqTime').textContent = now.toLocaleTimeString('ko-KR', { hour12: false });
  $('hqDate').textContent = now.toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'short' });
  const s = Math.floor((Date.now() - bootAt) / 1000);
  const pad = (n) => String(n).padStart(2, '0');
  $('hqUptime').textContent = `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}`;
}

render();
tick();
setInterval(tick, 1000);
