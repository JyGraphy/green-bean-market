/* ── Supabase DB 레이어 ── */
const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON);

let currentUserId = null;

async function initDB() {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) { location.href = 'auth.html?next=roastery.html'; return; }
  currentUserId = session.user.id;

  const logoutBtn = document.getElementById('btnLogout');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await sb.auth.signOut();
      location.href = 'auth.html';
    });
  }
}

async function dbInsert(bean) {
  const { error } = await sb.from('beans').insert({
    name: bean.name, roastery: bean.roastery, country: bean.country || null,
    farm: bean.farm || null, altitude: bean.altitude || null,
    process: bean.process || null, roast: bean.roast || null,
    variety: bean.variety || null, notes: bean.notes || null,
    memo: bean.memo || null, created_by: currentUserId
  });
  if (error) throw error;
}

async function dbUpdate(bean) {
  const { error } = await sb.from('beans').update({
    name: bean.name, roastery: bean.roastery, country: bean.country || null,
    farm: bean.farm || null, altitude: bean.altitude || null,
    process: bean.process || null, roast: bean.roast || null,
    variety: bean.variety || null, notes: bean.notes || null,
    memo: bean.memo || null
  }).eq('id', bean.id);
  if (error) throw error;
}

async function dbDelete(id) {
  const { error } = await sb.from('beans').delete().eq('id', id);
  if (error) throw error;
}

async function dbGetAll() {
  const { data, error } = await sb.from('beans').select('*').order('id', { ascending: false });
  if (error) throw error;
  return data;
}

/* ── UI 상태 ── */
let allBeans = [];
let pendingDeleteId = null;

const grid          = document.getElementById('beanGrid');
const emptyState    = document.getElementById('emptyState');
const beanCount     = document.getElementById('beanCount');
const searchInput   = document.getElementById('searchInput');
const filterProcess = document.getElementById('filterProcess');
const filterRoast   = document.getElementById('filterRoast');

const modalOverlay   = document.getElementById('modalOverlay');
const modal          = document.getElementById('modal');
const modalTitle     = document.getElementById('modalTitle');
const beanForm       = document.getElementById('beanForm');
const confirmOverlay = document.getElementById('confirmOverlay');

/* ── 나라 국기 매핑 ── */
const COUNTRY_FLAG = {
  '에티오피아':'🇪🇹','케냐':'🇰🇪','탄자니아':'🇹🇿','르완다':'🇷🇼','우간다':'🇺🇬','부룬디':'🇧🇮',
  '브라질':'🇧🇷','콜롬비아':'🇨🇴','과테말라':'🇬🇹','코스타리카':'🇨🇷','파나마':'🇵🇦',
  '엘살바도르':'🇸🇻','온두라스':'🇭🇳','멕시코':'🇲🇽','자메이카':'🇯🇲','페루':'🇵🇪',
  '볼리비아':'🇧🇴','에콰도르':'🇪🇨','니카라과':'🇳🇮','인도네시아':'🇮🇩','인도':'🇮🇳',
  '베트남':'🇻🇳','예멘':'🇾🇪','중국':'🇨🇳','파푸아뉴기니':'🇵🇬','하와이':'🌺',
  '세인트헬레나':'🌍','콩고민주공화국':'🇨🇩',
};

const openSections = new Set();

