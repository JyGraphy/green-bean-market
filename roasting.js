'use strict';
/* ── Supabase ── */
const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON);
let currentUserId = null;
let allProfiles = [];
let activeId = null;
let chartInstance = null;
let deleteTargetId = null;

/* ── DOM refs ── */
const profileList   = document.getElementById('profileList');
const listEmpty     = document.getElementById('listEmpty');
const profileCount  = document.getElementById('profileCount');
const searchInput   = document.getElementById('searchInput');
const welcomeView   = document.getElementById('welcomeView');
const formView      = document.getElementById('formView');
const detailView    = document.getElementById('detailView');
const profileForm   = document.getElementById('profileForm');
const parseStatus   = document.getElementById('parseStatus');
const fileDrop      = document.getElementById('fileDrop');
const fileInput     = document.getElementById('fileInput');
const confirmOverlay = document.getElementById('confirmOverlay');
const metricsRow    = document.getElementById('metricsRow');
const feedbackPanel = document.getElementById('feedbackPanel');
const chartWrap     = document.getElementById('chartWrap');
const memoSection   = document.getElementById('memoSection');

/* ── Init ── */
(async () => {
  const { data: { session } } = await sb.auth.getSession();
  if (!session) { location.href = 'auth.html?next=roasting.html'; return; }
  currentUserId = session.user.id;

  document.getElementById('btnLogout').addEventListener('click', async () => {
    await sb.auth.signOut();
    location.href = 'auth.html';
  });

  setupUI();
  await loadProfiles();
})();

/* ── UI wiring ── */
function setupUI() {
  document.getElementById('btnNewProfile').addEventListener('click', openFormNew);
  document.getElementById('btnWelcomeNew').addEventListener('click', openFormNew);
  document.getElementById('btnFormClose').addEventListener('click', closeForm);
  document.getElementById('btnFormCancel').addEventListener('click', closeForm);
  document.getElementById('btnEdit').addEventListener('click', openFormEdit);
  document.getElementById('btnDelete').addEventListener('click', () => {
    deleteTargetId = activeId;
    confirmOverlay.style.display = 'flex';
  });
  document.getElementById('btnConfirmNo').addEventListener('click', () => { confirmOverlay.style.display = 'none'; });
  document.getElementById('btnConfirmYes').addEventListener('click', deleteProfile);

  profileForm.addEventListener('submit', saveProfile);
  searchInput.addEventListener('input', renderList);

  fileDrop.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', e => handleFile(e.target.files[0]));
  fileDrop.addEventListener('dragover', e => { e.preventDefault(); fileDrop.classList.add('drag-over'); });
  fileDrop.addEventListener('dragleave', () => fileDrop.classList.remove('drag-over'));
  fileDrop.addEventListener('drop', e => {
    e.preventDefault();
    fileDrop.classList.remove('drag-over');
    handleFile(e.dataTransfer.files[0]);
  });
}

/* ── Supabase CRUD ── */
async function loadProfiles() {
  const { data, error } = await sb.from('roasting_profiles')
    .select('*')
    .eq('user_id', currentUserId)
    .order('roast_date', { ascending: false });
  if (error) { console.error(error); return; }
  allProfiles = data || [];
  renderList();
}

