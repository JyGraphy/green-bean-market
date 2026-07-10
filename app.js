// ── State ─────────────────────────────────────────────────
let PRODUCTS = null;
let dbReady = false;
let curStore = 'all', curOrigin = 'all', curRegion = 'all', curView = 'table', curPage = 1;
let curQuick = 'all';
const PAGE_SZ = 50;

// ── Data init ─────────────────────────────────────────────
async function initDB() {
  showLoading(true);
  try {
    // 캐시 버스팅: 날짜 기준 쿼리로 옛 데이터(상대경로 등) 캐시 방지. 데이터는 매일 06시 갱신.
    const v = new Date().toISOString().slice(0, 10);
    const res = await fetch(`data/products_web.json?v=${v}`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    PRODUCTS = await res.json();
    dbReady = true;
    showLoading(false);
    init();
    loadUpdateLog();
  } catch (e) {
    showLoadError();
  }
}

function showLoading(on) {
  document.getElementById('loadingOverlay').style.display = on ? 'flex' : 'none';
}

function showLoadError() {
  const overlay = document.getElementById('loadingOverlay');
  overlay.style.display = 'flex';
  overlay.querySelector('.loading-box').innerHTML = `
    <div class="loading-text">데이터를 불러오지 못했습니다.<br>네트워크 상태를 확인한 뒤 다시 시도해주세요.</div>
    <button class="reset-btn" style="margin-top:14px" onclick="location.reload()">다시 시도</button>`;
}

function queryAll() {
  return PRODUCTS || [];
}

// ── Init ──────────────────────────────────────────────────
function init() {
  const products = queryAll();
  const origins = [...new Set(products.map(p => p.origin))].sort((a,b) => a.localeCompare(b,'ko'));

  document.getElementById('totalCount').textContent = products.length;
  document.getElementById('originCount').textContent = origins.length;

  // 신규 입고 배지 카운트
  const cutoff = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const newCount = products.filter(p => p.added_date && p.added_date >= cutoff).length;
  const el = document.getElementById('newCount');
  if (el) el.textContent = newCount;

  buildStatBars(products);
  applyFilters();
}

// ── Update log banner ─────────────────────────────────────
async function loadUpdateLog() {
  try {
    const v = new Date().toISOString().slice(0, 10);
    const res = await fetch(`data/update_log.json?v=${v}`, { cache: 'no-cache' });
    if (!res.ok) return;
    const log = await res.json();
    if (!log.total_new || log.total_new === 0) return;
    if (!log.updated_at) return;

    // 3일 이내 업데이트만 표시
    const daysDiff = (Date.now() - new Date(log.updated_at)) / (1000 * 60 * 60 * 24);
    if (daysDiff > 3) return;

    // 이미 닫은 경우 표시 안 함
    if (sessionStorage.getItem('update_seen_' + log.updated_at)) return;

    const storeNames = log.stores.map(s => `${s.name}(${s.new_count})`).join(', ');
    document.getElementById('updateBannerText').textContent =
      `신규 입고 ${log.total_new}개 · ${storeNames}`;

    const banner = document.getElementById('updateBanner');
    banner.style.display = 'flex';

    document.getElementById('updateBannerNew').onclick = () => {
      banner.style.display = 'none';
      sessionStorage.setItem('update_seen_' + log.updated_at, '1');
      setQuick('new');
    };
    document.getElementById('updateBannerClose').onclick = () => {
      banner.style.display = 'none';
      sessionStorage.setItem('update_seen_' + log.updated_at, '1');
    };
  } catch(e) {}
}

// ── Statistics sidebar ────────────────────────────────────
function buildStatBars(products) {
  const oc = {};
  products.forEach(p => { oc[p.origin] = (oc[p.origin]||0)+1; });
  const topO = Object.entries(oc).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxO = topO[0]?.[1]||1;
  document.getElementById('originStats').innerHTML = topO.map(([o,c])=>`
    <div class="stat-bar-item">
      <div class="stat-bar-lbl"><span>${o}</span><span>${c}</span></div>
      <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${c/maxO*100}%"></div></div>
    </div>`).join('');

  const pc = {};
  products.forEach(p => { pc[p.process] = (pc[p.process]||0)+1; });
  const topP = Object.entries(pc).sort((a,b)=>b[1]-a[1]);
  const maxP = topP[0]?.[1]||1;
  document.getElementById('processStats').innerHTML = topP.map(([proc,c])=>`
    <div class="stat-bar-item">
      <div class="stat-bar-lbl"><span>${proc}</span><span>${c}</span></div>
      <div class="stat-bar-track"><div class="stat-bar-fill" style="width:${c/maxP*100}%;background:${PROC_COLORS[proc]||'#5c3317'}"></div></div>
    </div>`).join('');
}

// ── Filter controls ───────────────────────────────────────
function setStore(el, val) {
  curStore = val;
  document.querySelectorAll('#storeFilter .tag-btn, #storeFilterMob .tag-btn').forEach(b=>b.classList.toggle('active', b.dataset.store===val));
  curPage = 1; applyFilters();
}
function setRegion(el, val) {
  curRegion = val;
  curOrigin = 'all';
  document.querySelectorAll('.region-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  rebuildOriginButtons(val);
  curPage = 1; applyFilters();
}

function rebuildOriginButtons(region) {
  const grp = document.getElementById('originFilter');
  if (region === 'all') {
    grp.innerHTML = '';
    return;
  }
  const origins = [...new Set(
    queryAll()
      .filter(p => region === '아시아' ? p.region.startsWith('아시아') : p.region === region)
      .map(p => p.origin)
  )].sort((a, b) => a.localeCompare(b, 'ko'));

  grp.innerHTML = `<button class="origin-chip active" data-origin="all" onclick="setOrigin(this,'all')">전체</button>`;
  origins.forEach(o => {
    const btn = document.createElement('button');
    btn.className = 'origin-chip';
    btn.dataset.origin = o;
    btn.textContent = o;
    btn.onclick = () => setOrigin(btn, o);
    grp.appendChild(btn);
  });
}
function setOrigin(el, val) {
  curOrigin = val;
  document.querySelectorAll('#originFilter .origin-chip').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  curPage = 1; applyFilters();
}
function setView(v) {
  curView = v;
  document.getElementById('btnTable').classList.toggle('active', v==='table');
  document.getElementById('btnCard').classList.toggle('active', v==='card');
  applyFilters();
}
function setQuick(val) {
  curQuick = val;
  document.querySelectorAll('.quick-btn').forEach(b => b.classList.toggle('active', b.dataset.quick === val));
  curPage = 1;
  applyFilters();
}

function resetFilters() {
  ['searchInput','searchInputMob'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  ['priceMin','priceMinMob'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  ['priceMax','priceMaxMob'].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  document.getElementById('sortSelect').value = 'price_asc';
  curStore = 'all'; curOrigin = 'all'; curRegion = 'all'; curQuick = 'all'; curPage = 1;
  document.querySelectorAll('#storeFilter .tag-btn, #storeFilterMob .tag-btn').forEach(b=>b.classList.toggle('active',b.dataset.store==='all'));
  document.querySelectorAll('.region-btn').forEach(b=>b.classList.toggle('active',b.dataset.region==='all'));
  document.querySelectorAll('.quick-btn').forEach(b=>b.classList.toggle('active',b.dataset.quick==='all'));
  rebuildOriginButtons('all');
  applyFilters();
}

// ── Core filter & render ──────────────────────────────────
function applyFilters() {
  if (!dbReady) return;
  const search  = document.getElementById('searchInput').value.toLowerCase().trim();
  const pMin    = parseFloat(document.getElementById('priceMin').value)||0;
  const pMax    = parseFloat(document.getElementById('priceMax').value)||Infinity;
  const sortVal = document.getElementById('sortSelect').value;

  const cutoff7 = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

  let filtered = queryAll().filter(p => {
    if (curQuick === 'new'     && !(p.added_date && p.added_date >= cutoff7)) return false;
    if (curQuick === 'special' && !p.isSpecial) return false;
    if (curQuick === 'decaf'   && !p.isDecaf)   return false;
    if (curRegion !== 'all') {
      const inRegion = curRegion === '아시아' ? p.region.startsWith('아시아') : p.region === curRegion;
      if (!inRegion) return false;
    }
    if (curOrigin !== 'all' && p.origin !== curOrigin) return false;
    if (curStore !== 'all' && p.store !== curStore) return false;
    if (p.price < pMin || p.price > pMax) return false;
    if (search) {
      const hay = (p.name+p.origin+p.notes+p.store+p.process).toLowerCase();
      if (!hay.includes(search)) return false;
    }
    return true;
  });

  ({
    price_asc:   ()=>filtered.sort((a,b)=>a.price-b.price),
    price_desc:  ()=>filtered.sort((a,b)=>b.price-a.price),
    latest:      ()=>filtered.sort((a,b)=>{
      if (!a.added_date && !b.added_date) return 0;
      if (!a.added_date) return 1;
      if (!b.added_date) return -1;
      return b.added_date.localeCompare(a.added_date);
    }),
    name_asc:    ()=>filtered.sort((a,b)=>a.name.localeCompare(b.name,'ko')),
    origin_asc:  ()=>filtered.sort((a,b)=>a.origin.localeCompare(b.origin,'ko')),
    process_asc: ()=>filtered.sort((a,b)=>a.process.localeCompare(b.process,'ko')),
  }[sortVal]||(() => filtered.sort((a,b)=>a.price-b.price)))();

  document.getElementById('showingCount').textContent = filtered.length;
  const mobCount = document.getElementById('showingCountMob');
  if (mobCount) mobCount.textContent = filtered.length;
  updateFilterBadge();
  renderPage(filtered);
}

function renderPage(filtered) {
  const totalPages = Math.max(1, Math.ceil(filtered.length/PAGE_SZ));
  if (curPage > totalPages) curPage = totalPages;
  const slice = filtered.slice((curPage-1)*PAGE_SZ, curPage*PAGE_SZ);
  const ctr = document.getElementById('productContainer');

  if (!filtered.length) {
    ctr.innerHTML = `<div class="empty-state"><h3>검색 결과가 없습니다</h3><p>다른 조건으로 검색해보세요</p></div>`;
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  const isMobile = window.innerWidth <= 600;
  if (curView === 'table') {
    if (isMobile) {
      ctr.innerHTML = '';
      renderTableMobile(slice, ctr);
    } else {
      renderTable(slice, ctr);
    }
  } else {
    renderCards(slice, ctr);
  }
  renderPagination(totalPages);
}

// ── Table render ──────────────────────────────────────────
function renderTable(items, ctr) {
  ctr.innerHTML = `<div class="tbl-wrap"><table class="coffee-table">
    <thead><tr>
      <th class="sortable" onclick="colSort('origin')">원산지</th>
      <th class="sortable" onclick="colSort('name')">커피 이름</th>
      <th>가공방식</th>
      <th class="sortable" onclick="colSort('price')" style="text-align:right">가격 (1kg)</th>
      <th>공급사</th>
      <th>구매</th>
    </tr></thead>
    <tbody>${items.map(p => {
      const sc   = STORE_CLS[p.store]||'sp-cp';
      const pc   = PROC_CLS[p.process]||'proc-unknown';
      const bdgs = [
        p.isNew     ? `<span class="bsm bsm-new">NEW</span>`     : '',
        p.isDecaf   ? `<span class="bsm bsm-decaf">디카페인</span>` : '',
        p.isSpecial ? `<span class="bsm bsm-special">스페셜티</span>` : '',
      ].filter(Boolean).join(' ');
      const notes = p.notes ? `<div class="name-notes">${p.notes}</div>` : '';
      return `<tr>
        <td><div class="origin-cell"><span class="oname">${p.origin}</span></div></td>
        <td class="name-wrap">
          <div class="name-main">${p.name}</div>
          ${notes}
          ${bdgs ? `<div class="name-badges">${bdgs}</div>` : ''}
        </td>
        <td><span class="proc-badge ${pc}">${p.process}</span></td>
        <td class="td-price"><span class="price-val">₩${p.price.toLocaleString()}</span><span class="price-kg">/kg</span></td>
        <td><span class="sp ${sc}">${p.store}</span></td>
        <td>${p.isSoldout ? '<span class="soldout-lnk">품절</span>' : `<a href="${p.url}" target="_blank" rel="noopener noreferrer" class="buy-lnk">구매</a>`}</td>
      </tr>`;
    }).join('')}</tbody>
  </table></div>`;
}

// ── Card render ───────────────────────────────────────────
function renderCards(items, ctr) {
  ctr.innerHTML = `<div class="card-grid">${items.map(p => {
    const sc   = STORE_CLS[p.store]||'sp-cp';
    const pc   = PROC_CLS[p.process]||'proc-unknown';
    const bdgs = [
      p.isNew     ? `<span class="bsm bsm-new">NEW</span>`     : '',
      p.isDecaf   ? `<span class="bsm bsm-decaf">디카페인</span>` : '',
      p.isSpecial ? `<span class="bsm bsm-special">스페셜티</span>` : '',
    ].filter(Boolean).join('');
    const notes = p.notes ? `<div class="c-notes">${p.notes}</div>` : '';
    return `<div class="c-card">
      <div class="c-top"><div class="c-badges">${bdgs}</div><span class="sp ${sc}">${p.store}</span></div>
      <div class="c-mid">
        <div class="c-title">${p.name}</div>
        <div class="c-origin">${p.origin} · ${p.region}</div>
        <span class="proc-badge ${pc}" style="margin-top:4px;display:inline-block">${p.process}</span>
        ${notes}
      </div>
      <div class="c-bot">
        <div><div class="c-price">₩${p.price.toLocaleString()}</div><div class="c-price-unit">1kg 기준</div></div>
        ${p.isSoldout ? '<span class="soldout-lnk">품절</span>' : `<a href="${p.url}" target="_blank" rel="noopener noreferrer" class="buy-lnk">구매</a>`}
      </div>
    </div>`;
  }).join('')}</div>`;
}

// ── Pagination ────────────────────────────────────────────
function renderPagination(total) {
  const pg = document.getElementById('pagination');
  if (total <= 1) { pg.innerHTML = ''; return; }
  let h = `<button class="pg-btn" onclick="goPage(${curPage-1})" ${curPage===1?'disabled':''} aria-label="이전">이전</button>`;
  for (let i=1; i<=total; i++) {
    if (i===1||i===total||Math.abs(i-curPage)<=2)
      h += `<button class="pg-btn ${i===curPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
    else if (Math.abs(i-curPage)===3)
      h += `<span style="padding:5px 3px;color:var(--text-muted)">…</span>`;
  }
  h += `<button class="pg-btn" onclick="goPage(${curPage+1})" ${curPage===total?'disabled':''} aria-label="다음">다음</button>`;
  pg.innerHTML = h;
}
function goPage(p) {
  if (p<1) return;
  curPage = p;
  applyFilters();
  document.querySelector('.content').scrollIntoView({behavior:'smooth',block:'start'});
}

// ── Column sort shortcut ──────────────────────────────────
function colSort(col) {
  const m = {origin:'origin_asc', name:'name_asc', price:'price_asc', process:'process_asc'};
  const sel = document.getElementById('sortSelect');
  const cur = sel.value;
  if (cur === m[col]) {
    if (col==='price') sel.value = 'price_desc';
  } else {
    sel.value = m[col]||'price_asc';
  }
  curPage = 1;
  applyFilters();
}

// ── Mobile drawer ─────────────────────────────────────────
function openDrawer() {
  document.getElementById('filterDrawer').classList.add('open');
  document.getElementById('drawerOverlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeDrawer() {
  document.getElementById('filterDrawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
  document.body.style.overflow = '';
}

// Sync drawer inputs → sidebar inputs → applyFilters
function syncSearch(el) {
  const other = el.id === 'searchInputMob' ? 'searchInput' : 'searchInputMob';
  document.getElementById(other).value = el.value;
  applyFilters();
}
function syncPriceMin(el) {
  const other = el.id === 'priceMinMob' ? 'priceMin' : 'priceMinMob';
  document.getElementById(other).value = el.value;
  applyFilters();
}
function syncPriceMax(el) {
  const other = el.id === 'priceMaxMob' ? 'priceMax' : 'priceMaxMob';
  document.getElementById(other).value = el.value;
  applyFilters();
}
function setStoreMob(el, val) {
  curStore = val;
  // sync both filter panels
  document.querySelectorAll('#storeFilter .tag-btn, #storeFilterMob .tag-btn').forEach(b => b.classList.toggle('active', b.dataset.store === val));
  curPage = 1; applyFilters();
}
function resetFiltersMob() {
  document.getElementById('searchInputMob').value = '';
  document.getElementById('priceMinMob').value = '';
  document.getElementById('priceMaxMob').value = '';
  resetFilters();
}

// Update filter badge count
function updateFilterBadge() {
  const active = [
    document.getElementById('searchInput').value.trim() !== '',
    document.getElementById('priceMin').value !== '',
    document.getElementById('priceMax').value !== '',
    curStore !== 'all',
    curOrigin !== 'all',
    curRegion !== 'all',
    curQuick !== 'all',
  ].filter(Boolean).length;
  const badge = document.getElementById('filterCount');
  if (badge) {
    badge.style.display = active > 0 ? 'inline-block' : 'none';
    badge.textContent = active;
  }
}

// ── Mobile table cards render ─────────────────────────────
function renderTableMobile(items, ctr) {
  ctr.innerHTML = items.map(p => {
    const sc   = STORE_CLS[p.store]||'sp-cp';
    const pc   = PROC_CLS[p.process]||'proc-unknown';
    const bdgs = [
      p.isNew     ? `<span class="bsm bsm-new">NEW</span>`     : '',
      p.isDecaf   ? `<span class="bsm bsm-decaf">디카페인</span>` : '',
      p.isSpecial ? `<span class="bsm bsm-special">스페셜티</span>` : '',
    ].filter(Boolean).join(' ');
    const notes = p.notes ? `<div class="mob-row-notes">${p.notes}</div>` : '';
    return `<div class="mob-row-card">
      <div class="mob-row-top">
        <div class="mob-row-name">${p.name}${bdgs ? ` <span style="display:inline-flex;gap:3px;vertical-align:middle">${bdgs}</span>` : ''}</div>
        <div class="mob-row-price">₩${p.price.toLocaleString()}<span style="font-size:0.62rem;font-weight:500;color:var(--text-muted);display:block;text-align:right">/kg</span></div>
      </div>
      <div class="mob-row-meta">
        <span class="mob-row-origin">${p.origin}</span>
        <span class="proc-badge ${pc}">${p.process}</span>
      </div>
      ${notes}
      <div class="mob-row-bot">
        <span class="sp ${sc}">${p.store}</span>
        ${p.isSoldout ? '<span class="soldout-lnk">품절</span>' : `<a href="${p.url}" target="_blank" rel="noopener noreferrer" class="buy-lnk">구매</a>`}
      </div>
    </div>`;
  }).join('');
}

initDB();
