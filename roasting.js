'use strict';
/* ════════════════════════════════════════════════════════════
   로스팅 프로파일 분석 페이지
   - 사진 클릭 디지타이징 → 그래프 생성
   - DTR 계산 + 로스팅 포인트 분석
   - 원하는 다음 포인트 선택 → 피드백 (포인트 변경 가이드 + 종합 분석)
   ════════════════════════════════════════════════════════════ */

const { createClient } = supabase;
const sb = createClient(SUPABASE_URL, SUPABASE_ANON);
let currentUserId = null;

/* ── 로스팅 포인트 레퍼런스 ── */
const ROAST_POINTS = [
  { key:'라이트',        order:1, dropMin:196, dropMax:205, dtrMin:15, dtrMax:18, agtron:'75–95', desc:'밝은 산미·플로럴·과일향. 수분 제거와 건조 단계가 핵심.' },
  { key:'라이트 플러스', order:2, dropMin:204, dropMax:210, dtrMin:17, dtrMax:20, agtron:'70–80', desc:'산미를 유지하면서 단맛을 끌어올린 단계.' },
  { key:'미디엄 라이트', order:3, dropMin:208, dropMax:214, dtrMin:18, dtrMax:22, agtron:'65–75', desc:'산미와 바디의 균형. 스페셜티의 표준 영역.' },
  { key:'미디엄',        order:4, dropMin:212, dropMax:219, dtrMin:20, dtrMax:25, agtron:'55–65', desc:'단맛·바디 중심, 캐러멜·초콜릿 노트.' },
  { key:'중약배전',      order:5, dropMin:217, dropMax:225, dtrMin:22, dtrMax:27, agtron:'45–55', desc:'초콜릿·견과 강화, 산미 약화.' },
  { key:'다크',          order:6, dropMin:224, dropMax:236, dtrMin:25, dtrMax:32, agtron:'25–45', desc:'쓴맛·스모키, 2차 크랙 이후 오일 표면화.' },
];

/* ── 상태 ── */
let allProfiles = [];
let activeId = null;
let chartInstance = null;
let detailChartInstance = null;
let deleteTargetId = null;
let wizardData = null;      // 생성 중인 프로파일 데이터
let selectedTarget = null;  // 선택된 타겟 포인트(생성 화면)

/* 디지타이저 상태 */
const digi = { img:null, cal:{x1:null,x2:null,y1:null,y2:null}, events:{}, curve:[], mode:null, scale:1, images:[], dataParsed:null };

/* ── DOM ── */
const $ = id => document.getElementById(id);
const welcomeView = $('welcomeView'), wizardView = $('wizardView'), detailView = $('detailView');
const step1 = $('step1'), step2 = $('step2'), step3 = $('step3');
const profileList = $('profileList'), listEmpty = $('listEmpty'), profileCount = $('profileCount');
const searchInput = $('searchInput');
const fileDrop = $('fileDrop'), fileInput = $('fileInput'), digitizer = $('digitizer');
const canvas = $('digiCanvas'), ctx = canvas.getContext('2d');
const confirmOverlay = $('confirmOverlay');

/* ════════ 초기화 ════════ */
(async () => {
  const { data:{ session } } = await sb.auth.getSession();
  if (!session) { location.href = 'auth.html?next=roasting.html'; return; }
  currentUserId = session.user.id;
  $('btnLogout').addEventListener('click', async () => { await sb.auth.signOut(); location.href = 'auth.html'; });
  wireUI();
  await loadProfiles();
})();

/* ════════ UI 배선 ════════ */
function wireUI() {
  $('btnNewProfile').addEventListener('click', openWizard);
  $('btnWelcomeNew').addEventListener('click', openWizard);
  $('btnWizCancel1').addEventListener('click', closeWizard);
  $('btnToStep2').addEventListener('click', gotoStep2);
  $('btnBackStep1').addEventListener('click', () => showStep(1));
  $('btnBackStep2').addEventListener('click', () => showStep(2));
  $('btnGenerate').addEventListener('click', generateProfile);
  $('btnSaveProfile').addEventListener('click', saveProfile);
  searchInput.addEventListener('input', renderList);

  // 파일 업로드
  fileDrop.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', e => loadFiles(e.target.files));
  fileDrop.addEventListener('dragover', e => { e.preventDefault(); fileDrop.classList.add('drag-over'); });
  fileDrop.addEventListener('dragleave', () => fileDrop.classList.remove('drag-over'));
  fileDrop.addEventListener('drop', e => { e.preventDefault(); fileDrop.classList.remove('drag-over'); loadFiles(e.dataTransfer.files); });

  // 분석 실행 / 파일 추가 / 초기화
  $('btnAutoScan').addEventListener('click', runAnalysis);
  $('btnAddFile').addEventListener('click', () => fileInput.click());
  $('btnChangeImage').addEventListener('click', resetUpload);

  // 디지타이저 모드 버튼
  document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => armMode(btn.dataset.mode, btn));
  });
  $('btnUndoCurve').addEventListener('click', () => { digi.curve.pop(); redraw(); updateMarks(); });
  $('btnClearAll').addEventListener('click', clearDigi);
  canvas.addEventListener('click', onCanvasClick);

  // 1차 크랙 수동 입력
  $('btnFcsApply').addEventListener('click', () => {
    const raw = $('fcsManualInput').value.trim();
    const sec = parseTimeStr(raw);
    if (!sec || sec <= 0 || sec >= wizardData.total_time) {
      $('fcsManualInput').style.borderColor = 'var(--red)'; return;
    }
    $('fcsManualInput').style.borderColor = '';
    wizardData.events.fcs = sec;
    wizardData.dtr = +(((wizardData.total_time - sec) / wizardData.total_time) * 100).toFixed(1);
    wizardData.current_roast_point = analyzeCurrentPoint(wizardData.drop_temp, wizardData.dtr)?.key || wizardData.current_roast_point;
    $('fcsInputRow').style.display = 'none';
    renderMetrics($('metricsRow'), wizardData);
    // 이벤트 선 다시 그리기
    chartInstance = buildChart('roastChart', wizardData.time_series, wizardData.bt_series, wizardData.et_series||[], wizardData.agitation_series||[], wizardData.ror||[], wizardData.et_ror||[], wizardData.events, chartInstance);
    renderFeedback($('feedbackPanel'), wizardData, selectedTarget);
  });

  // 삭제
  $('btnDelete').addEventListener('click', () => { deleteTargetId = activeId; confirmOverlay.style.display = 'flex'; });
  $('btnConfirmNo').addEventListener('click', () => confirmOverlay.style.display = 'none');
  $('btnConfirmYes').addEventListener('click', deleteProfile);

  // 1차 크랙 수동 입력
  $('btnFcsApply').addEventListener('click', applyManualFcs);
}

/* ════════ Supabase CRUD ════════ */
async function loadProfiles() {
  const { data, error } = await sb.from('roasting_profiles')
    .select('*').eq('user_id', currentUserId).order('created_at', { ascending:false });
  if (error) { console.error(error); return; }
  allProfiles = data || [];
  renderList();
}

async function saveProfile() {
  if (!wizardData) return;
  const payload = {
    user_id: currentUserId,
    bean_name: wizardData.bean_name,
    seller: wizardData.seller || null,
    roaster: wizardData.roaster || null,
    ambient_temp: wizardData.ambient_temp,
    ambient_humidity: wizardData.ambient_humidity,
    roast_date: wizardData.roast_date || null,
    memo: wizardData.memo || null,
    charge_temp: wizardData.charge_temp,
    drop_temp: wizardData.drop_temp,
    total_time: wizardData.total_time,
    dtr: wizardData.dtr,
    current_roast_point: wizardData.current_roast_point,
    target_roast_point: selectedTarget,
    time_series: wizardData.time_series,
    bt_series: wizardData.bt_series,
    et_series: wizardData.et_series?.length ? wizardData.et_series : null,
    agitation_series: wizardData.agitation_series?.length ? wizardData.agitation_series : null,
    et_ror_series: wizardData.et_ror?.length ? wizardData.et_ror : null,
    et_drop_temp: wizardData.et_drop_temp ?? null,
    charge_weight: wizardData.charge_weight ?? null,
    drop_weight: wizardData.drop_weight ?? null,
    weight_loss: wizardData.weight_loss ?? null,
    events: wizardData.events,
    et_drop_temp: wizardData.et_drop_temp ?? null,
    charge_weight: wizardData.charge_weight ?? null,
    drop_weight: wizardData.drop_weight ?? null,
    weight_loss: wizardData.weight_loss ?? null,
    et_ror_series: wizardData.et_ror?.length ? wizardData.et_ror : null,
  };
  const { error } = await sb.from('roasting_profiles').insert(payload);
  if (error) { alert('저장 실패: ' + error.message); return; }
  await loadProfiles();
  closeWizard();
  if (allProfiles[0]) showDetail(allProfiles[0]);
}

async function deleteProfile() {
  confirmOverlay.style.display = 'none';
  if (!deleteTargetId) return;
  const { error } = await sb.from('roasting_profiles').delete().eq('id', deleteTargetId);
  if (error) { alert('삭제 실패: ' + error.message); return; }
  activeId = null; deleteTargetId = null;
  await loadProfiles();
  showView('welcome');
}