async function saveProfile(e) {
  e.preventDefault();
  const beanName = document.getElementById('fBeanName').value.trim();
  if (!beanName) { document.getElementById('fBeanName').focus(); return; }

  const btRaw = document.getElementById('fBTData').value.trim();
  const etRaw = document.getElementById('fETData').value.trim();
  const btArr = btRaw ? btRaw.split(',').map(v => parseFloat(v.trim())).filter(n => !isNaN(n)) : [];
  const etArr = etRaw ? etRaw.split(',').map(v => parseFloat(v.trim())).filter(n => !isNaN(n)) : [];

  const payload = {
    user_id:           currentUserId,
    bean_name:         beanName,
    roastery:          document.getElementById('fRoastery').value.trim() || null,
    roast_date:        document.getElementById('fRoastDate').value || null,
    green_weight:      parseFloatOrNull('fGreenWeight'),
    roasted_weight:    parseFloatOrNull('fRoastedWeight'),
    charge_temp:       parseFloatOrNull('fChargeTemp'),
    drop_temp:         parseFloatOrNull('fDropTemp'),
    total_time:        parseFloatOrNull('fTotalTime'),
    agtron:            parseFloatOrNull('fAgtron'),
    ambient_temp:      parseFloatOrNull('fAmbientTemp'),
    ambient_humidity:  parseFloatOrNull('fAmbientHumidity'),
    memo:              document.getElementById('fMemo').value.trim() || null,
    e_charge:          parseFloatOrNull('eCharge'),
    e_tp:              parseFloatOrNull('eTP'),
    e_dry_end:         parseFloatOrNull('eDryEnd'),
    e_fcs:             parseFloatOrNull('eFCs'),
    e_fce:             parseFloatOrNull('eFCe'),
    e_scs:             parseFloatOrNull('eSCs'),
    e_drop:            parseFloatOrNull('eDrop'),
    bt_series:         btArr.length ? btArr : null,
    et_series:         etArr.length ? etArr : null,
  };

  const id = document.getElementById('fId').value;
  let error;
  if (id) {
    ({ error } = await sb.from('roasting_profiles').update(payload).eq('id', id));
  } else {
    ({ error } = await sb.from('roasting_profiles').insert(payload));
  }
  if (error) { alert('저장 실패: ' + error.message); return; }

  await loadProfiles();
  closeForm();
  if (id) {
    showDetail(allProfiles.find(p => String(p.id) === id));
  } else {
    showDetail(allProfiles[0]);
  }
}

async function deleteProfile() {
  confirmOverlay.style.display = 'none';
  if (!deleteTargetId) return;
  const { error } = await sb.from('roasting_profiles').delete().eq('id', deleteTargetId);
  if (error) { alert('삭제 실패: ' + error.message); return; }
  activeId = null;
  deleteTargetId = null;
  await loadProfiles();
  showView('welcome');
}

function parseFloatOrNull(id) {
  const v = parseFloat(document.getElementById(id).value);
  return isNaN(v) ? null : v;
}

/* ── 목록 렌더 ── */
function renderList() {
  const q = searchInput.value.toLowerCase();
  const filtered = allProfiles.filter(p =>
    p.bean_name.toLowerCase().includes(q) ||
    (p.roastery || '').toLowerCase().includes(q)
  );

  profileCount.textContent = `${filtered.length}개`;

  if (!filtered.length) {
    listEmpty.style.display = '';
    return;
  }
  listEmpty.style.display = 'none';

  const items = filtered.map(p => {
    const dtr = calcDTR(p);
    const wl  = calcWeightLoss(p);
    const sub = [
      p.roast_date || '',
      wl != null ? `감량 ${wl.toFixed(1)}%` : '',
      dtr != null ? `DTR ${dtr.toFixed(1)}%` : '',
    ].filter(Boolean).join(' · ');

    const el = document.createElement('div');
    el.className = 'rp-list-item' + (p.id === activeId ? ' active' : '');
    el.dataset.id = p.id;
    el.innerHTML = `
      <div class="rp-list-icon">🔥</div>
      <div class="rp-list-info">
        <div class="rp-list-name">${esc(p.bean_name)}</div>
        <div class="rp-list-sub">${esc(sub)}</div>
      </div>`;
    el.addEventListener('click', () => showDetail(p));
    return el;
  });

  profileList.innerHTML = '';
  profileList.appendChild(listEmpty);
  items.forEach(el => profileList.appendChild(el));
}

/* ── 폼 열기/닫기 ── */
function openFormNew() {
  document.getElementById('formTitle').textContent = '새 프로파일 추가';
  document.getElementById('fId').value = '';
  profileForm.reset();
  parseStatus.style.display = 'none';
  showView('form');
}

