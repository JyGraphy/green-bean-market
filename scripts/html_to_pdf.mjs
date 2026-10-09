/**
 * HTML → PDF (쪽번호 포함).
 *
 *   node scripts/html_to_pdf.mjs <input.html> <output.pdf> [머리말]
 *
 * chromium 의 `--print-to-pdf` 로는 쪽번호를 못 넣는다(머리말/꼬리말 템플릿을
 * CLI 로 못 준다). 그래서 playwright 로 띄워 page.pdf() 의 footerTemplate 에
 * {{pageNumber}}/{{totalPages}} 를 넣는다. 공부용으로 통째로 읽을 문서라
 * 쪽번호가 있어야 "몇 쪽 얘기"가 가능하다.
 *
 * 브라우저는 컨테이너에 미리 깔린 것을 쓴다(PLAYWRIGHT_BROWSERS_PATH).
 * 절대 `playwright install` 을 돌리지 않는다.
 */
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';

/**
 * playwright 는 이 리포의 의존성이 아니라 **전역 설치**(npm -g)되어 있다.
 * ESM 의 bare import 는 NODE_PATH 를 보지 않으므로, 전역 경로를 직접 찾아 require 한다.
 * (리포에 node_modules 를 만들지 않으려는 의도 — 이 리포는 정적 사이트다.)
 */
function loadPlaywright() {
  const roots = [];
  if (process.env.NODE_PATH) roots.push(...process.env.NODE_PATH.split(':'));
  try {
    roots.push(execSync('npm root -g', { encoding: 'utf8' }).trim());
  } catch { /* npm 이 없으면 아래 후보로 간다 */ }
  roots.push('/opt/node22/lib/node_modules', '/usr/lib/node_modules',
             '/usr/local/lib/node_modules');

  for (const root of roots.filter(Boolean)) {
    try {
      const req = createRequire(resolve(root, 'noop.js'));
      return req('playwright');
    } catch { /* 다음 후보 */ }
  }
  throw new Error('playwright 를 찾지 못했다 — `npm root -g` 확인 필요');
}

const { chromium } = loadPlaywright();

const [input, output, headerText = ''] = process.argv.slice(2);
if (!input || !output) {
  console.error('사용법: node scripts/html_to_pdf.mjs <input.html> <output.pdf> [머리말]');
  process.exit(2);
}

const esc = (s) => s.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

const browser = await chromium.launch({
  args: ['--no-sandbox', '--disable-gpu', '--font-render-hinting=none'],
});
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(resolve(input)).href, { waitUntil: 'load' });
  // 웹폰트·레이아웃이 자리잡을 시간 (fc-cache 직후 첫 렌더가 밀리는 경우가 있다)
  await page.waitForTimeout(600);

  const style = 'font-family:"Noto Sans KR",sans-serif;font-size:7.4pt;color:#8a9096;'
    + 'width:100%;padding:0 16mm;-webkit-print-color-adjust:exact;';

  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    // 문서의 h1~h3 로 PDF 북마크(뷰어 사이드바 목차)를 만든다 — 31쪽짜리를
    // 공부용으로 넘겨볼 때 앞뒤로 점프가 된다.
    outline: true,
    tagged: true,
    displayHeaderFooter: true,
    margin: { top: '17mm', bottom: '17mm', left: '16mm', right: '16mm' },
    headerTemplate:
      `<div style="${style}text-align:right;">${esc(headerText)}</div>`,
    footerTemplate:
      `<div style="${style}display:flex;justify-content:space-between;">`
      + '<span>생두마켓 세컨드 브레인</span>'
      + '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span>'
      + '</div>',
  });
  console.log('🖨️  PDF 작성 완료');
} finally {
  await browser.close();
}
