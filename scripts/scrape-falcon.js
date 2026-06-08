/**
 * 팔콘커피 생두 스크래퍼
 * 실행: node scripts/scrape-falcon.js
 * 결과: scripts/falcon-output.sql (database.sql에 붙여넣기)
 */

const https = require('https');

const BASE_URL = 'korea.falcon-micro.com';
const COLLECTION = 'korea-store-all-coffee';
const STORE_NAME = '팔콘커피';
const START_ID = 850; // 기존 최대 ID(845) 이후부터 시작

function get(path) {
  return new Promise((resolve, reject) => {
    https.get({ hostname: BASE_URL, path, headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { reject(new Error('JSON parse error: ' + data.slice(0, 200))); }
      });
    }).on('error', reject);
  });
}

function extractProcess(name) {
  const n = (name || '').toLowerCase();
  if (/무산소|anaerobic|애너러빅|카보닉|carbonic|인퓨즈드/.test(n)) return '무산소발효';
  if (/펄프드.?내추럴|pulped.?natural/.test(n)) return '펄프드내추럴';
  if (/워시드|washed|fully.?washed/.test(n)) return '워시드';
  if (/레드허니|옐로허니|화이트허니|블랙허니|세미워시드|semi.?washed/.test(n)) return '허니';
  if (/허니|honey/.test(n)) return '허니';
  if (/내추럴|natural|레포사도/.test(n)) return '내추럴';
  if (/웻.?훌|웻.?헐|wet.?hul/.test(n)) return '웻훌드';
  return '알수없음';
}

function guessOrigin(title) {
  const t = title;
  if (/에티오피아|ethiopia/i.test(t)) return { origin: '에티오피아', region: '아프리카' };
  if (/케냐|kenya/i.test(t)) return { origin: '케냐', region: '아프리카' };
  if (/탄자니아|tanzania/i.test(t)) return { origin: '탄자니아', region: '아프리카' };
  if (/르완다|rwanda/i.test(t)) return { origin: '르완다', region: '아프리카' };
  if (/우간다|uganda/i.test(t)) return { origin: '우간다', region: '아프리카' };
  if (/콩고|congo/i.test(t)) return { origin: '콩고민주공화국', region: '아프리카' };
  if (/브라질|brazil/i.test(t)) return { origin: '브라질', region: '중남미' };
  if (/콜롬비아|colombia/i.test(t)) return { origin: '콜롬비아', region: '중남미' };
  if (/과테말라|guatemala/i.test(t)) return { origin: '과테말라', region: '중남미' };
  if (/코스타리카|costa.?rica/i.test(t)) return { origin: '코스타리카', region: '중남미' };
  if (/파나마|panama/i.test(t)) return { origin: '파나마', region: '중남미' };
  if (/엘살바도르|el.?salvador/i.test(t)) return { origin: '엘살바도르', region: '중남미' };
  if (/온두라스|honduras/i.test(t)) return { origin: '온두라스', region: '중남미' };
  if (/멕시코|mexico/i.test(t)) return { origin: '멕시코', region: '중남미' };
  if (/페루|peru/i.test(t)) return { origin: '페루', region: '중남미' };
  if (/볼리비아|bolivia/i.test(t)) return { origin: '볼리비아', region: '중남미' };
  if (/에콰도르|ecuador/i.test(t)) return { origin: '에콰도르', region: '중남미' };
  if (/니카라과|nicaragua/i.test(t)) return { origin: '니카라과', region: '중남미' };
  if (/자메이카|jamaica/i.test(t)) return { origin: '자메이카', region: '중남미' };
  if (/인도네시아|indonesia/i.test(t)) return { origin: '인도네시아', region: '아시아/태평양' };
  if (/인도|india/i.test(t)) return { origin: '인도', region: '아시아/태평양' };
  if (/베트남|vietnam/i.test(t)) return { origin: '베트남', region: '아시아/태평양' };
  if (/하와이|hawaii/i.test(t)) return { origin: '하와이', region: '아시아/태평양' };
  if (/파푸아|papua/i.test(t)) return { origin: '파푸아뉴기니', region: '아시아/태평양' };
  if (/예멘|yemen/i.test(t)) return { origin: '예멘', region: '아시아/태평양' };
  if (/중국|china|yunnan|yunnan/i.test(t)) return { origin: '중국', region: '아시아/태평양' };
  return { origin: '기타', region: '기타' };
}