function openFormEdit() {
  const p = allProfiles.find(x => x.id === activeId);
  if (!p) return;
  document.getElementById('formTitle').textContent = '프로파일 편집';
  document.getElementById('fId').value = p.id;
  document.getElementById('fBeanName').value = p.bean_name || '';
  document.getElementById('fRoastery').value = p.roastery || '';
  document.getElementById('fRoastDate').value = p.roast_date || '';
  document.getElementById('fGreenWeight').value = p.green_weight || '';
  document.getElementById('fRoastedWeight').value = p.roasted_weight || '';
  document.getElementById('fChargeTemp').value = p.charge_temp || '';
  document.getElementById('fDropTemp').value = p.drop_temp || '';
  document.getElementById('fTotalTime').value = p.total_time || '';
  document.getElementById('fAgtron').value = p.agtron || '';
  document.getElementById('fAmbientTemp').value = p.ambient_temp || '';
  document.getElementById('fAmbientHumidity').value = p.ambient_humidity || '';
  document.getElementById('fMemo').value = p.memo || '';
  document.getElementById('eCharge').value = p.e_charge ?? 0;
  document.getElementById('eTP').value = p.e_tp || '';
  document.getElementById('eDryEnd').value = p.e_dry_end || '';
  document.getElementById('eFCs').value = p.e_fcs || '';
  document.getElementById('eFCe').value = p.e_fce || '';
  document.getElementById('eSCs').value = p.e_scs || '';
  document.getElementById('eDrop').value = p.e_drop || '';
  document.getElementById('fBTData').value = p.bt_series ? p.bt_series.join(',') : '';
  document.getElementById('fETData').value = p.et_series ? p.et_series.join(',') : '';
  parseStatus.style.display = 'none';
  showView('form');
}

function closeForm() {
  showView(activeId ? 'detail' : 'welcome');
}

/* ── 상세 뷰 ── */
function showDetail(p) {
  if (!p) return;
  activeId = p.id;
  renderList();

  document.getElementById('detailName').textContent = p.bean_name;
  const metaParts = [p.roastery, p.roast_date].filter(Boolean);
  document.getElementById('detailMeta').textContent = metaParts.join(' · ');

  renderMetrics(p);
  renderFeedback(p);
  renderChart(p);

  if (p.memo) {
    document.getElementById('detailMemo').textContent = p.memo;
    memoSection.style.display = '';
  } else {
    memoSection.style.display = 'none';
  }

  showView('detail');
}

function showView(name) {
  welcomeView.style.display = name === 'welcome' ? '' : 'none';
  formView.style.display    = name === 'form'    ? '' : 'none';
  detailView.style.display  = name === 'detail'  ? '' : 'none';
}

/* ── 계산 헬퍼 ── */
function calcDTR(p) {
  const drop  = p.e_drop  || p.total_time;
  const fcs   = p.e_fcs;
  const total = p.total_time;
  if (!fcs || !drop || !total) return null;
  return ((drop - fcs) / total) * 100;
}

function calcWeightLoss(p) {
  if (!p.green_weight || !p.roasted_weight) return null;
  return ((p.green_weight - p.roasted_weight) / p.green_weight) * 100;
}

function calcDryPhasePct(p) {
  const dry   = p.e_dry_end;
  const total = p.total_time;
  if (!dry || !total) return null;
  return (dry / total) * 100;
}

function calcMaillardPhasePct(p) {
  const dry   = p.e_dry_end;
  const fcs   = p.e_fcs;
  const total = p.total_time;
  if (!dry || !fcs || !total) return null;
  return ((fcs - dry) / total) * 100;
}

function formatTime(sec) {
  if (sec == null) return '—';
  return `${Math.floor(sec / 60)}:${String(Math.round(sec % 60)).padStart(2, '0')}`;
}