/* ── 렌더링 ── */
function renderCards(beans) {
  grid.querySelectorAll('.rb-country-section').forEach(s => s.remove());

  emptyState.style.display = beans.length ? 'none' : '';
  beanCount.textContent = `${beans.length}개`;
  if (!beans.length) return;

  /* 나라별 그룹핑, 원두 수 내림차순 */
  const groups = {};
  beans.forEach(b => {
    const key = b.country || '기타';
    if (!groups[key]) groups[key] = [];
    groups[key].push(b);
  });
  const countries = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);

  /* 처음 로드 시 첫 번째 나라만 열기 */
  if (openSections.size === 0) openSections.add(countries[0]);

  countries.forEach(country => {
    const list = groups[country];
    const flag = COUNTRY_FLAG[country] || '🌍';
    const isOpen = openSections.has(country);

    const section = document.createElement('div');
    section.className = 'rb-country-section';

    section.innerHTML = `
      <button class="rb-country-header${isOpen ? ' open' : ''}" type="button">
        <span class="rb-country-flag">${flag}</span>
        <span class="rb-country-name">${esc(country)}</span>
        <span class="rb-country-count">${list.length}개</span>
        <span class="rb-country-arrow">▾</span>
      </button>
      <div class="rb-country-body${isOpen ? ' open' : ''}">
        <div class="rb-card-grid"></div>
      </div>
    `;

    const cardGrid = section.querySelector('.rb-card-grid');
    list.forEach(b => {
      const card = document.createElement('div');
      card.className = 'rb-card';
      card.innerHTML = `
        <div class="rb-card-header">
          <div class="rb-card-name">${esc(b.name)}</div>
          <div class="rb-card-actions">
            <button class="rb-icon-btn" data-edit="${b.id}" title="수정">✏️</button>
            <button class="rb-icon-btn del" data-del="${b.id}" title="삭제">🗑️</button>
          </div>
        </div>
        ${b.roastery ? `<div class="rb-card-roastery">${esc(b.roastery)}</div>` : ''}
        <div class="rb-card-meta">
          ${b.process  ? `<span class="rb-badge process">${esc(b.process)}</span>` : ''}
          ${b.roast    ? `<span class="rb-badge roast">${esc(b.roast)}</span>` : ''}
          ${b.altitude ? `<span class="rb-badge altitude">▲ ${b.altitude}m</span>` : ''}
        </div>
        ${b.farm ? `<div class="rb-tag" style="width:fit-content">📍 ${esc(b.farm)}</div>` : ''}
        ${b.variety || b.notes ? `<hr class="rb-card-divider">` : ''}
        ${b.variety ? renderTags(b.variety, 'variety', '🌱') : ''}
        ${b.notes   ? renderTags(b.notes,   'note',    '☕') : ''}
        ${b.memo    ? `<hr class="rb-card-divider"><div class="rb-card-memo">${esc(b.memo)}</div>` : ''}
      `;
      cardGrid.appendChild(card);
    });

    section.querySelector('.rb-country-header').addEventListener('click', () => {
      const header = section.querySelector('.rb-country-header');
      const body   = section.querySelector('.rb-country-body');
      const nowOpen = body.classList.toggle('open');
      header.classList.toggle('open', nowOpen);
      if (nowOpen) openSections.add(country);
      else openSections.delete(country);
    });

    section.querySelectorAll('[data-edit]').forEach(btn =>
      btn.addEventListener('click', () => openEdit(+btn.dataset.edit))
    );
    section.querySelectorAll('[data-del]').forEach(btn =>
      btn.addEventListener('click', () => openConfirm(+btn.dataset.del))
    );

    grid.appendChild(section);
  });
}