/* ════════ 목록 렌더 ════════ */
function renderList() {
  const q = searchInput.value.toLowerCase();
  const filtered = allProfiles.filter(p =>
    p.bean_name.toLowerCase().includes(q) || (p.seller||'').toLowerCase().includes(q));
  profileCount.textContent = filtered.length;
  profileList.innerHTML = '';
  if (!filtered.length) { profileList.appendChild(listEmpty); listEmpty.style.display=''; return; }
  filtered.forEach(p => {
    const el = document.createElement('div');
    el.className = 'rp-list-item' + (p.id===activeId ? ' active':'');
    el.innerHTML = `
      <div class="rp-list-name">${esc(p.bean_name)}</div>
      <div class="rp-list-sub">
        ${p.current_roast_point ? `<span class="rp-list-badge">${esc(p.current_roast_point)}</span>`:''}
        ${p.dtr!=null ? `<span>DTR ${(+p.dtr).toFixed(1)}%</span>`:''}
        ${p.roast_date ? `<span>${p.roast_date}</span>`:''}
      </div>`;
    el.addEventListener('click', () => showDetail(p));
    profileList.appendChild(el);
  });
}

/* ════════ 뷰 전환 ════════ */
function showView(name) {
  welcomeView.style.display = name==='welcome' ? '' : 'none';
  wizardView.style.display  = name==='wizard'  ? '' : 'none';
  detailView.style.display  = name==='detail'  ? '' : 'none';
}
function openWizard() {
  wizardData = null; selectedTarget = null; clearDigi();
  $('fBeanName').value=''; $('fSeller').value=''; $('fRoastDate').value=''; $('fRoaster').value='';
  $('fAmbientTemp').value=''; $('fAmbientHumidity').value=''; $('fMemo').value='';
  $('fChargeWeight').value=''; $('fDropWeight').value='';
  digitizer.style.display='none'; fileDrop.style.display='';
  $('aiPanel').style.display='none';
  $('fcsInputRow').style.display='none';
  digi.images = [];
  digi.dataParsed = null;
  activeId = null; renderList();
  showView('wizard'); showStep(1);
}
function closeWizard() { showView(allProfiles.length ? (activeId?'detail':'welcome') : 'welcome'); }

function showStep(n) {
  step1.style.display = n===1?'':'none';
  step2.style.display = n===2?'':'none';
  step3.style.display = n===3?'':'none';
  document.querySelectorAll('.rp-step').forEach(s => {
    const sn = +s.dataset.step;
    s.classList.toggle('active', sn===n);
    s.classList.toggle('done', sn<n);
  });
}

function gotoStep2() {
  const name = $('fBeanName').value.trim();
  if (!name) { $('fBeanName').focus(); $('fBeanName').style.borderColor='var(--red)'; return; }
  $('fBeanName').style.borderColor='';
  showStep(2);
}

/* ════════ 디지타이저 ════════ */
/* 업로드는 누적식: 사진·데이터 파일을 여러 번 나눠서 추가할 수 있다.
   (모바일은 사진앨범/파일앱을 동시에 못 고르므로 순차 추가가 필수) */
function loadFiles(files) {
  if (!files || !files.length) return;
  const arr = Array.from(files);

  const dataFile   = arr.find(f => /\.(alog|csv|json|xlsx|xls)$/i.test(f.name));
  const imageFiles = arr.filter(f => f.type.startsWith('image/'));

  const jobs = [];

  // 데이터 파일: 파싱해서 digi.dataParsed에 저장(교체)
  if (dataFile) {
    jobs.push(new Promise(res => {
      parseDataFileAsync(dataFile, (parse, err) => {
        if (err) alert('데이터 파일 파싱 실패: ' + err.message);
        else digi.dataParsed = parse;
        res();
      });
    }));
  }

  // 이미지: 기존 목록에 누적 (최대 4장)
  const room = Math.max(0, 4 - digi.images.length);
  const toAdd = imageFiles.slice(0, room);
  if (imageFiles.length > room)
    setTimeout(() => alert(`사진은 최대 4장까지입니다. ${imageFiles.length - room}장은 제외되었습니다.`), 0);
  toAdd.forEach(file => {
    jobs.push(new Promise(res => {
      const reader = new FileReader();
      reader.onload = e => {
        const dataUrl = e.target.result;
        digi.images.push({ base64: dataUrl.split(',')[1], mediaType: file.type, dataUrl });
        res();
      };
      reader.onerror = () => res();
      reader.readAsDataURL(file);
    }));
  });

  if (!jobs.length) return;

  Promise.all(jobs).then(() => {
    fileInput.value = '';   // 같은 파일 재선택 허용
    showStagePanel();
  });
}

/* 업로드 스테이징 패널 표시 (사진 썸네일 + 데이터 칩 + 액션 버튼) */
function showStagePanel() {
  fileDrop.style.display = 'none';
  digitizer.style.display = 'none';
  $('aiPanel').style.display = '';
  renderAiThumbs();
  updateAiMode();
  if (digi.images.length) loadCanvasImage(digi.images[0].dataUrl);
}

/* 수동 디지타이저 캔버스에 이미지 올리기 */
function loadCanvasImage(dataUrl) {
  const img = new Image();
  img.onload = () => {
    digi.img = img;
    const maxW = 720;
    digi.scale = Math.min(1, maxW / img.width);
    canvas.width = Math.round(img.width * digi.scale);
    canvas.height = Math.round(img.height * digi.scale);
    digi.cal = {x1:null,x2:null,y1:null,y2:null}; digi.events={}; digi.curve=[]; digi.mode=null;
    redraw(); updateMarks(); updateGenerateBtn();
  };
  img.src = dataUrl;
}

/* 업로드 전체 초기화 → 드롭 영역 복귀 */
function resetUpload() {
  digi.images = [];
  digi.dataParsed = null;
  digi.img = null;
  fileInput.value = '';
  $('aiPanel').style.display = 'none';
  digitizer.style.display = 'none';
  fileDrop.style.display = '';
}

/* 분석 실행: 사진 있으면 AI, 데이터만 있으면 즉시 그래프 생성 */
function runAnalysis() {
  if (digi.images.length) { autoScan(); return; }
  if (digi.dataParsed) { applyParsedData(digi.dataParsed); return; }
  alert('업로드된 파일이 없습니다.');
}

/* 업로드 상태에 맞춰 기본 버튼 라벨·안내 갱신 */
function updateAiMode() {
  const btn = $('btnAutoScan');
  const hasImg = digi.images.length > 0;
  const hasData = !!digi.dataParsed;
  if (btn) {
    btn.textContent = hasImg
      ? (hasData ? '🤖 AI 통합 분석 (사진＋데이터)' : '🤖 AI 자동 분석')
      : '📊 데이터로 그래프 생성';
  }
  setAiStatus('idle');
}

function renderAiThumbs() {
  const container = $('aiThumbs');
  container.innerHTML = '';
  digi.images.forEach((img, i) => {
    const el = document.createElement('img');
    el.className = 'rp-ai-thumb';
    el.src = img.dataUrl;
    el.alt = `사진 ${i+1}`;
    container.appendChild(el);
  });
  if (digi.dataParsed) {
    const chip = document.createElement('div');
    chip.className = 'rp-ai-datachip';
    chip.innerHTML = `📄 <strong>${esc(digi.dataParsed.title || '데이터 파일')}</strong><span>온도·시간 기준</span>`;
    container.appendChild(chip);
  }
}

/* ════════ 데이터 파일 파싱 (.alog / .csv / .json / .xlsx) ════════ */
function parseDataFileAsync(file, cb) {
  const isXlsx = /\.(xlsx|xls)$/i.test(file.name);
  const reader = new FileReader();
  reader.onload = e => {
    try {
      let parse;
      if (isXlsx) parse = parseXlsxProfile(e.target.result, file.name);
      else if (/\.(alog|json)$/i.test(file.name)) parse = parseArtisanAlog(e.target.result, file.name);
      else parse = parseCsvProfile(e.target.result, file.name);
      cb(parse, null);
    } catch (err) {
      cb(null, err);
    }
  };
  reader.onerror = () => cb(null, new Error('파일을 읽지 못했습니다.'));
  if (isXlsx) reader.readAsArrayBuffer(file);
  else reader.readAsText(file, 'utf-8');
}