function isGreenBean(title, tags, productType) {
  const combined = [title, ...(tags || []), productType || ''].join(' ').toLowerCase();
  // 생두 키워드 포함
  if (/생두|green.?bean|raw.?coffee|unroasted/.test(combined)) return true;
  // 원두(roasted) 제외
  if (/원두|roast|drip.?bag|드립백|캡슐|capsule/.test(combined)) return false;
  return true; // 기본적으로 포함
}

function isNew(title) {
  return /2026|26crop|-26-/i.test(title);
}

function isDecaf(title) {
  return /디카페인|decaf/i.test(title);
}

function isSpecial(title, price) {
  return price >= 50000 || /게이샤|geisha|파카마라|pacamara|에스메랄다|esmeralda|sl28|sl34|자바|java/i.test(title);
}

function esc(s) {
  return (s || '').replace(/'/g, "''");
}

async function scrape() {
  const products = [];
  let page = 1;

  console.log('팔콘커피 스크래핑 시작...');

  while (true) {
    const path = `/collections/${COLLECTION}/products.json?limit=250&page=${page}`;
    console.log(`  페이지 ${page} 요청 중...`);
    const data = await get(path);

    if (!data.products || data.products.length === 0) break;

    for (const p of data.products) {
      // 생두만 필터
      if (!isGreenBean(p.title, p.tags, p.product_type)) {
        console.log(`  [스킵] ${p.title}`);
        continue;
      }

      // 대표 variant (가장 저렴한 1kg 옵션 우선)
      const variants = p.variants || [];
      const kgVariant = variants.find(v =>
        /1\s*kg|1000\s*g/i.test(v.title) || variants.length === 1
      ) || variants[0];

      if (!kgVariant) continue;

      const price = Math.round(parseFloat(kgVariant.price));
      if (!price) continue;

      const { origin, region } = guessOrigin(p.title);
      const process = extractProcess(p.title);
      const url = `https://korea.falcon-micro.com/products/${p.handle}`;

      products.push({
        name: p.title,
        price,
        origin,
        region,
        process,
        notes: '',
        url,
        isNew: isNew(p.title) ? 1 : 0,
        isDecaf: isDecaf(p.title) ? 1 : 0,
        isSpecial: isSpecial(p.title, price) ? 1 : 0,
      });

      console.log(`  ✓ ${p.title} — ₩${price.toLocaleString()} / ${origin}`);
    }

    if (data.products.length < 250) break;
    page++;
    await new Promise(r => setTimeout(r, 500));
  }

  console.log(`\n총 ${products.length}개 생두 상품 수집 완료`);

  // SQL 생성
  const fs = require('fs');
  const path = require('path');

  const rows = products.map((p, i) => {
    const id = START_ID + i;
    return `  (${id},'${esc(STORE_NAME)}','${esc(p.name)}',${p.price},'${esc(p.origin)}','${esc(p.region)}','${esc(p.process)}','${esc(p.notes)}','${esc(p.url)}',${p.isNew},${p.isDecaf},${p.isSpecial})`;
  });

  const sql = `-- 팔콘커피 생두 데이터 (${products.length}개)\n-- database.sql의 기존 INSERT 마지막 줄 세미콜론(;) 앞에 쉼표(,)로 연결하거나\n-- 아래를 별도 INSERT로 붙여넣으세요.\n\nINSERT INTO products (id,store,name,price,origin,region,process,notes,url,isNew,isDecaf,isSpecial) VALUES\n${rows.join(',\n')};\n`;

  const outPath = path.join(__dirname, 'falcon-output.sql');
  fs.writeFileSync(outPath, sql, 'utf8');
  console.log(`\n✅ 결과 저장: ${outPath}`);
  console.log('\n다음 단계:');
  console.log('1. scripts/falcon-output.sql 내용을 확인');
  console.log('2. database.sql 맨 아래에 붙여넣기');
  console.log('3. styles.css와 index.html에 팔콘커피 배지 추가');
}

scrape().catch(console.error);
