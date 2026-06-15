/* ── DB 레이어 — 추후 서버 API로 교체 시 이 섹션만 교체하면 됨 ── */
const STORAGE_KEY = 'roastery_beans_db';
let SQL, db;

async function initDB() {
  SQL = await initSqlJs({
    locateFile: f => `https://cdn.jsdelivr.net/npm/sql.js@1.12.0/dist/${f}`
  });
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    const buf = Uint8Array.from(atob(saved), c => c.charCodeAt(0));
    db = new SQL.Database(buf);
  } else {
    db = new SQL.Database();
  }
  db.run(`CREATE TABLE IF NOT EXISTS beans (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    roastery  TEXT NOT NULL,
    country   TEXT,
    farm      TEXT,
    altitude  INTEGER,
    process   TEXT,
    roast     TEXT,
    variety   TEXT,
    notes     TEXT,
    memo      TEXT,
    created   TEXT DEFAULT (datetime('now','localtime'))
  )`);
  saveDB();
}

function saveDB() {
  const data = db.export();
  localStorage.setItem(STORAGE_KEY, btoa(String.fromCharCode(...data)));
}

function dbInsert(bean) {
  db.run(
    `INSERT INTO beans (name,roastery,country,farm,altitude,process,roast,variety,notes,memo)
     VALUES (?,?,?,?,?,?,?,?,?,?)`,
    [bean.name, bean.roastery, bean.country, bean.farm,
     bean.altitude || null, bean.process, bean.roast,
     bean.variety, bean.notes, bean.memo]
  );
  saveDB();
}

function dbUpdate(bean) {
  db.run(
    `UPDATE beans SET name=?,roastery=?,country=?,farm=?,altitude=?,
     process=?,roast=?,variety=?,notes=?,memo=? WHERE id=?`,
    [bean.name, bean.roastery, bean.country, bean.farm,
     bean.altitude || null, bean.process, bean.roast,
     bean.variety, bean.notes, bean.memo, bean.id]
  );
  saveDB();
}

function dbDelete(id) {
  db.run('DELETE FROM beans WHERE id=?', [id]);
  saveDB();
}

function dbGetAll() {
  const stmt = db.prepare('SELECT * FROM beans ORDER BY id DESC');
  const rows = [];
  while (stmt.step()) rows.push(stmt.getAsObject());
  stmt.free();
  return rows;
}

/* ── UI 상태 ── */
let allBeans = [];
let pendingDeleteId = null;

const grid        = document.getElementById('beanGrid');
const emptyState  = document.getElementById('emptyState');
const beanCount   = document.getElementById('beanCount');
const searchInput = document.getElementById('searchInput');
const filterProcess = document.getElementById('filterProcess');
const filterRoast   = document.getElementById('filterRoast');

const modalOverlay  = document.getElementById('modalOverlay');
const modal         = document.getElementById('modal');
const modalTitle    = document.getElementById('modalTitle');
const beanForm      = document.getElementById('beanForm');
const confirmOverlay = document.getElementById('confirmOverlay');

/* ── 렌더링 ── */
function renderCards(beans) {
  const cards = grid.querySelectorAll('.rb-card');
  cards.forEach(c => c.remove());

  emptyState.style.display = beans.length ? 'none' : '';
  beanCount.textContent = `${beans.length}개`;

  beans.forEach(b => {
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
        ${b.country  ? `<span class="rb-badge country">🌍 ${esc(b.country)}</span>` : ''}
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
    grid.appendChild(card);
  });

  /* 이벤트 위임 */
  grid.querySelectorAll('[data-edit]').forEach(btn =>
    btn.addEventListener('click', () => openEdit(+btn.dataset.edit))
  );
  grid.querySelectorAll('[data-del]').forEach(btn =>
    btn.addEventListener('click', () => openConfirm(+btn.dataset.del))
  );
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

function refresh() {
  allBeans = dbGetAll();
  applyFilter();
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

beanForm.addEventListener('submit', e => {
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

  if (bean.id) {
    dbUpdate(bean);
  } else {
    dbInsert(bean);
  }
  closeModal();
  refresh();
});

/* ── 삭제 확인 ── */
function openConfirm(id) {
  pendingDeleteId = id;
  confirmOverlay.classList.add('open');
}

document.getElementById('btnConfirmYes').addEventListener('click', () => {
  if (pendingDeleteId) {
    dbDelete(pendingDeleteId);
    pendingDeleteId = null;
    confirmOverlay.classList.remove('open');
    refresh();
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