function parseArtisanAlog(text, filename) {
  // Artisan .alog는 표준 JSON이거나 Python 스타일(단따옴표, None, True/False)일 수 있음
  let d;
  try {
    d = JSON.parse(text);
  } catch {
    const cleaned = text
      .replace(/'/g, '"')
      .replace(/\bNone\b/g, 'null')
      .replace(/\bTrue\b/g, 'true')
      .replace(/\bFalse\b/g, 'false');
    d = JSON.parse(cleaned);
  }

  const timex = (d.timex || []).map(Number);
  // Artisan 기본: temp1=ET, temp2=BT
  const rawBt = (d.temp2 || d.BT || []).map(Number);
  const rawEt = (d.temp1 || d.ET || []).map(Number);

  if (timex.length < 2 || rawBt.length < 2) throw new Error('BT 데이터를 찾지 못했습니다.');

  const btPts = timex.map((t, i) => ({ t, bt: rawBt[i] })).filter(p => !isNaN(p.bt) && p.bt > 10);
  const etPts = rawEt.length
    ? timex.map((t, i) => ({ t, bt: rawEt[i] })).filter(p => !isNaN(p.bt) && p.bt > 10)
    : [];

  const dropT = btPts[btPts.length - 1].t;
  const evTimes = { charge: 0, drop: dropT };

  // TP
  if (d.TP_idx != null && timex[d.TP_idx] != null) evTimes.tp = timex[d.TP_idx];

  // specialevents 배열로 이벤트 추출
  const evIdxs = d.specialevents || [];
  const evStrs = d.specialeventsStrings || [];
  evIdxs.forEach((idx, i) => {
    const label = (evStrs[i] || '').toUpperCase().replace(/\s+/g, '');
    const t = timex[idx];
    if (t == null) return;
    if (label.includes('DRYE') || label.includes('DRYEND')) evTimes.dry = t;
    else if (label === 'FCS' || label.includes('FCSTART') || label.includes('FIRSTCRACKSTART')) evTimes.fcs = t;
    else if (label === 'FCE' || label.includes('FCEND') || label.includes('FIRSTCRACKEND')) evTimes.fce = t;
    else if (label === 'DROP' || label.includes('SCO')) evTimes.drop = t;
    else if (label === 'TP' || label.includes('TURNING')) evTimes.tp = t;
  });

  // 직접 시간값 필드 (일부 버전)
  ['DRYe','FCs','FCe'].forEach(k => {
    if (d[k] != null && d[k] > 0) {
      const map = { DRYe:'dry', FCs:'fcs', FCe:'fce' };
      evTimes[map[k]] = +d[k];
    }
  });

  return {
    btPts, etPts, evTimes,
    dropT: evTimes.drop,
    title: d.title || d.name || filename.replace(/\.[^.]+$/, ''),
    ambient_temp: d.ambient != null ? +d.ambient : null,
    ambient_humidity: d.humidity != null ? +d.humidity : null,
  };
}

function parseCsvProfile(text, filename) {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (lines.length < 2) throw new Error('CSV 데이터가 너무 짧습니다.');
  // 구분자 자동 감지: 헤더(문자 포함) 행에서 가장 많은 컬럼을 만드는 문자
  const probe = lines.find(l => /[a-z가-힣]/i.test(l)) || lines[0];
  let sep = ',', best = 0;
  [',', ';', '\t'].forEach(c => { const n = probe.split(c).length; if (n > best) { best = n; sep = c; } });
  const rows = lines.map(l => l.split(sep));
  return parseRows(rows, filename);
}

function parseXlsxProfile(arrayBuffer, filename) {
  if (typeof XLSX === 'undefined') throw new Error('엑셀 파서를 불러오지 못했습니다. 새로고침 후 다시 시도하세요.');
  const wb = XLSX.read(new Uint8Array(arrayBuffer), { type: 'array' });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  if (!sheet) throw new Error('엑셀에 시트가 없습니다.');
  const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: '' });
  return parseRows(rows, filename);
}

/* 행 배열(셀 배열의 배열) → 프로파일 파싱. CSV·엑셀 공용 */
function parseRows(rows, filename) {
  rows = (rows || []).filter(r => r && r.some(c => String(c).trim() !== ''));
  if (rows.length < 3) throw new Error('데이터 행이 너무 적습니다.');

  // 헤더 행: 문자(영문/한글)가 포함된 첫 행
  let hdr = 0;
  for (let i = 0; i < Math.min(6, rows.length); i++) {
    if (rows[i].some(c => /[a-z가-힣]/i.test(String(c)))) { hdr = i; break; }
  }
  const cols = rows[hdr].map(c => String(c).trim().replace(/^"|"$/g, '').toLowerCase());

  // 온도 컬럼은 RoR·히터·비율 컬럼과 혼동되면 안 됨 → 제외 패턴
  const isRate = c => /ror|rate|히터|heater|비율|출력|파워|power|%/.test(c);
  const findCol = (...patterns) => cols.findIndex(c => patterns.some(p => p.test(c)));
  const findTemp = (...patterns) => cols.findIndex(c => !isRate(c) && patterns.some(p => p.test(c)));

  const tIdx   = findCol(/^(time|t|seconds?|sec|zeit|시간|시각)$/, /time.*sec/, /^hh:mm:ss/, /경과|시간|시각/);
  // BT = 원두 표면(bean surface) — 로스팅 레벨을 결정하는 온도
  const btIdx  = findTemp(/^(bt|bean.?temp|temp2|beansurface|bohnentemp)$/, /^bean/, /temp.*2/, /원두.?표면|원두|표면/);
  // ET = 내부/드럼 환경 온도
  const etIdx  = findTemp(/^(et|env.?temp|temp1|drum|internal|trommeltemp)$/, /temp.*1/, /내부/, /드럼.?표면|드럼/);
  const agitIdx = findCol(/^(agit|agitation|교반|stir)$/, /교반/);
  const noteIdx = findCol(/^(비고|remark|note|event|이벤트|메모|comment)$/, /비고|remark|event|이벤트/);
  const fcsIdx  = findCol(/^(fc.?start|first.?crack.?s|fcs|1차.?크랙.?시작)$/);
  const dropIdx = findCol(/^(drop|sco|ende|배출)$/);

  if (tIdx === -1) throw new Error(`시간(Time) 컬럼을 찾지 못했습니다. (헤더: ${cols.join(', ')})`);
  if (btIdx === -1) throw new Error(`BT(원두표면) 컬럼을 찾지 못했습니다. (헤더: ${cols.join(', ')})`);

  const parseTime = raw => {
    const s = String(raw).replace(/\s+/g, '');  // "00 : 00" → "00:00"
    if (s.includes(':')) return s.split(':').reverse().reduce((acc, v, j) => acc + (+v) * Math.pow(60, j), 0);
    return parseFloat(s);
  };

  // 비고(remark) 텍스트에서 이벤트 시각 추출
  const noteEvent = (txt, t) => {
    const s = String(txt).toLowerCase().replace(/\s+/g, '');
    if (/(t\.?p|turning|터닝|터닝포인트)/.test(s)) evTimes.tp = t;
    else if (/(1st|firstcrack|fc(s|start)?|1차|1차크랙)/.test(s)) { if (evTimes.fcs == null) evTimes.fcs = t; }
    else if (/(2nd|secondcrack|sc(e|start)?|2차|2차크랙)/.test(s)) { if (evTimes.fce == null) evTimes.fce = t; }
    else if (/(dryend|dry|건조)/.test(s)) evTimes.dry = t;
    else if (/(drop|배출|out|discharge)/.test(s)) evTimes.drop = t;
  };

  const btPts = [], etPts = [], agitPts = [];
  const evTimes = { charge: 0 };

  for (let i = hdr + 1; i < rows.length; i++) {
    const vals = rows[i].map(v => String(v).trim().replace(/^"|"$/g, ''));
    const t = parseTime(vals[tIdx] || '');
    const bt = parseFloat(vals[btIdx]);
    if (isNaN(t) || isNaN(bt) || bt <= 0) continue;
    btPts.push({ t, bt });
    if (etIdx !== -1) {
      const et = parseFloat(vals[etIdx]);
      if (!isNaN(et) && et > 0) etPts.push({ t, bt: et });
    }
    if (agitIdx !== -1) {
      const ag = parseFloat(vals[agitIdx]);
      if (!isNaN(ag)) agitPts.push({ t, v: ag });
    }
    if (noteIdx !== -1 && vals[noteIdx]) noteEvent(vals[noteIdx], t);
    if (fcsIdx !== -1 && vals[fcsIdx] && parseFloat(vals[fcsIdx]) > 0 && evTimes.fcs == null) evTimes.fcs = t;
    if (dropIdx !== -1 && vals[dropIdx] && parseFloat(vals[dropIdx]) > 0) evTimes.drop = t;
  }

  if (btPts.length < 2) throw new Error('유효한 BT 포인트가 부족합니다.');
  if (!evTimes.drop) evTimes.drop = btPts[btPts.length - 1].t;

  // 교반 컬럼이 있으면 변화 지점만 step 포인트로 압축
  let agitSorted = null;
  if (agitPts.length) {
    agitSorted = [];
    agitPts.forEach(p => {
      if (!agitSorted.length || agitSorted[agitSorted.length - 1].v !== p.v) agitSorted.push(p);
    });
  }

  return {
    btPts, etPts, evTimes, dropT: evTimes.drop, agitSorted,
    title: filename.replace(/\.[^.]+$/, ''), ambient_temp: null, ambient_humidity: null,
  };
}

/* 파싱 결과(btPts/etPts/evTimes/dropT)로 wizardData 객체 생성.
   extra.agitSorted: 교반 step 포인트([{t,v}]) — AI 또는 데이터파일 출처
   extra.chargeTemp/dropTemp: 명시 온도(없으면 BT 곡선에서 보간) */