/* ── 지표 렌더 ── */
function renderMetrics(p) {
  const wl  = calcWeightLoss(p);
  const dtr = calcDTR(p);
  const dry = calcDryPhasePct(p);
  const mai = calcMaillardPhasePct(p);

  const cards = [
    {
      label: '총 로스팅 시간', value: formatTime(p.total_time), unit: '',
      cls: p.total_time ? (p.total_time < 600 ? 'warn' : p.total_time > 900 ? 'warn' : 'good') : '',
    },
    {
      label: '감량률', value: wl != null ? wl.toFixed(1) : '—', unit: '%',
      cls: wl != null ? (wl < 11 ? 'warn' : wl > 18 ? 'warn' : 'good') : '',
    },
    {
      label: 'DTR', value: dtr != null ? dtr.toFixed(1) : '—', unit: '%',
      cls: dtr != null ? (dtr < 18 ? 'bad' : dtr > 28 ? 'warn' : 'good') : '',
    },
    {
      label: '건조 단계', value: dry != null ? dry.toFixed(1) : '—', unit: '%',
      cls: dry != null ? (dry < 25 ? 'warn' : dry > 45 ? 'warn' : 'good') : '',
    },
    {
      label: '마이야르 단계', value: mai != null ? mai.toFixed(1) : '—', unit: '%',
      cls: mai != null ? (mai < 25 ? 'warn' : mai > 45 ? 'warn' : 'good') : '',
    },
    {
      label: '투입온도', value: p.charge_temp || '—', unit: '°C', cls: '',
    },
    {
      label: '배출온도', value: p.drop_temp || '—', unit: '°C', cls: '',
    },
    {
      label: 'Agtron', value: p.agtron || '—', unit: '',
      cls: p.agtron ? (p.agtron >= 75 ? 'good' : p.agtron >= 55 ? 'good' : p.agtron >= 40 ? 'warn' : 'bad') : '',
    },
  ];

  metricsRow.innerHTML = cards.map(c => `
    <div class="rp-metric-card ${c.cls}">
      <div class="rp-metric-label">${c.label}</div>
      <div class="rp-metric-value">${c.value}</div>
      <div class="rp-metric-unit">${c.unit}</div>
    </div>`).join('');
}

