// ── State ─────────────────────────────────────────────────
let DB = null;
let curStore = 'all', curOrigin = 'all', curRegion = 'all', curView = 'table', curPage = 1;
const PAGE_SZ = 50;

// ── DB init ───────────────────────────────────────────────
async function initDB() {
  const SQL = await initSqlJs({
    locateFile: f => `https://cdn.jsdelivr.net/npm/sql.js@1.12.0/dist/${f}`
  });
  const res = await fetch('database.sql');
  const sql = await res.text();
  DB = new SQL.Database();
  DB.run(sql);
  init();
}

function queryAll() {
  const result = DB.exec('SELECT id,store,name,price,origin,region,process,notes,url,isNew,isDecaf,isSpecial FROM products');
  if (!result.length) return [];
  const { columns, values } = result[0];
  return values.map(row => {
    const p = {};
    columns.forEach((c, i) => p[c] = row[i]);
    p.isNew     = p.isNew     === 1;
    p.isDecaf   = p.isDecaf   === 1;
    p.isSpecial = p.isSpecial === 1;
    return p;
  });
}

// ── Init ──────────────────────────────────────────────────
function init() {
  const products = queryAll();

  const origins = [...new Set(products.map(p => p.origin))].sort((a,b) => a.localeCompare(b,'ko'));
  const grp = document.getElementById('originFilter');
  origins.forEach(o => {
    const btn = document.createElement('button');
    btn.className = 'origin-chip';
    btn.dataset.origin = o;
    btn.textContent = `${FLAG[o]||'🌍'} ${o}`;
    btn.onclick = () => setOrigin(btn, o);
    grp.appendChild(btn);
  });

  document.getElementById('totalCount').textContent = products.length;
  document.getElementById('originCount').textContent = origins.length;

  buildStatBars(products);
  applyFilters();
}