function buildWizardFromParse(parse, extra) {
  extra = extra || {};
  const { btPts, etPts, evTimes, dropT } = parse;

  const series = resample(btPts, 5, dropT);
  const times = series.map(s => s.t);
  const bts   = series.map(s => s.bt);
  const ror   = computeRoR(times, bts, 30);

  const ets   = etPts.length >= 2 ? resample(etPts, 5, dropT).map(s => s.bt) : [];
  const etRor = etPts.length >= 2 ? computeRoR(times, ets, 30) : [];
  const etDropTemp = etPts.length >= 2 ? +interp(etPts, dropT).toFixed(1) : null;

  // 교반: AI 보강값 우선, 없으면 데이터파일 교반 컬럼
  const agitSrc = (extra.agitSorted && extra.agitSorted.length) ? extra.agitSorted
    : (parse.agitSorted && parse.agitSorted.length ? parse.agitSorted : null);
  const agits = agitSrc ? resampleStep(agitSrc, 5, dropT) : [];

  const chargeWeight = numOrNull('fChargeWeight');
  const dropWeight   = numOrNull('fDropWeight');
  const weightLoss   = (chargeWeight && dropWeight && chargeWeight > 0)
    ? +(((chargeWeight - dropWeight) / chargeWeight) * 100).toFixed(1) : null;

  // 투입온도: 투입 시점엔 원두(BT)가 차갑고 환경(ET/드럼)이 뜨겁다.
  // 로스터가 말하는 '투입온도'는 예열된 드럼/환경 온도이므로 BT·ET 중 높은 값 사용.
  let chargeTemp;
  if (extra.chargeTemp != null) {
    chargeTemp = extra.chargeTemp;
  } else {
    const btCharge = interp(btPts, 0);
    const etCharge = etPts.length >= 2 ? interp(etPts, 0) : null;
    chargeTemp = +(etCharge != null ? Math.max(btCharge, etCharge) : btCharge).toFixed(1);
  }
  const dropTemp   = extra.dropTemp   != null ? extra.dropTemp   : +interp(btPts, dropT).toFixed(1);
  const dtr = evTimes.fcs != null ? +(((dropT - evTimes.fcs) / dropT) * 100).toFixed(1) : null;
  const current = analyzeCurrentPoint(dropTemp, dtr);

  return {
    bean_name:        $('fBeanName').value.trim() || parse.title || '',
    seller:           $('fSeller').value.trim(),
    roaster:          $('fRoaster').value.trim() || null,
    roast_date:       $('fRoastDate').value,
    ambient_temp:     numOrNull('fAmbientTemp') != null ? numOrNull('fAmbientTemp') : (parse.ambient_temp != null ? parse.ambient_temp : null),
    ambient_humidity: numOrNull('fAmbientHumidity') != null ? numOrNull('fAmbientHumidity') : (parse.ambient_humidity != null ? parse.ambient_humidity : null),
    memo:             $('fMemo').value.trim(),
    charge_temp: chargeTemp, drop_temp: dropTemp, total_time: dropT, dtr,
    current_roast_point: current ? current.key : null,
    time_series: times, bt_series: bts, et_series: ets, agitation_series: agits, ror, et_ror: etRor,
    et_drop_temp: etDropTemp, charge_weight: chargeWeight, drop_weight: dropWeight, weight_loss: weightLoss,
    events: evTimes,
  };
}

/* wizardData → STEP 3 화면 렌더 (지표·차트·타겟·피드백) */
function showWizardResult() {
  renderMetrics($('metricsRow'), wizardData);
  chartInstance = buildChart('roastChart',
    wizardData.time_series, wizardData.bt_series, wizardData.et_series || [],
    wizardData.agitation_series || [], wizardData.ror || [], wizardData.et_ror || [],
    wizardData.events, chartInstance);
  $('chartTitle').textContent = wizardData.bean_name;
  selectedTarget = null;
  const renderTargets = () => renderTargetButtons($('targetBtns'), wizardData, key => {
    selectedTarget = key; renderTargets();
    renderFeedback($('feedbackPanel'), wizardData, key);
  }, selectedTarget);
  renderTargets();
  renderFeedback($('feedbackPanel'), wizardData, null);
  $('fcsInputRow').style.display = wizardData.events.fcs == null ? '' : 'none';
  showStep(3);
}

/* 데이터 파일 단독 업로드 → 바로 결과 */
function applyParsedData(parse) {
  wizardData = buildWizardFromParse(parse);
  if (!$('fBeanName').value.trim() && parse.title) $('fBeanName').value = parse.title;
  fileDrop.style.display = 'none';
  $('aiPanel').style.display = 'none';
  digitizer.style.display = 'none';
  showWizardResult();
}

/* ════════ AI 자동 분석 ════════ */
function setAiStatus(state, msg) {
  const el = $('aiStatus');
  if (state === 'idle') {
    const hasImg = digi.images.length > 0;
    const hasData = !!digi.dataParsed;
    let msg;
    if (hasImg && hasData)
      msg = '📄 데이터 파일의 정확한 <strong>온도·시간</strong> 위에, 사진에서 읽은 <strong>교반·이벤트</strong>를 보강해 통합합니다.';
    else if (hasImg)
      msg = 'AI가 BT·ET 곡선·교반·이벤트 마커를 자동으로 읽어 그래프를 생성합니다. 정확도를 높이려면 <strong>➕ 파일 추가</strong>로 엑셀·CSV도 함께 올려보세요.';
    else if (hasData)
      msg = '📄 데이터 파일이 준비됐습니다. <strong>➕ 파일 추가</strong>로 사진을 올리면 교반·이벤트까지 통합할 수 있습니다.';
    else
      msg = '파일을 업로드하세요.';
    el.innerHTML = `<span class="rp-ai-msg">${msg}</span>`;
  } else if (state === 'loading') {
    el.innerHTML = '<span class="rp-ai-spinner"></span><span class="rp-ai-msg">AI가 프로파일을 분석 중입니다… (10~20초)</span>';
  } else if (state === 'error') {
    el.innerHTML = `<span class="rp-ai-err">❌ ${esc(msg || '분석 실패')}</span><span class="rp-ai-msg"> — 아래 수동 디지타이징을 이용하세요.</span>`;
  } else if (state === 'ok') {
    el.innerHTML = `<span class="rp-ai-ok">✅ ${esc(msg || '분석 완료')}</span>`;
  }
}

async function autoScan() {
  if (!digi.images.length) { alert('이미지를 먼저 업로드해 주세요.'); return; }
  $('btnAutoScan').disabled = true;
  setAiStatus('loading');
  digitizer.style.display = 'none';

  try {
    const { data, error } = await sb.functions.invoke('analyze-roast', {
      body: {
        images: digi.images.map(img => ({ base64: img.base64, media_type: img.mediaType })),
      }
    });

    if (error) {
      // edge function not deployed → FunctionsHttpError or FunctionsRelayError
      const msg = error.message || String(error);
      if (msg.includes('Failed to fetch') || msg.includes('relay') || msg.includes('404') || msg.includes('not found')) {
        throw new Error('Edge Function이 아직 배포되지 않았습니다. Supabase 대시보드에서 배포해 주세요.');
      }
      throw new Error(msg);
    }
    if (data?.error) throw new Error(data.error);

    const result = data;

    // AI 결과 → wizardData 구성
    // labeled_points: 새 포맷 { time_sec, temp_celsius, curve } 또는 구 배열 포맷 모두 허용
    const labeled = (result.labeled_points || [])
      .filter(p => (p.curve === 'BT' || Array.isArray(p)))  // BT 레이블만 BT 곡선에 반영
      .map(p => Array.isArray(p) ? { t: +p[0], bt: +p[1] } : { t: +p.time_sec, bt: +p.temp_celsius });
    const labeledEt = (result.labeled_points || [])
      .filter(p => !Array.isArray(p) && p.curve === 'ET')
      .map(p => ({ t: +p.time_sec, bt: +p.temp_celsius }));
    const rawCurve = (result.bt_curve || []).map(([t, bt]) => ({ t: +t, bt: +bt }));
    const rawEt    = (result.et_curve   || []).map(([t, bt]) => ({ t: +t, bt: +bt }));
    const rawAgit  = (result.agitation  || []).map(([t, v])  => ({ t: +t, v: +v  }));

    // BT: labeled BT points + bt_curve 합쳐 중복 제거
    const mergedBt = [...labeled, ...rawCurve].sort((a, b) => a.t - b.t);
    const curve = [];
    for (const p of mergedBt) {
      if (!curve.length || Math.abs(p.t - curve[curve.length - 1].t) > 0.4) curve.push(p);
    }

    // ET: labeled ET points + et_curve 합쳐 중복 제거
    const mergedEt = [...labeledEt, ...rawEt].sort((a, b) => a.t - b.t);
    const etCurve = [];
    for (const p of mergedEt) {
      if (!etCurve.length || Math.abs(p.t - etCurve[etCurve.length - 1].t) > 0.4) etCurve.push(p);
    }

    const hasData = !!digi.dataParsed;
    if (curve.length < 2 && !hasData) throw new Error('BT 곡선 데이터를 추출하지 못했습니다. 이미지를 더 선명하게 캡처해 보세요.');

    const evRaw = result.events || {};
    const dropT = typeof evRaw.drop === 'number' ? +evRaw.drop
      : result.total_time_sec ? +result.total_time_sec
      : (curve.length ? curve[curve.length - 1].t : 0);
    if (dropT <= 0 && !hasData) throw new Error('배출 시간을 읽지 못했습니다.');

    const evTimes = {};
    ['charge','tp','dry','fcs','fce','drop'].forEach(k => {
      if (evRaw[k] != null) evTimes[k] = +evRaw[k];
    });
    evTimes.charge = 0;

    // 교반: AI step 포인트
    const agitSorted = rawAgit.sort((a, b) => a.t - b.t);

    if (hasData) {
      // ── 통합: 데이터 파일(온도·시간) 권위 + 사진(교반·누락 이벤트) 보강 ──
      const dp = digi.dataParsed;
      const mergedEvents = Object.assign({}, dp.evTimes);
      // 데이터에 없는 이벤트만 AI 값으로 채움 (범위 검증)
      ['tp','dry','fcs','fce'].forEach(k => {
        if (mergedEvents[k] == null && evTimes[k] != null && evTimes[k] > 0 && evTimes[k] < dp.dropT)
          mergedEvents[k] = evTimes[k];
      });
      const mergedParse = Object.assign({}, dp, { evTimes: mergedEvents });
      // 교반: 사진 추출값 우선, 없으면 데이터파일 교반 컬럼(buildWizardFromParse가 처리)
      wizardData = buildWizardFromParse(mergedParse, agitSorted.length ? { agitSorted } : {});

      const conf = result.confidence || 'medium';
      const confTxt = conf === 'high' ? '높음 🟢' : conf === 'medium' ? '보통 🟡' : '낮음 🔴';
      const agitNote = wizardData.agitation_series && wizardData.agitation_series.length ? '교반✓' : '교반 없음';
      setAiStatus('ok', `통합 완료 · 온도/시간=데이터파일, 교반/이벤트=사진(${confTxt}, ${agitNote})`);
    } else {
      // ── 사진 단독 ──
      const chargeTemp = result.charge_temp != null ? +result.charge_temp : +interp(curve, 0).toFixed(1);
      const dropTemp   = result.drop_temp   != null ? +result.drop_temp   : +interp(curve, dropT).toFixed(1);
      wizardData = buildWizardFromParse(
        { btPts: curve, etPts: etCurve, evTimes, dropT, title: '', ambient_temp: null, ambient_humidity: null },
        { agitSorted, chargeTemp, dropTemp }
      );

      const conf = result.confidence || 'medium';
      const confTxt = conf === 'high' ? '높음 🟢' : conf === 'medium' ? '보통 🟡' : '낮음 🔴';
      const notes = result.notes ? ` · ${result.notes}` : '';
      setAiStatus('ok', `분석 완료 (신뢰도: ${confTxt}${notes})`);
    }

    showWizardResult();

  } catch (err) {
    console.error('AI scan error:', err);
    setAiStatus('error', err.message);
    digitizer.style.display = '';
  } finally {
    $('btnAutoScan').disabled = false;
  }
}