/* ── 피드백 엔진 ── */
function renderFeedback(p) {
  const items = [];
  const wl  = calcWeightLoss(p);
  const dtr = calcDTR(p);
  const dry = calcDryPhasePct(p);
  const mai = calcMaillardPhasePct(p);
  const bt  = p.bt_series;

  /* 1. DTR 분석 */
  if (dtr != null) {
    if (dtr < 18) {
      items.push({ type:'bad', icon:'⚠️', title:'DTR 부족 — 발달 미흡', text:`개발 시간 비율이 ${dtr.toFixed(1)}%로 권장 범위(20–25%)에 미치지 못합니다. 크랙 이후 열 공급이 부족하거나 배출이 너무 이릅니다. 신맛과 미성숙 향미가 나타날 수 있습니다.` });
    } else if (dtr > 28) {
      items.push({ type:'warn', icon:'⚡', title:'DTR 과다 — 과발달 위험', text:`DTR ${dtr.toFixed(1)}%로 높습니다. 개발 단계 과열로 쓴맛·탄 향·평탄한 컵 프로파일이 나타날 수 있습니다. 크랙 이후 열을 줄이거나 더 이른 시점에 배출하는 것을 고려하세요.` });
    } else {
      items.push({ type:'good', icon:'✅', title:'DTR 양호', text:`DTR ${dtr.toFixed(1)}%는 권장 범위 안에 있습니다. 마이야르 반응과 캐러멜화의 균형이 잘 잡혀 있을 가능성이 높습니다.` });
    }
  }

  /* 2. 감량률 분석 */
  if (wl != null) {
    if (wl < 11) {
      items.push({ type:'warn', icon:'💧', title:'감량률 낮음 — 수분 잔류', text:`감량률 ${wl.toFixed(1)}%로 낮습니다(권장: 라이트 11–13%, 다크 17–18%). 수분이 충분히 제거되지 않아 풋내, 쇳내, 발효취가 발생할 수 있습니다.` });
    } else if (wl > 18) {
      items.push({ type:'warn', icon:'🔥', title:'감량률 높음 — 과도한 열 노출', text:`감량률 ${wl.toFixed(1)}%로 높습니다. 지나친 열 노출로 오일이 표면으로 올라오거나 탄화 향이 날 수 있습니다.` });
    } else {
      items.push({ type:'good', icon:'✅', title:'감량률 정상', text:`감량률 ${wl.toFixed(1)}%는 일반적인 범위 내에 있습니다.` });
    }
  }

  /* 3. 건조 단계 */
  if (dry != null) {
    if (dry < 25) {
      items.push({ type:'warn', icon:'⚡', title:'건조 단계 짧음 — Too Fast 패턴', text:`건조 단계 비율 ${dry.toFixed(1)}%는 너무 짧습니다. 빠른 승온으로 마이야르 반응이 과활성화(Maillard Max)될 수 있어 밝은 산미는 있으나 바디감이 얕을 수 있습니다.` });
    } else if (dry > 45) {
      items.push({ type:'warn', icon:'🐢', title:'건조 단계 길음 — Too Slow 패턴', text:`건조 단계 비율 ${dry.toFixed(1)}%로 과도합니다. 저온 장시간으로 마이야르 반응이 최소화(Maillard Minimum)되어 베이킹 결함·밀·짚 향이 나타날 수 있습니다.` });
    }
  }

  /* 4. 마이야르 단계 */
  if (mai != null) {
    if (mai < 25) {
      items.push({ type:'bad', icon:'⚠️', title:'마이야르 단계 짧음 — 풍미 부족', text:`마이야르 단계 ${mai.toFixed(1)}%로 짧습니다. 갈변·복잡한 향미 발달이 부족해 밋밋한 컵이 될 수 있습니다. 1차 크랙 전 단계에서 열을 더 유지하세요.` });
    } else if (mai > 45) {
      items.push({ type:'warn', icon:'⚡', title:'마이야르 단계 과다 — Gas Over 패턴', text:`마이야르 단계 ${mai.toFixed(1)}%가 길어 캐러멜화 단계가 상대적으로 짧아집니다. 단맛은 강하지만 평탄한 컵 프로파일이 나타날 수 있습니다.` });
    }
  }

  /* 5. ROR 크래시 감지 (BT 시계열 기반) */
  if (bt && bt.length >= 4) {
    const rors = [];
    for (let i = 1; i < bt.length; i++) rors.push(bt[i] - bt[i-1]);
    let crash = false, flick = false;
    for (let i = 1; i < rors.length - 1; i++) {
      const drop = rors[i-1] - rors[i];
      if (drop > 5 && rors[i+1] !== undefined && rors[i+1] < rors[i]) crash = true;
      if (rors[i] > rors[i-1] + 3 && i > rors.length * 0.7) flick = true;
    }
    if (crash) {
      items.push({ type:'bad', icon:'📉', title:'ROR 크래시 감지', text:'BT 곡선에서 ROR이 급격히 떨어지는 구간이 있습니다. 이는 "베이킹 결함"으로 이어질 수 있습니다. 해당 구간에서 가스를 서서히 줄이고 드럼 속도를 점검하세요.' });
    }
    if (flick) {
      items.push({ type:'warn', icon:'📈', title:'ROR 플릭 감지', text:'개발 후반에 ROR이 다시 상승하는 패턴이 감지됩니다. 지나친 열 공급은 표면 탄화로 이어질 수 있습니다. 배출 시점을 앞당기거나 가스를 낮추세요.' });
    }
    if (!crash && !flick) {
      items.push({ type:'good', icon:'📊', title:'ROR 곡선 양호', text:'BT 데이터에서 크래시나 플릭 패턴이 감지되지 않았습니다. ROR이 전반적으로 부드럽게 감소하고 있습니다.' });
    }
  }

  /* 6. 총 시간 */
  if (p.total_time) {
    if (p.total_time < 420) {
      items.push({ type:'bad', icon:'⚡', title:'로스팅 시간 너무 짧음', text:`총 ${formatTime(p.total_time)}으로 매우 짧습니다. 급격한 열 투입으로 외부는 탄화되고 내부는 생두 상태인 불균등 로스팅이 발생할 수 있습니다.` });
    } else if (p.total_time > 1200) {
      items.push({ type:'warn', icon:'🐌', title:'로스팅 시간 길음', text:`총 ${formatTime(p.total_time)}으로 길습니다. 장시간 저온 로스팅은 베이킹·평탄화 결함으로 이어질 수 있습니다.` });
    }
  }

  /* 7. Agtron 기반 로스팅 수준 안내 */
  if (p.agtron) {
    let level, note;
    if (p.agtron >= 75)      { level = '라이트'; note = '과일향·산미 위주. DTR과 수분 제거에 집중하세요.'; }
    else if (p.agtron >= 55) { level = '미디엄'; note = '균형 잡힌 단맛·산미·바디. 스페셜티에 이상적인 범위입니다.'; }
    else if (p.agtron >= 40) { level = '미디엄-다크'; note = '쓴맛·초콜릿 노트 발달. 개발 단계 열 조절에 주의하세요.'; }
    else                      { level = '다크'; note = '탄화 향 위험. 1차 크랙 이후 열을 과감히 줄이세요.'; }
    items.push({ type:'info', icon:'🎨', title:`Agtron ${p.agtron} — ${level} 로스팅`, text: note });
  }

  /* 8. 데이터 없을 때 */
  if (!items.length) {
    items.push({ type:'info', icon:'ℹ️', title:'더 많은 피드백을 위해 데이터를 입력하세요', text:'이벤트 포인트(건조 종료, 1차 크랙, 배출 시간)와 투입/배출량을 입력하면 DTR, 감량률, 단계별 비율 분석이 제공됩니다.' });
  }

  feedbackPanel.innerHTML = `
    <div class="rp-feedback-title">🤖 자동 피드백 분석</div>
    <div class="rp-feedback-list">
      ${items.map(i => `
        <div class="rp-feedback-item ${i.type}">
          <span class="rp-feedback-icon">${i.icon}</span>
          <div class="rp-feedback-text">
            <strong>${i.title}</strong>
            ${i.text}
          </div>
        </div>`).join('')}
    </div>`;
}