// ── Statistics sidebar ────────────────────────────────────
function buildStatBars(products) {
  const oc = {};
  products.forEach(p => { oc[p.origin] = (oc[p.origin]||0)+1; });
  const topO = Object.entries(oc).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const maxO = topO[0]?.[1]||1;
  document.getElementById('originStats').innerHTML = topO.map(([o,c])=>`
    <div class="stat-bar-item">
      <div class="stat-bar-lbl"><span>${FLAG[o]||'🌍'} ${o}</span><span>${c}</span></div>
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
  document.querySelectorAll('#storeFilter .tag-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
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
  const all = queryAll();
  const origins = [...new Set(
    all
      .filter(p => region === 'all' || (region === '아시아' ? p.region.startsWith('아시아') : p.region === region))
      .map(p => p.origin)
  )].sort((a, b) => a.localeCompare(b, 'ko'));

  const grp = document.getElementById('originFilter');
  grp.innerHTML = `<button class="origin-chip active" data-origin="all" onclick="setOrigin(this,'all')">전체</button>`;
  origins.forEach(o => {
    const btn = document.createElement('button');
    btn.className = 'origin-chip';
    btn.dataset.origin = o;
    btn.textContent = `${FLAG[o]||'🌍'} ${o}`;
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
function resetFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('processSelect').value = '';
  document.getElementById('priceMin').value = '';
  document.getElementById('priceMax').value = '';
  document.getElementById('sortSelect').value = 'price_asc';
  curStore = 'all'; curOrigin = 'all'; curRegion = 'all'; curPage = 1;
  document.querySelectorAll('#storeFilter .tag-btn').forEach(b=>b.classList.toggle('active',b.dataset.store==='all'));
  document.querySelectorAll('.region-btn').forEach(b=>b.classList.toggle('active',b.dataset.region==='all'));
  rebuildOriginButtons('all');
  applyFilters();
}

// ── Core filter & render ──────────────────────────────────
function applyFilters() {
  if (!DB) return;
  const search  = document.getElementById('searchInput').value.toLowerCase().trim();
  const process = document.getElementById('processSelect').value;
  const pMin    = parseFloat(document.getElementById('priceMin').value)||0;
  const pMax    = parseFloat(document.getElementById('priceMax').value)||Infinity;
  const sortVal = document.getElementById('sortSelect').value;

  let filtered = queryAll().filter(p => {
    if (curRegion !== 'all') {
      const inRegion = curRegion === '아시아' ? p.region.startsWith('아시아') : p.region === curRegion;
      if (!inRegion) return false;
    }
    if (curOrigin !== 'all' && p.origin !== curOrigin) return false;
    if (process && p.process !== process) return false;
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
    name_asc:    ()=>filtered.sort((a,b)=>a.name.localeCompare(b.name,'ko')),
    origin_asc:  ()=>filtered.sort((a,b)=>a.origin.localeCompare(b.origin,'ko')),
    process_asc: ()=>filtered.sort((a,b)=>a.process.localeCompare(b.process,'ko')),
  }[sortVal]||(() => filtered.sort((a,b)=>a.price-b.price)))();

  document.getElementById('showingCount').textContent = filtered.length;
  renderPage(filtered);
}

function renderPage(filtered) {
  const totalPages = Math.max(1, Math.ceil(filtered.length/PAGE_SZ));
  if (curPage > totalPages) curPage = totalPages;
  const slice = filtered.slice((curPage-1)*PAGE_SZ, curPage*PAGE_SZ);
  const ctr = document.getElementById('productContainer');

  if (!filtered.length) {
    ctr.innerHTML = `<div class="empty-state"><div class="ei">☕</div><h3>검색 결과가 없습니다</h3><p>다른 조건으로 검색해보세요</p></div>`;
    document.getElementById('pagination').innerHTML = '';
    return;
  }

  if (curView === 'table') renderTable(slice, ctr);
  else renderCards(slice, ctr);
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
      const flag = FLAG[p.origin]||'🌍';
      const sc   = STORE_CLS[p.store]||'sp-cp';
      const pc   = PROC_CLS[p.process]||'proc-unknown';
      const bdgs = [
        p.isNew     ? `<span class="bsm bsm-new">NEW</span>`     : '',
        p.isDecaf   ? `<span class="bsm bsm-decaf">디카페인</span>` : '',
        p.isSpecial ? `<span class="bsm bsm-special">스페셜티</span>` : '',
      ].filter(Boolean).join(' ');
      const notes = p.notes ? `<div class="name-notes">☕ ${p.notes}</div>` : '';
      return `<tr>
        <td><div class="origin-cell"><span class="oflag">${flag}</span><span class="oname">${p.origin}</span></div></td>
        <td class="name-wrap">
          <div class="name-main">${p.name}</div>
          ${notes}
          ${bdgs ? `<div class="name-badges">${bdgs}</div>` : ''}
        </td>
        <td><span class="proc-badge ${pc}">${p.process}</span></td>
        <td class="td-price"><span class="price-val">₩${p.price.toLocaleString()}</span><span class="price-kg">/kg</span></td>
        <td><span class="sp ${sc}">${p.store}</span></td>
        <td><a href="${p.url}" target="_blank" rel="noopener" class="buy-lnk">구매 →</a></td>
      </tr>`;
    }).join('')}</tbody>
  </table></div>`;
}

// ── Card render ───────────────────────────────────────────
function renderCards(items, ctr) {
  ctr.innerHTML = `<div class="card-grid">${items.map(p => {
    const flag = FLAG[p.origin]||'🌍';
    const sc   = STORE_CLS[p.store]||'sp-cp';
    const pc   = PROC_CLS[p.process]||'proc-unknown';
    const bdgs = [
      p.isNew     ? `<span class="bsm bsm-new">NEW</span>`     : '',
      p.isDecaf   ? `<span class="bsm bsm-decaf">디카페인</span>` : '',
      p.isSpecial ? `<span class="bsm bsm-special">스페셜티</span>` : '',
    ].filter(Boolean).join('');
    const notes = p.notes ? `<div class="c-notes">☕ ${p.notes}</div>` : '';
    return `<div class="c-card">
      <div class="c-top"><div class="c-badges">${bdgs}</div><span class="sp ${sc}">${p.store}</span></div>
      <div class="c-mid">
        <div class="c-title">${p.name}</div>
        <div class="c-origin"><span style="font-size:1.05rem">${flag}</span> ${p.origin} · ${p.region}</div>
        <span class="proc-badge ${pc}" style="margin-top:4px;display:inline-block">${p.process}</span>
        ${notes}
      </div>
      <div class="c-bot">
        <div><div class="c-price">₩${p.price.toLocaleString()}</div><div class="c-price-unit">1kg 기준</div></div>
        <a href="${p.url}" target="_blank" rel="noopener" class="buy-lnk">구매 →</a>
      </div>
    </div>`;
  }).join('')}</div>`;
}

// ── Pagination ────────────────────────────────────────────
function renderPagination(total) {
  const pg = document.getElementById('pagination');
  if (total <= 1) { pg.innerHTML = ''; return; }
  let h = `<button class="pg-btn" onclick="goPage(${curPage-1})" ${curPage===1?'disabled':''}>◀</button>`;
  for (let i=1; i<=total; i++) {
    if (i===1||i===total||Math.abs(i-curPage)<=2)
      h += `<button class="pg-btn ${i===curPage?'active':''}" onclick="goPage(${i})">${i}</button>`;
    else if (Math.abs(i-curPage)===3)
      h += `<span style="padding:5px 3px;color:var(--text-muted)">…</span>`;
  }
  h += `<button class="pg-btn" onclick="goPage(${curPage+1})" ${curPage===total?'disabled':''}>▶</button>`;
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

initDB();