/* ════════ 1차 크랙 수동 입력 ════════ */
function applyManualFcs() {
  if (!wizardData) return;
  const raw = $('fcsManualInput').value.trim();
  const sec = parseTimeStr(raw);
  if (!sec || sec <= 0 || sec >= wizardData.total_time) {
    $('fcsManualInput').style.borderColor = 'var(--red)'; return;
  }
  $('fcsManualInput').style.borderColor = '';
  wizardData.events.fcs = sec;
  wizardData.dtr = +(((wizardData.total_time - sec) / wizardData.total_time) * 100).toFixed(1);
  const pt = analyzeCurrentPoint(wizardData.drop_temp, wizardData.dtr);
  if (pt) wizardData.current_roast_point = pt.key;
  $('fcsInputRow').style.display = 'none';
  renderMetrics($('metricsRow'), wizardData);
  chartInstance = buildChart('roastChart',
    wizardData.time_series, wizardData.bt_series, wizardData.et_series||[],
    wizardData.agitation_series||[], wizardData.ror||[], wizardData.et_ror||[],
    wizardData.events, chartInstance);
  const renderTargets = () => renderTargetButtons($('targetBtns'), wizardData, (key) => {
    selectedTarget = key; renderTargets();
    renderFeedback($('feedbackPanel'), wizardData, key);
  }, selectedTarget);
  renderTargets();
  renderFeedback($('feedbackPanel'), wizardData, selectedTarget);
}

function armMode(mode, btn) {
  digi.mode = (digi.mode===mode) ? null : mode;
  document.querySelectorAll('.rp-cal-btn,.rp-event-btn').forEach(b => b.classList.remove('armed'));
  if (digi.mode && btn) btn.classList.add('armed');
  $('digiHelp').innerHTML = digi.mode
    ? `<strong>${modeLabel(digi.mode)}</strong> 모드: 그래프 위 해당 지점을 클릭하세요.`
    : '먼저 <strong>축 보정</strong>을 한 뒤, 곡선 위 <strong>이벤트 포인트</strong>를 찍어주세요.';
}

function modeLabel(m) {
  return { 'cal-x1':'시간축 점1','cal-x2':'시간축 점2','cal-y1':'온도축 점1','cal-y2':'온도축 점2',
    'ev-charge':'투입','ev-tp':'터닝포인트','ev-dry':'건조종료','ev-fcs':'1차크랙 시작',
    'ev-fce':'1차크랙 종료','ev-drop':'배출','curve':'곡선점 추가' }[m] || m;
}

function onCanvasClick(e) {
  if (!digi.img || !digi.mode) return;
  const rect = canvas.getBoundingClientRect();
  const px = (e.clientX - rect.left) * (canvas.width / rect.width);
  const py = (e.clientY - rect.top) * (canvas.height / rect.height);
  const m = digi.mode;
  if (m.startsWith('cal-')) digi.cal[m.slice(4)] = {px,py};
  else if (m==='curve') digi.curve.push({px,py});
  else if (m.startsWith('ev-')) digi.events[m.slice(3)] = {px,py};
  redraw(); updateMarks(); updateGenerateBtn();
}

function clearDigi() {
  digi.cal={x1:null,x2:null,y1:null,y2:null}; digi.events={}; digi.curve=[]; digi.mode=null;
  document.querySelectorAll('.rp-cal-btn,.rp-event-btn').forEach(b=>b.classList.remove('armed'));
  if (digi.img) { redraw(); updateMarks(); updateGenerateBtn(); }
}

function redraw() {
  if (!digi.img) return;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(digi.img, 0,0, canvas.width, canvas.height);
  // 보정점 (청록 십자)
  const calColors = {x1:'#06b6d4',x2:'#06b6d4',y1:'#a855f7',y2:'#a855f7'};
  for (const k in digi.cal) if (digi.cal[k]) drawCross(digi.cal[k], calColors[k], k.toUpperCase());
  // 곡선점
  digi.curve.forEach(p => drawDot(p, '#0ea5e9', 3));
  // 이벤트
  const evC = {charge:'#6366f1',tp:'#8b5cf6',dry:'#f59e0b',fcs:'#ef4444',fce:'#f97316',drop:'#16a34a'};
  const evL = {charge:'CH',tp:'TP',dry:'DRY',fcs:'FC',fce:'FCe',drop:'DROP'};
  for (const k in digi.events) drawDot(digi.events[k], evC[k], 6, evL[k]);
}
function drawCross(p,color,label){ ctx.strokeStyle=color; ctx.lineWidth=1.5; ctx.beginPath();
  ctx.moveTo(p.px-8,p.py); ctx.lineTo(p.px+8,p.py); ctx.moveTo(p.px,p.py-8); ctx.lineTo(p.px,p.py+8); ctx.stroke();
  ctx.fillStyle=color; ctx.font='bold 11px sans-serif'; ctx.fillText(label,p.px+9,p.py-4); }
function drawDot(p,color,r,label){ ctx.fillStyle=color; ctx.beginPath(); ctx.arc(p.px,p.py,r,0,7); ctx.fill();
  ctx.strokeStyle='#fff'; ctx.lineWidth=1.5; ctx.stroke();
  if(label){ ctx.fillStyle=color; ctx.font='bold 11px sans-serif'; ctx.fillText(label,p.px+8,p.py-6); } }

function updateMarks() {
  const setDot=(id,on)=>{ const el=$(id); if(el){el.textContent=on?'●':'○'; el.classList.toggle('set',on);} };
  setDot('calX1Dot',!!digi.cal.x1); setDot('calX2Dot',!!digi.cal.x2);
  setDot('calY1Dot',!!digi.cal.y1); setDot('calY2Dot',!!digi.cal.y2);
  const mk=(id,on)=>{ const el=$(id); if(el) el.textContent = on?'✓':''; };
  mk('mk-charge',!!digi.events.charge); mk('mk-tp',!!digi.events.tp); mk('mk-dry',!!digi.events.dry);
  mk('mk-fcs',!!digi.events.fcs); mk('mk-fce',!!digi.events.fce); mk('mk-drop',!!digi.events.drop);
  $('mk-curve').textContent = digi.curve.length ? `${digi.curve.length}점` : '';
}

function calReady() {
  return digi.cal.x1 && digi.cal.x2 && digi.cal.y1 && digi.cal.y2 &&
    $('calX1Val').value && $('calX2Val').value && $('calY1Val').value && $('calY2Val').value;
}
function updateGenerateBtn() {
  // 최소: 보정 4점+값, 투입, 배출
  const ok = calReady() && digi.events.charge && digi.events.drop;
  $('btnGenerate').disabled = !ok;
}
['calX1Val','calX2Val','calY1Val','calY2Val'].forEach(id =>
  document.addEventListener('input', e => { if(e.target.id===id) updateGenerateBtn(); }));

/* ════════ 좌표 변환 & 그래프 생성 ════════ */
function pxToTime(px){ const {x1,x2}=digi.cal; const v1=parseTimeStr($('calX1Val').value), v2=parseTimeStr($('calX2Val').value);
  return v1 + (px - x1.px) * (v2 - v1) / (x2.px - x1.px); }
function pyToTemp(py){ const {y1,y2}=digi.cal; const v1=parseFloat($('calY1Val').value), v2=parseFloat($('calY2Val').value);
  return v1 + (py - y1.py) * (v2 - v1) / (y2.py - y1.py); }

function parseTimeStr(s){ s=String(s).trim(); if(s.includes(':')){ const [m,sec]=s.split(':').map(Number); return (m||0)*60+(sec||0);} return parseFloat(s)||0; }