/* ── 차트 렌더 ── */
function renderChart(p) {
  if (chartInstance) { chartInstance.destroy(); chartInstance = null; }
  const bt = p.bt_series;
  const et = p.et_series;

  if (!bt || bt.length < 2) {
    chartWrap.style.display = 'none';
    return;
  }
  chartWrap.style.display = '';

  const interval = p.total_time ? p.total_time / (bt.length - 1) : 15;
  const labels = bt.map((_, i) => formatTime(Math.round(i * interval)));

  const rors = [null];
  for (let i = 1; i < bt.length; i++) {
    const delta = (bt[i] - bt[i-1]) / (interval / 60);
    rors.push(+delta.toFixed(2));
  }

  const annotations = {};
  const eventDefs = [
    { key:'e_charge',  label:'CHARGE', color:'#6366f1' },
    { key:'e_tp',      label:'TP',     color:'#8b5cf6' },
    { key:'e_dry_end', label:'DRY',    color:'#f59e0b' },
    { key:'e_fcs',     label:'FC↑',    color:'#ef4444' },
    { key:'e_fce',     label:'FC↓',    color:'#f97316' },
    { key:'e_scs',     label:'SC↑',    color:'#dc2626' },
    { key:'e_drop',    label:'DROP',   color:'#16a34a' },
  ];
  eventDefs.forEach(({ key, label, color }) => {
    const sec = p[key];
    if (sec == null) return;
    const x = Math.round(sec / interval);
    annotations[key] = {
      type: 'line', xMin: x, xMax: x,
      borderColor: color, borderWidth: 1.5, borderDash: [4, 3],
      label: { display: true, content: label, position: 'start', font: { size: 10 }, color },
    };
  });

  chartInstance = new Chart(document.getElementById('roastChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'BT (°C)',
          data: bt,
          borderColor: '#e07b2a',
          backgroundColor: 'rgba(224,123,42,.08)',
          borderWidth: 2.5,
          pointRadius: 0,
          tension: 0.4,
          yAxisID: 'yTemp',
        },
        ...(et ? [{
          label: 'ET (°C)',
          data: et,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59,130,246,.05)',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          borderDash: [5, 3],
          yAxisID: 'yTemp',
        }] : []),
        {
          label: 'ROR (°C/min)',
          data: rors,
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34,197,94,.08)',
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          yAxisID: 'yROR',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: {
          label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(1) ?? '—'}`
        }},
        annotation: { annotations },
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 10, font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,.05)' },
        },
        yTemp: {
          type: 'linear',
          position: 'left',
          title: { display: true, text: '온도 (°C)', font: { size: 11 } },
          ticks: { font: { size: 11 } },
          grid: { color: 'rgba(0,0,0,.05)' },
        },
        yROR: {
          type: 'linear',
          position: 'right',
          title: { display: true, text: 'ROR (°C/min)', font: { size: 11 } },
          ticks: { font: { size: 11 } },
          grid: { drawOnChartArea: false },
          min: 0,
          max: 30,
        },
      },
    },
  });
}

/* ── 파일 파서 ── */
function handleFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const content = e.target.result;
    try {
      if (file.name.endsWith('.csv')) {
        parseCSV(content);
      } else {
        parseAlog(content);
      }
    } catch (err) {
      showParseStatus(`파싱 실패: ${err.message}`, false);
    }
  };
  reader.readAsText(file);
}

function parseAlog(text) {
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    text = text.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false').replace(/None/g, 'null');
    data = JSON.parse(text);
  }

  const r = Array.isArray(data) ? data[0] : data;
  const timex = r.timex || [];
  const bt    = r.temp2 || r.temp1 || [];
  const et    = r.temp1 || [];
  const ti    = r.timeindex || [];

  if (r.beans)    document.getElementById('fBeanName').value = r.beans;
  if (r.roaster)  document.getElementById('fRoastery').value = r.roaster;
  if (r.roastdate) document.getElementById('fRoastDate').value = r.roastdate?.split('T')[0] || '';
  if (r.weight && r.weight[0]) document.getElementById('fGreenWeight').value = r.weight[0];
  if (r.weight && r.weight[1]) document.getElementById('fRoastedWeight').value = r.weight[1];
  if (ti[0] !== undefined && timex[ti[0]] != null) document.getElementById('fChargeTemp').value = Math.round(bt[ti[0]] || 0);
  if (ti[6] !== undefined && timex[ti[6]] != null) {
    document.getElementById('fDropTemp').value = Math.round(bt[ti[6]] || 0);
    document.getElementById('fTotalTime').value = Math.round(timex[ti[6]]);
    document.getElementById('eDrop').value = Math.round(timex[ti[6]]);
  }
  const eventMap = { 0:'eCharge', 5:'eDryEnd', 2:'eFCs', 3:'eFCe', 4:'eSCs', 6:'eDrop' };
  // Artisan timeindex: [CHARGE, DRYe, FCs, FCe, SCs, SCe, DROP, COOL]
  const artisanMap = [[0,'eCharge'],[1,'eDryEnd'],[2,'eFCs'],[3,'eFCe'],[4,'eSCs'],[6,'eDrop']];
  artisanMap.forEach(([idx, fid]) => {
    const t = timex[ti[idx]];
    if (t != null) document.getElementById(fid).value = Math.round(t);
  });

  if (bt.length > 1) {
    document.getElementById('fBTData').value = bt.map(v => v?.toFixed(1) ?? '').join(',');
    if (et.length > 1 && et !== bt)
      document.getElementById('fETData').value = et.map(v => v?.toFixed(1) ?? '').join(',');
  }

  showParseStatus(`✅ Artisan 파일 파싱 성공 — ${bt.length}개 데이터 포인트, 총 ${formatTime(timex[timex.length-1])}`, true);
}

function parseCSV(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  const header = lines[0].toLowerCase().split(',').map(h => h.trim().replace(/"/g,''));
  const rows   = lines.slice(1).map(l => l.split(',').map(v => v.trim().replace(/"/g,'')));

  const idx = k => header.indexOf(k);
  const get = (row, k) => { const i = idx(k); return i >= 0 ? row[i] : ''; };

  if (rows.length < 2) { showParseStatus('CSV 데이터가 너무 적습니다', false); return; }

  const bts = [], ets = [];
  rows.forEach(row => {
    const b = parseFloat(get(row, 'bt') || get(row, 'bean temp'));
    const e = parseFloat(get(row, 'et') || get(row, 'env temp'));
    if (!isNaN(b)) bts.push(b);
    if (!isNaN(e)) ets.push(e);
  });

  const first = rows[0];
  if (get(first, 'bean') || get(first, 'name')) document.getElementById('fBeanName').value = get(first, 'bean') || get(first, 'name');

  if (bts.length) document.getElementById('fBTData').value = bts.map(v => v.toFixed(1)).join(',');
  if (ets.length) document.getElementById('fETData').value = ets.map(v => v.toFixed(1)).join(',');

  showParseStatus(`✅ CSV 파싱 성공 — BT ${bts.length}행`, true);
}

function showParseStatus(msg, ok) {
  parseStatus.textContent = msg;
  parseStatus.className = 'rp-parse-status ' + (ok ? 'success' : 'error');
  parseStatus.style.display = '';
}

/* ── 유틸 ── */
function esc(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