function renderTags(csv, cls, icon) {
  if (!csv) return '';
  const tags = csv.split(',').map(t => t.trim()).filter(Boolean);
  if (!tags.length) return '';
  return `<div class="rb-card-variety">${icon ? `<span style="font-size:12px">${icon}</span>` : ''}${
    tags.map(t => `<span class="rb-tag ${cls}">${esc(t)}</span>`).join('')
  }</div>`;
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── 필터링 ── */
function applyFilter() {
  const q   = searchInput.value.trim().toLowerCase();
  const prc = filterProcess.value;
  const rst = filterRoast.value;
  const filtered = allBeans.filter(b => {
    const text = [b.name, b.roastery, b.country, b.farm].join(' ').toLowerCase();
    return (!q || text.includes(q))
        && (!prc || b.process === prc)
        && (!rst || b.roast  === rst);
  });
  renderCards(filtered);
  updateRoasteryDatalist();
}

async function refresh() {
  try {
    allBeans = await dbGetAll();
    applyFilter();
  } catch (err) {
    console.error('beans 로드 실패:', err);
    emptyState.innerHTML = `<div class="rb-empty-icon">⚠️</div><p>원두 목록을 불러오지 못했습니다</p><p class="rb-empty-sub">${err.message}</p>`;
    emptyState.style.display = '';
    beanCount.textContent = '오류';
  }
}

function updateRoasteryDatalist() {
  const dl = document.getElementById('roasteryList');
  const names = [...new Set(allBeans.map(b => b.roastery).filter(Boolean))];
  dl.innerHTML = names.map(n => `<option>${esc(n)}</option>`).join('');
}

/* ── 폼 모달 ── */
function openAdd() {
  modalTitle.textContent = '원두 추가';
  beanForm.reset();
  document.getElementById('fieldId').value = '';
  clearInvalid();
  modalOverlay.classList.add('open');
  document.getElementById('fieldName').focus();
}

function openEdit(id) {
  const b = allBeans.find(x => x.id === id);
  if (!b) return;
  modalTitle.textContent = '원두 수정';
  document.getElementById('fieldId').value       = b.id;
  document.getElementById('fieldName').value     = b.name     ?? '';
  document.getElementById('fieldRoastery').value = b.roastery ?? '';
  document.getElementById('fieldCountry').value  = b.country  ?? '';
  document.getElementById('fieldFarm').value     = b.farm     ?? '';
  document.getElementById('fieldAltitude').value = b.altitude ?? '';
  document.getElementById('fieldProcess').value  = b.process  ?? '';
  document.getElementById('fieldRoast').value    = b.roast    ?? '';
  document.getElementById('fieldVariety').value  = b.variety  ?? '';
  document.getElementById('fieldNotes').value    = b.notes    ?? '';
  document.getElementById('fieldMemo').value     = b.memo     ?? '';
  clearInvalid();
  modalOverlay.classList.add('open');
}

function closeModal() { modalOverlay.classList.remove('open'); }

function clearInvalid() {
  beanForm.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
}

function getFormBean() {
  return {
    id:       +document.getElementById('fieldId').value || null,
    name:     document.getElementById('fieldName').value.trim(),
    roastery: document.getElementById('fieldRoastery').value.trim(),
    country:  document.getElementById('fieldCountry').value.trim(),
    farm:     document.getElementById('fieldFarm').value.trim(),
    altitude: +document.getElementById('fieldAltitude').value || null,
    process:  document.getElementById('fieldProcess').value,
    roast:    document.getElementById('fieldRoast').value,
    variety:  document.getElementById('fieldVariety').value.trim(),
    notes:    document.getElementById('fieldNotes').value.trim(),
    memo:     document.getElementById('fieldMemo').value.trim(),
  };
}

beanForm.addEventListener('submit', async e => {
  e.preventDefault();
  clearInvalid();
  const bean = getFormBean();
  let valid = true;
  if (!bean.name) {
    document.getElementById('fieldName').classList.add('invalid'); valid = false;
  }
  if (!bean.roastery) {
    document.getElementById('fieldRoastery').classList.add('invalid'); valid = false;
  }
  if (!valid) return;

  const saveBtn = beanForm.querySelector('.rb-btn-save');
  saveBtn.disabled = true;
  try {
    if (bean.id) {
      await dbUpdate(bean);
    } else {
      await dbInsert(bean);
    }
    closeModal();
    await refresh();
  } catch (err) {
    alert('저장 중 오류가 발생했습니다: ' + err.message);
  } finally {
    saveBtn.disabled = false;
  }
});

/* ── 삭제 확인 ── */
function openConfirm(id) {
  pendingDeleteId = id;
  confirmOverlay.classList.add('open');
}

document.getElementById('btnConfirmYes').addEventListener('click', async () => {
  if (pendingDeleteId) {
    try {
      await dbDelete(pendingDeleteId);
      pendingDeleteId = null;
      confirmOverlay.classList.remove('open');
      await refresh();
    } catch (err) {
      alert('삭제 중 오류가 발생했습니다: ' + err.message);
    }
  }
});
document.getElementById('btnConfirmNo').addEventListener('click', () => {
  pendingDeleteId = null;
  confirmOverlay.classList.remove('open');
});

/* ── 이벤트 바인딩 ── */
document.getElementById('btnOpenForm').addEventListener('click', openAdd);
document.getElementById('btnCloseModal').addEventListener('click', closeModal);
document.getElementById('btnCancel').addEventListener('click', closeModal);

modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
confirmOverlay.addEventListener('click', e => {
  if (e.target === confirmOverlay) { pendingDeleteId = null; confirmOverlay.classList.remove('open'); }
});

searchInput.addEventListener('input', applyFilter);
filterProcess.addEventListener('change', applyFilter);
filterRoast.addEventListener('change', applyFilter);

/* ── 초기화 ── */
initDB().then(refresh);