function generateProfile() {
  if (!calReady() || !digi.events.charge || !digi.events.drop) return;

  // 1) 모든 점을 (시간,온도)로 변환
  const raw = [];
  for (const k in digi.events) raw.push({ t: pxToTime(digi.events[k].px), bt: pyToTemp(digi.events[k].py), ev:k });
  digi.curve.forEach(p => raw.push({ t: pxToTime(p.px), bt: pyToTemp(p.py) }));

  // 2) 투입 기준 0초로 정렬
  const chargeT = pxToTime(digi.events.charge.px);
  raw.forEach(p => p.t -= chargeT);
  raw.sort((a,b) => a.t - b.t);

  // 이벤트 시간(초) 추출
  const evTimes = {};
  for (const k in digi.events) evTimes[k] = +(pxToTime(digi.events[k].px) - chargeT).toFixed(1);
  evTimes.charge = 0;

  const dropT = evTimes.drop;
  if (dropT <= 0) { alert('배출 시간이 투입보다 빠릅니다. 보정값을 확인하세요.'); return; }

  // 3) 곡선 점들만으로 BT 시계열 구성 (시간순, 중복 제거)
  const curvePts = raw.filter(p => p.t >= -1 && p.t <= dropT + 1);
  const dedup = [];
  curvePts.forEach(p => { if (!dedup.length || Math.abs(p.t - dedup[dedup.length-1].t) > 0.5) dedup.push(p); });
  if (dedup.length < 2) { alert('점이 부족합니다. 곡선점을 더 추가해 주세요.'); return; }

  // 4) 5초 간격 리샘플 + ROR
  const series = resample(dedup, 5, dropT);
  const times = series.map(s=>s.t), bts = series.map(s=>s.bt);
  const ror = computeRoR(times, bts, 30);

  // 5) 지표
  const chargeTemp = +interp(dedup, 0).toFixed(1);
  const dropTemp = +interp(dedup, dropT).toFixed(1);
  const dtr = (evTimes.fcs!=null) ? +(((dropT - evTimes.fcs) / dropT) * 100).toFixed(1) : null;
  const current = analyzeCurrentPoint(dropTemp, dtr);

  const chargeWeight = numOrNull('fChargeWeight');
  const dropWeight = numOrNull('fDropWeight');
  const weightLoss = (chargeWeight && dropWeight && chargeWeight > 0)
    ? +(((chargeWeight - dropWeight) / chargeWeight) * 100).toFixed(1) : null;

  wizardData = {
    bean_name: $('fBeanName').value.trim(),
    seller: $('fSeller').value.trim(),
    roast_date: $('fRoastDate').value,
    ambient_temp: numOrNull('fAmbientTemp'),
    ambient_humidity: numOrNull('fAmbientHumidity'),
    memo: $('fMemo').value.trim(),
    charge_temp: chargeTemp, drop_temp: dropTemp, total_time: dropT, dtr,
    current_roast_point: current ? current.key : null,
    time_series: times, bt_series: bts, ror, et_ror: [], et_drop_temp: null,
    charge_weight: chargeWeight, drop_weight: dropWeight, weight_loss: weightLoss,
    events: evTimes,
  };

  // 6) STEP 3 렌더
  renderMetrics($('metricsRow'), wizardData);
  chartInstance = buildChart('roastChart', times, bts, [], [], ror, [], evTimes, chartInstance);
  $('chartTitle').textContent = wizardData.bean_name;
  selectedTarget = null;
  const renderTargets = () => renderTargetButtons($('targetBtns'), wizardData, (key) => {
    selectedTarget = key;
    renderTargets();
    renderFeedback($('feedbackPanel'), wizardData, key);
  }, selectedTarget);
  renderTargets();
  renderFeedback($('feedbackPanel'), wizardData, null);
  // fcs 없으면 수동 입력 행 표시
  $('fcsInputRow').style.display = wizardData.events.fcs == null ? '' : 'none';
  showStep(3);
}

function numOrNull(id){ const v=parseFloat($(id).value); return isNaN(v)?null:v; }

/* 리샘플: dedup [{t,bt}] (정렬됨) → step초 간격 0~endT */
function resample(pts, step, endT) {
  const out=[];
  for (let t=0; t<=endT+0.001; t+=step) out.push({ t:+t.toFixed(1), bt:+interp(pts,t).toFixed(1) });
  return out;
}
function interp(pts, t) {
  if (t<=pts[0].t) return pts[0].bt;
  if (t>=pts[pts.length-1].t) return pts[pts.length-1].bt;
  for (let i=0;i<pts.length-1;i++){ const a=pts[i],b=pts[i+1];
    if (t>=a.t && t<=b.t) return b.t===a.t ? a.bt : a.bt+(b.bt-a.bt)*(t-a.t)/(b.t-a.t); }
  return pts[pts.length-1].bt;
}
/* step 함수 리샘플: [{t,v}] → 5초 간격 값 배열 (계단 유지) */
function resampleStep(pts, step, endT) {
  const out = [];
  for (let t = 0; t <= endT + 0.001; t += step) {
    let val = pts[0].v;
    for (let i = 0; i < pts.length; i++) {
      if (pts[i].t <= t) val = pts[i].v; else break;
    }
    out.push(+val.toFixed(1));
  }
  return out;
}

function computeRoR(times, bts, span=30) {
  return times.map((t,i)=>{ if(i===0) return null;
    let k=i; while(k>0 && t-times[k] < span) k--;
    const dt=t-times[k]; if(dt<=0) return null;
    return +(((bts[i]-bts[k])/dt)*60).toFixed(2); });
}

/* ════════ 로스팅 포인트 분석 ════════ */
function analyzeCurrentPoint(dropTemp, dtr) {
  if (dropTemp!=null) {
    for (const p of ROAST_POINTS) if (dropTemp>=p.dropMin && dropTemp<=p.dropMax) return p;
    let best=null, bd=1e9;
    for (const p of ROAST_POINTS){ const mid=(p.dropMin+p.dropMax)/2, d=Math.abs(dropTemp-mid); if(d<bd){bd=d;best=p;} }
    return best;
  }
  if (dtr!=null) for (const p of ROAST_POINTS) if (dtr>=p.dtrMin && dtr<=p.dtrMax) return p;
  return null;
}

/* ════════ 지표 렌더 ════════ */
function renderMetrics(el, d) {
  const cards = [
    { label:'총 시간', value: fmtTime(d.total_time), unit:'',
      cls: d.total_time<420?'warn':d.total_time>1200?'warn':'good' },
    { label:'DTR', value: d.dtr!=null? d.dtr.toFixed(1):'—', unit:'%',
      cls: d.dtr==null?'':d.dtr<15?'bad':d.dtr>30?'warn':'good' },
    { label:'투입온도', value: d.charge_temp ?? '—', unit:'°C', cls:'' },
    { label:'배출(BT)', value: d.drop_temp ?? '—', unit:'°C', cls:'' },
    ...(d.et_drop_temp != null ? [{ label:'배출(ET)', value: d.et_drop_temp, unit:'°C', cls:'' }] : []),
    ...(d.weight_loss != null ? [{ label:'무게 손실률', value: d.weight_loss.toFixed(1), unit:'%',
      cls: d.weight_loss < 12 ? 'warn' : d.weight_loss > 20 ? 'warn' : 'good' }] : []),
    { label:'로스팅 포인트', value: d.current_roast_point || '—', unit:'', cls:'accent' },
  ];
  if (d.events && d.events.fcs!=null)
    cards.splice(2,0,{ label:'발달시간', value: fmtTime(d.total_time - d.events.fcs), unit:'', cls:'' });
  el.innerHTML = cards.map(c => `
    <div class="rp-metric ${c.cls}">
      <div class="rp-metric-label">${c.label}</div>
      <div class="rp-metric-value">${c.value}</div>
      <div class="rp-metric-unit">${c.unit}</div>
    </div>`).join('');
}

/* ════════ 차트 ════════ */
function buildChart(canvasId, times, bts, ets, agits, btRor, etRor, events, prev) {
  if (prev) prev.destroy();
  const labels = times.map(t => fmtTime(t));

  const annotations = {};
  const evMap = [['charge','투입','#6366f1'],['tp','TP','#8b5cf6'],['dry','건조','#f59e0b'],
    ['fcs','1차크랙','#ef4444'],['fce','FC종료','#f97316'],['drop','배출','#16a34a']];
  evMap.forEach(([k,label,color]) => {
    if (events[k]==null) return;
    const idx = times.reduce((best,t,i)=> Math.abs(t-events[k])<Math.abs(times[best]-events[k])?i:best, 0);
    annotations['ev_'+k] = { type:'line', xMin:idx, xMax:idx, borderColor:color, borderWidth:1.5,
      borderDash:[4,3], label:{ display:true, content:label, position:'start', font:{size:10}, color, backgroundColor:'rgba(255,255,255,.85)' } };
  });

  const datasets = [];

  // BT
  datasets.push({ label:'BT (°C)', data:bts, borderColor:'#e07b2a', backgroundColor:'rgba(224,123,42,.07)',
    borderWidth:2.5, pointRadius:0, tension:.35, yAxisID:'yT', order:1 });

  // ET (파란 점선, 있을 때만)
  if (ets && ets.length > 0)
    datasets.push({ label:'ET (°C)', data:ets, borderColor:'#60a5fa', backgroundColor:'rgba(96,165,250,.05)',
      borderWidth:1.8, pointRadius:0, tension:.35, yAxisID:'yT', borderDash:[5,3], order:2 });

  // BT ROR (초록 실선, 오른쪽 ROR 축)
  datasets.push({ label:'BT ROR (°C/min)', data:btRor, borderColor:'#22c55e', borderWidth:1.5,
    pointRadius:0, tension:.35, yAxisID:'yR', order:3 });
  // ET ROR (있을 때만, 연초록 점선)
  if (etRor && etRor.length > 0)
    datasets.push({ label:'ET ROR (°C/min)', data:etRor, borderColor:'#86efac', borderWidth:1.3,
      pointRadius:0, tension:.35, yAxisID:'yR', borderDash:[3,2], order:4, opacity:0.75 });

  // 교반 (보라 계단 라인, 있을 때만)
  if (agits && agits.length > 0)
    datasets.push({ label:'교반', data:agits, borderColor:'#a855f7', backgroundColor:'rgba(168,85,247,.08)',
      borderWidth:1.5, pointRadius:0, stepped:'before', yAxisID:'yG', fill:false, order:4 });

  const scales = {
    x:  { ticks:{ maxTicksLimit:12, font:{size:11} }, grid:{color:'rgba(0,0,0,.05)'} },
    yT: { type:'linear', position:'left',
          title:{display:true, text:'온도 (°C)', font:{size:11}},
          grid:{color:'rgba(0,0,0,.05)'} },
    yR: { type:'linear', position:'right',
          title:{display:true, text:'ROR (°C/min)', font:{size:11}},
          grid:{drawOnChartArea:false}, min:0, suggestedMax:30 },
  };

  if (agits && agits.length > 0) {
    scales.yG = { type:'linear', position:'right',
      title:{display:true, text:'교반', font:{size:11}, color:'#a855f7'},
      grid:{drawOnChartArea:false}, min:0, max:10,
      ticks:{ stepSize:1, color:'#a855f7', font:{size:10} },
      // ROR 축과 겹치지 않게 offset
      offset: true };
  }

  return new Chart($(canvasId), {
    type:'line',
    data:{ labels, datasets },
    options:{ responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
      plugins:{ legend:{display:false}, annotation:{annotations},
        tooltip:{ callbacks:{ label:c=>`${c.dataset.label}: ${c.parsed.y?.toFixed(1) ?? '—'}` } } },
      scales }
  });
}

/* ════════ 타겟 포인트 버튼 ════════ */
function renderTargetButtons(el, d, onPick, selected) {
  el.innerHTML = '';
  ROAST_POINTS.forEach(p => {
    const btn = document.createElement('button');
    btn.className = 'rp-target-btn'
      + (p.key===d.current_roast_point ? ' current' : '')
      + (p.key===selected ? ' active' : '');
    btn.textContent = p.key;
    btn.title = `배출 ${p.dropMin}~${p.dropMax}°C · DTR ${p.dtrMin}~${p.dtrMax}%`;
    btn.addEventListener('click', () => onPick(p.key));
    el.appendChild(btn);
  });
  const note = document.createElement('span');
  note.style.cssText = 'font-size:11.5px;color:var(--text3);align-self:center;margin-left:4px';
  note.textContent = d.current_roast_point ? `(테두리 = 현재: ${d.current_roast_point})` : '';
  el.appendChild(note);
}

/* ════════ 피드백 엔진 ════════ */
function renderFeedback(el, d, targetKey) {
  let html = '';

  // 블록 1: 포인트 변경 가이드
  html += `<div class="rp-fb-block"><div class="rp-fb-block-title">🎯 로스팅 포인트 변경 가이드</div>`;
  if (!targetKey) {
    html += `<div class="rp-fb-empty">위에서 원하는 다음 로스팅 포인트를 선택하면 맞춤 가이드를 보여드립니다.</div>`;
  } else {
    html += `<div class="rp-fb-list">${pointChangeGuide(d, targetKey).map(fbItem).join('')}</div>`;
  }
  html += `</div>`;

  // 블록 2: 종합 분석
  html += `<div class="rp-fb-block"><div class="rp-fb-block-title">🔬 전체 종합 분석</div>`;
  html += `<div class="rp-fb-list">${comprehensiveAnalysis(d).map(item =>
    item._fcsInput ? renderFcsInlineItem(item) : fbItem(item)
  ).join('')}</div></div>`;

  el.innerHTML = html;

  // DTR 인라인 입력 이벤트 연결 (DTR 미계산일 때만 존재)
  const inlineApply = el.querySelector('#btnFcsInlineApply');
  if (inlineApply) {
    inlineApply.addEventListener('click', () => {
      const inp = el.querySelector('#fcsInlineInput');
      const sec = parseTimeStr(inp.value.trim());
      if (!sec || sec <= 0 || sec >= d.total_time) { inp.style.borderColor='var(--red)'; return; }
      inp.style.borderColor = '';
      d.events = d.events || {};
      d.events.fcs = sec;
      d.dtr = +(((d.total_time - sec) / d.total_time) * 100).toFixed(1);
      const pt = analyzeCurrentPoint(d.drop_temp, d.dtr);
      if (pt) d.current_roast_point = pt.key;
      // step3 상단 fcsInputRow도 숨기기
      const row = $('fcsInputRow'); if (row) row.style.display = 'none';
      // 지표 카드 재렌더
      const metricsEl = $('metricsRow') || $('detailMetrics');
      if (metricsEl) renderMetrics(metricsEl, d);
      // 차트 이벤트 선 재그리기 (wizardData와 같은 객체라면 자동 반영)
      if (d === wizardData) {
        chartInstance = buildChart('roastChart',
          d.time_series, d.bt_series, d.et_series||[], d.agitation_series||[],
          d.ror||[], d.et_ror||[], d.events, chartInstance);
      }
      // 피드백 전체 재렌더
      renderFeedback(el, d, targetKey);
    });
  }
}
function fbItem(i){ return `<div class="rp-fb-item ${i.type}"><span class="rp-fb-icon">${i.icon}</span>
  <div class="rp-fb-text"><strong>${i.title}</strong>${i.text}</div></div>`; }

function renderFcsInlineItem(i) {
  return `<div class="rp-fb-item ${i.type}">
    <span class="rp-fb-icon">${i.icon}</span>
    <div class="rp-fb-text">
      <strong>${i.title}</strong>
      <span>${i.text}</span>
      <div class="rp-fcs-inline">
        <input type="text" id="fcsInlineInput" class="rp-fcs-input" placeholder="예: 4:30">
        <button id="btnFcsInlineApply" class="rp-btn-fcs">DTR 계산</button>
      </div>
    </div>
  </div>`;
}

/* 포인트 변경 가이드 */
function pointChangeGuide(d, targetKey) {
  const target = ROAST_POINTS.find(p=>p.key===targetKey);
  const cur = ROAST_POINTS.find(p=>p.key===d.current_roast_point);
  const items = [];
  if (!target) return items;
  const tMidDrop = Math.round((target.dropMin+target.dropMax)/2);
  const tMidDtr = ((target.dtrMin+target.dtrMax)/2).toFixed(0);

  if (cur && cur.order===target.order) {
    items.push({ type:'good', icon:'✅', title:`현재와 동일한 '${target.key}' 유지`,
      text:`이미 ${target.key} 범위입니다. 배출온도 ${target.dropMin}~${target.dropMax}°C, DTR ${target.dtrMin}~${target.dtrMax}%를 유지하면 일관되게 재현됩니다. ${target.desc}` });
    return items;
  }

  const darker = !cur || target.order > cur.order;
  const dropDelta = d.drop_temp!=null ? Math.round(tMidDrop - d.drop_temp) : null;
  const dtrDelta  = d.dtr!=null ? Math.round(tMidDtr - d.dtr) : null;

  // 핵심 변경 방향
  if (darker) {
    items.push({ type:'info', icon:'🔥', title:`더 다크하게 — '${target.key}'로`,
      text:`${cur?cur.key+'에서 ':''}${target.key}로 가려면 더 많은 열 에너지와 발달이 필요합니다. ${target.desc}` });
    if (dropDelta!=null && dropDelta>0)
      items.push({ type:'warn', icon:'🌡️', title:`배출온도 약 +${dropDelta}°C`,
        text:`현재 ${d.drop_temp}°C → 목표 ${tMidDrop}°C 부근. 1차 크랙 이후 열을 유지하며 배출 시점을 늦추세요.` });
    if (dtrDelta!=null && dtrDelta>0)
      items.push({ type:'warn', icon:'⏱️', title:`DTR 약 +${dtrDelta}%p (목표 ${target.dtrMin}~${target.dtrMax}%)`,
        text:`발달 시간을 늘려야 합니다. 단, ROR이 급반등(flick)하지 않도록 가스를 과하게 올리지 말고 완만히 유지하세요.` });
  } else {
    items.push({ type:'info', icon:'❄️', title:`더 라이트하게 — '${target.key}'로`,
      text:`${cur?cur.key+'에서 ':''}${target.key}로 가려면 발달을 줄이고 더 일찍 배출해야 합니다. ${target.desc}` });
    if (dropDelta!=null && dropDelta<0)
      items.push({ type:'warn', icon:'🌡️', title:`배출온도 약 ${dropDelta}°C`,
        text:`현재 ${d.drop_temp}°C → 목표 ${tMidDrop}°C 부근. 1차 크랙 후 더 이른 시점에 배출하세요.` });
    if (dtrDelta!=null && dtrDelta<0)
      items.push({ type:'warn', icon:'⏱️', title:`DTR 약 ${dtrDelta}%p (목표 ${target.dtrMin}~${target.dtrMax}%)`,
        text:`발달 시간을 줄이세요. 단, DTR이 15% 미만으로 떨어지면 풋내·신맛(언더디벨롭) 위험이 있으니 주의하세요.` });
  }
  items.push({ type:'info', icon:'🎨', title:`목표 Agtron ${target.agtron}`,
    text:`색도계가 있다면 ${target.agtron} 범위를 목표로 하세요. 같은 색이라도 가스 타이밍에 따라 마이야르/캐러멜화 균형이 달라지므로 컵핑으로 검증하세요.` });
  return items;
}

/* 종합 분석 */
function comprehensiveAnalysis(d) {
  const items = [];
  const { dtr, total_time, drop_temp, charge_temp, events, ambient_temp, ambient_humidity } = d;
  const bts = d.bt_series, times = d.time_series, ror = d.ror;

  // DTR
  if (dtr!=null) {
    if (dtr<15) items.push({type:'bad',icon:'⚠️',title:`DTR ${dtr.toFixed(1)}% — 발달 부족`,
      text:'권장 최소 15%에 미달합니다. 풋내·신맛·미성숙 향미(언더디벨롭) 위험. 1차 크랙 후 발달 시간을 늘리세요.'});
    else if (dtr>30) items.push({type:'warn',icon:'⚡',title:`DTR ${dtr.toFixed(1)}% — 과발달 경향`,
      text:'발달이 길어 평탄하거나 쓴맛이 날 수 있습니다. 라이트~미디엄을 원한다면 더 일찍 배출하세요.'});
    else items.push({type:'good',icon:'✅',title:`DTR ${dtr.toFixed(1)}% — 양호`,
      text:'일반적 권장 범위(15~30%) 안에 있습니다. 마이야르·캐러멜화 균형이 적절할 가능성이 높습니다.'});
  } else {
    items.push({type:'info', icon:'ℹ️', title:'DTR 미계산', _fcsInput: true,
      text:'1차 크랙 시작 시간을 입력하면 DTR을 바로 계산합니다.'});
  }

  // 페이즈 비율
  if (events && events.fcs!=null && total_time) {
    if (events.dry!=null) {
      const dryPct = (events.dry/total_time*100);
      const maillardPct = ((events.fcs-events.dry)/total_time*100);
      if (dryPct>45) items.push({type:'warn',icon:'🐢',title:`건조 단계 ${dryPct.toFixed(0)}% — 김`,
        text:'건조가 길면 마이야르 반응이 위축되어 베이킹·밋밋함(Too Slow 패턴)이 생길 수 있습니다.'});
      else if (dryPct<25) items.push({type:'warn',icon:'⚡',title:`건조 단계 ${dryPct.toFixed(0)}% — 짧음`,
        text:'건조가 짧으면 급속 승온으로 마이야르 과활성(Too Fast)이 되어 바디가 얕아질 수 있습니다.'});
      if (maillardPct<20) items.push({type:'warn',icon:'🍞',title:`마이야르 단계 ${maillardPct.toFixed(0)}% — 짧음`,
        text:'갈변·복잡한 향미 발달이 부족할 수 있습니다. 1차 크랙 전 구간에서 열을 더 유지하세요.'});
    }
  }

  // ROR 크래시/플릭
  if (ror && ror.length>=5) {
    const valid = ror.map((r,i)=>({r,i})).filter(o=>o.r!=null);
    let crash=false, flick=false;
    for (let j=2;j<valid.length-1;j++){
      const prev=valid[j-1].r, curr=valid[j].r, next=valid[j+1].r;
      if (prev-curr>4 && next<curr) crash=true;
      if (curr>prev+2.5 && valid[j].i > ror.length*0.65) flick=true;
    }
    if (crash) items.push({type:'bad',icon:'📉',title:'ROR 크래시 감지',
      text:'ROR이 급락하는 구간이 있습니다. 베이킹 결함으로 이어질 수 있습니다. 해당 구간에서 가스를 미리 완만히 줄이세요.'});
    if (flick) items.push({type:'warn',icon:'📈',title:'ROR 플릭(급반등) 감지',
      text:'발달 후반 ROR이 다시 상승하는 패턴입니다. 1차 크랙 중·후 가스를 올리면 탄 향이 날 수 있으니 화력을 낮추세요.'});
    if (!crash && !flick) items.push({type:'good',icon:'📊',title:'ROR 곡선 양호',
      text:'크래시·플릭 패턴이 감지되지 않았습니다. ROR이 비교적 매끄럽게 감소하고 있습니다.'});
  }

  // 총 시간
  if (total_time<420) items.push({type:'bad',icon:'⚡',title:`총 ${fmtTime(total_time)} — 매우 짧음`,
    text:'급속 로스팅으로 겉은 타고 속은 덜 익는 불균등 로스팅 위험이 있습니다.'});
  else if (total_time>1200) items.push({type:'warn',icon:'🐌',title:`총 ${fmtTime(total_time)} — 김`,
    text:'장시간 저온 로스팅은 베이킹·평탄화 결함으로 이어질 수 있습니다.'});

  // 환경(온습도) 반영
  if (ambient_humidity!=null) {
    if (ambient_humidity>=65) items.push({type:'info',icon:'💧',title:`실내 습도 ${ambient_humidity}% — 높음`,
      text:'습도가 높으면 생두가 수분을 머금어 건조 단계에 열이 더 필요합니다. 투입온도를 약간 높이거나 건조 구간 화력을 보강하세요.'});
    else if (ambient_humidity<35) items.push({type:'info',icon:'🏜️',title:`실내 습도 ${ambient_humidity}% — 낮음`,
      text:'건조한 환경에서는 수분 증발이 빨라 1차 크랙이 앞당겨질 수 있습니다. 후반 열 관리에 유의하세요.'});
  }
  if (ambient_temp!=null && ambient_temp<15)
    items.push({type:'info',icon:'🥶',title:`실내 온도 ${ambient_temp}°C — 낮음`,
      text:'저온 환경은 로스터 예열·열손실에 영향을 줍니다. 충분히 예열하고 배치 간 온도 회복을 확인하세요.'});

  // 생두 기반(이름 키워드)
  const name = (d.bean_name||'');
  if (/내추럴|natural|무산소|anaerobic|허니|honey/i.test(name))
    items.push({type:'info',icon:'🫘',title:'고당분 가공(내추럴/허니/무산소) 추정',
      text:'잔류 당분이 많아 타기 쉽습니다. 투입온도를 워시드보다 5~10°C 낮추고 초반 열을 절제하세요.'});
  else if (/게이샤|geisha|에스메랄다/i.test(name))
    items.push({type:'info',icon:'🌸',title:'게이샤 계열 추정 — 섬세한 향미',
      text:'플로럴·산미 보존을 위해 라이트~미디엄, 과한 발달을 피하는 것이 일반적입니다.'});
  else if (/예가체프|yirga|시다모|코케|아리차|에티오피아|ethiopia|케냐|kenya/i.test(name))
    items.push({type:'info',icon:'🌍',title:'아프리카 고지대 추정 — 고밀도',
      text:'단단한 고밀도 콩은 더 높은 열을 견딥니다. hot drum / low flame로 투입 후 후반 모멘텀을 유지하세요.'});

  // 무게 손실률
  if (d.weight_loss != null) {
    if (d.weight_loss < 12)
      items.push({type:'warn', icon:'⚖️', title:`무게 손실률 ${d.weight_loss.toFixed(1)}% — 낮음`,
        text:'손실률이 낮으면 수분 제거가 불충분하거나 배출이 너무 빠를 수 있습니다. 라이트 로스팅은 12~14%, 다크는 18~20% 범위가 일반적입니다.'});
    else if (d.weight_loss > 20)
      items.push({type:'warn', icon:'⚖️', title:`무게 손실률 ${d.weight_loss.toFixed(1)}% — 높음`,
        text:'손실률이 높으면 과배전이거나 총 시간이 길 수 있습니다. 다크 이상 로스팅이 아니라면 배출 시점을 앞당기는 것을 고려하세요.'});
    else
      items.push({type:'good', icon:'⚖️', title:`무게 손실률 ${d.weight_loss.toFixed(1)}% — 정상`,
        text:`일반적인 스페셜티 로스팅 손실 범위(12~20%)에 있습니다. 로스팅 포인트(${d.current_roast_point||'—'})에 맞는 적절한 수준입니다.`});
  }

  if (!items.length) items.push({type:'info',icon:'ℹ️',title:'데이터를 더 입력해 보세요',
    text:'이벤트 포인트와 곡선점을 더 추가하면 상세한 분석이 가능합니다.'});
  return items;
}

/* ════════ 상세 뷰 ════════ */
function showDetail(p) {
  activeId = p.id; renderList();
  $('detailName').textContent = p.bean_name;
  $('detailMeta').textContent = [p.seller, p.roaster, p.roast_date,
    p.ambient_temp!=null?`${p.ambient_temp}°C`:null,
    p.ambient_humidity!=null?`습도 ${p.ambient_humidity}%`:null].filter(Boolean).join(' · ');
  renderMetrics($('detailMetrics'), p);
  detailChartInstance = buildChart('detailChart', p.time_series||[], p.bt_series||[], p.et_series||[], p.agitation_series||[], p.ror||computeRoR(p.time_series||[], p.bt_series||[]), p.et_ror||[], p.events||{}, detailChartInstance);

  let sel = p.target_roast_point || null;
  const render = () => renderTargetButtons($('detailTargetBtns'), p, (key)=>{ sel=key; render(); renderFeedback($('detailFeedback'), p, key); }, sel);
  render();
  renderFeedback($('detailFeedback'), p, sel);
  showView('detail');
}

/* ════════ 유틸 ════════ */
function fmtTime(sec){ if(sec==null) return '—'; sec=Math.round(sec); return `${Math.floor(sec/60)}:${String(sec%60).padStart(2,'0')}`; }
function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
