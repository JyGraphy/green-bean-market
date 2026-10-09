#!/usr/bin/env python3
"""
볼트 문서(마크다운) → 읽기 편한 한글 PDF.

    python3 scripts/build_pdf.py --preset 품종
    python3 scripts/build_pdf.py --out /tmp/x.pdf --title "제목" a.md b.md

왜 이 스크립트가 있나 — 볼트는 옵시디언으로 읽는 게 기본이지만, 공부용으로 통째로
읽거나 출력·공유할 때는 PDF가 낫다. 주제가 늘어날 때마다 수작업으로 만들지 않도록
프리셋만 추가하면 되게 해둔다.

파이프라인:
    마크다운 → (python-markdown) → 인쇄용 CSS 입힌 단일 HTML
             → (node playwright + chromium) → PDF

한글 폰트: Noto Sans KR 이 없는 환경(이 컨테이너 기본값)에서는 한글이 두부(□)로
나온다. ensure_font() 가 없으면 받아서 ~/.fonts 에 깔고 fc-cache 를 돌린다.
"""
import argparse
import html
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
VAULT = ROOT / 'vault'
PRINTER = ROOT / 'scripts' / 'html_to_pdf.mjs'

FONT_DIR = pathlib.Path.home() / '.fonts'
FONT_FILE = FONT_DIR / 'NotoSansKR[wght].ttf'
FONT_URL = ('https://raw.githubusercontent.com/google/fonts/main/ofl/'
            'notosanskr/NotoSansKR%5Bwght%5D.ttf')

# 주제별 묶음. 각 항목 = (문서 경로, 섹션 제목, 한 줄 설명)
PRESETS: dict[str, dict] = {
    '품종도감': {
        'title': '커피 품종 도감',
        'subtitle': '계보도와 품종별 설명 — 품종을 처음 보는 사람을 위한 안내서',
        'docs': [
            ('raw/papers/2026-10-09-품종도감.md', '품종 도감',
             '용어 → 계보도 3장 → 품종 40여 종 개별 설명 → 비교표 → 라벨 읽는 법'),
            ('raw/papers/2026-10-05-품종-기초이론.md', '부록 — 품종 기초이론',
             '종 지도·배수체화·분류 5유형을 이론 쪽에서 한 번 더'),
            ('raw/papers/2026-08-03-wcr-f1하이브리드-스타마야.md',
             '부록 — 스타마야 F1 하이브리드 원논문 정리',
             '씨앗으로 번식하는 F1 을 만든 방법'),
            ('raw/papers/2026-08-03-wcr-커피잎녹병-품종시험.md',
             '부록 — 29개 품종 × 23개 지역 잎녹병 시험',
             '"저항성 품종" 라벨을 지역 검증 없이 믿으면 안 되는 이유'),
        ],
    },
    '품종': {
        'title': '커피 품종',
        'subtitle': '종(species)·계통(lineage)·분류체계 — 기초이론 종합',
        'docs': [
            ('wiki/커피-품종.md', '정리본 — 한 장 요약',
             '결론만 먼저. 세부는 뒤의 상세본에 있다.'),
            ('raw/papers/2026-10-05-품종-기초이론.md', '상세본 — 품종 기초이론',
             '종 지도·배수체화·분류 5유형·산지별 품종·품종명 혼란·사이트 현황'),
            ('raw/papers/2026-08-03-wcr-품종카탈로그-기후도구.md',
             '근거 ① WCR 품종 카탈로그 & CafeClima',
             '품종 스펙을 대조할 표준 소스'),
            ('raw/papers/2026-08-03-wcr-f1하이브리드-스타마야.md',
             '근거 ② 스타마야 — 최초의 씨앗번식 F1 하이브리드',
             'F1 하이브리드의 번식 문제와 그 해법'),
            ('raw/papers/2026-08-03-wcr-커피잎녹병-품종시험.md',
             '근거 ③ 29개 품종 × 23개 지역 잎녹병 시험',
             '"저항성 품종" 라벨을 지역 검증 없이 믿으면 안 되는 이유'),
            ('raw/papers/2026-08-03-wcr-기후변화-재배적합성.md',
             '근거 ④ 기후변화와 재배 적합성',
             '품종 선택이 기후 적응 전략이 되는 맥락'),
            ('raw/papers/2026-08-03-wcr-종합.md',
             '근거 ⑤ WCR 자료 종합',
             '위 네 건을 묶은 기존 종합 정리본'),
        ],
    },
}


# ─────────────────────────────── 폰트 ───────────────────────────────

def ensure_font() -> bool:
    """한글 폰트를 보장한다. 이미 있으면 그대로 True."""
    have = subprocess.run(['fc-list', ':lang=ko', 'family'],
                          capture_output=True, text=True).stdout
    if 'Noto Sans KR' in have:
        return True
    if not FONT_FILE.exists():
        FONT_DIR.mkdir(parents=True, exist_ok=True)
        print(f'🔤 한글 폰트 설치 중 — {FONT_URL}')
        try:
            with urllib.request.urlopen(FONT_URL, timeout=120) as r, \
                 open(FONT_FILE, 'wb') as f:
                shutil.copyfileobj(r, f)
        except Exception as e:                       # noqa: BLE001
            print(f'⚠️  폰트 다운로드 실패({e}) — 한글이 깨질 수 있다')
            return False
    subprocess.run(['fc-cache', '-f'], capture_output=True)
    print(f'✅ 폰트 설치: {FONT_FILE} ({FONT_FILE.stat().st_size:,} bytes)')
    return True


# ───────────────────────── 마크다운 전처리 ─────────────────────────

WIKILINK = re.compile(r'\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]')
CHECKBOX = re.compile(r'^(\s*)-\s*\[( |x|X)\]\s*', re.M)
# ![설명](assets/x.svg "landscape") — 제목이 landscape 면 가로 페이지 한 장을 통째로 쓴다
SVGIMG = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+\.svg)(?:\s+"([^"]*)")?\)\s*$', re.M)


def inline_svgs(md: str, base: pathlib.Path) -> str:
    """SVG 이미지를 파일째 본문에 박는다.

    <img src> 로 두면 PDF 에 래스터로 들어가 확대 시 깨지고, 파일 경로가 어긋나면
    조용히 빈칸이 된다. 인라인 SVG 면 벡터로 들어가고 누락도 바로 드러난다.
    마크다운 원문은 표준 이미지 문법이라 옵시디언에서도 그대로 보인다.
    """
    def sub(m: re.Match) -> str:
        alt, rel, title = m.group(1), m.group(2), (m.group(3) or '')
        path = base / rel
        if not path.exists():
            print(f'⚠️  SVG 없음: {rel}')
            return f'> ⚠️ 그림을 찾지 못했다: `{rel}`'
        svg = path.read_text(encoding='utf-8')
        land = title == 'landscape'
        cls = 'fig fig-land' if land else 'fig'
        # 가로 전면 그림은 SVG 안에 제목이 들어 있다 — 캡션을 또 붙이면 높이를
        # 넘겨 다음 장으로 밀린다.
        cap = '' if land or not alt else f'<figcaption>{html.escape(alt)}</figcaption>'
        return f'<figure class="{cls}">{svg}{cap}</figure>'
    return SVGIMG.sub(sub, md)


def preprocess(md: str) -> str:
    """PDF 에서 의미가 사라지는 표기를 읽을 수 있는 형태로 바꾼다."""
    # 옵시디언 위키링크는 PDF 에서 클릭이 안 되니 '참조' 표기로 바꾼다.
    md = WIKILINK.sub(lambda m: f'`{m.group(1)}`', md)
    # 체크박스 리스트 → 글리프 (markdown 기본 변환은 '[ ]' 를 그대로 흘린다)
    md = CHECKBOX.sub(lambda m: f'{m.group(1)}- '
                                f'{"☑" if m.group(2) in "xX" else "☐"} ', md)
    # 일반 문단 바로 다음 줄에서 시작하는 리스트 앞에 빈 줄을 넣는다.
    # 옵시디언은 이걸 리스트로 그려주지만 python-markdown 은 (nl2br 와 겹쳐)
    # 앞 문단에 붙여버려 '- 항목' 이 글자 그대로 찍힌다(출처 목록이 그랬다).
    out: list[str] = []
    in_code = False
    for line in md.split('\n'):
        if line.lstrip().startswith('```'):
            in_code = not in_code
        starts_list = bool(re.match(r'\s*([-*+]|\d+\.)\s', line))
        prev = out[-1] if out else ''
        prev_is_text = bool(prev.strip()) and not re.match(
            r'\s*([-*+]|\d+\.)\s|\s*#|\s*>|\s*\||\s*```', prev)
        if not in_code and starts_list and prev_is_text:
            out.append('')
        out.append(line)
    return '\n'.join(out)


# 모든 리서치 문서에 똑같이 붙는 상용구 제목 — 목차에 넣으면 7번 반복돼 목차가
# 두 쪽으로 늘고 정작 내용이 안 보인다. 본문에는 그대로 두고 목차에서만 뺀다.
TOC_SKIP = re.compile(
    r'^(📌\s*)?(결론\s*3줄|사장님\s*결정\s*필요|서지정보|출처.*|한계|방법.*|'
    r'연구\s*배경.*|근거\s*문서.*|실무\s*시사점.*|다음에?\s*할\s*것|'
    r'핵심\s*결과.*|확인하지\s*못한\s*것.*|다음\s*조사\s*후보.*)$')


def toc_worthy(title: str) -> bool:
    return not TOC_SKIP.match(re.sub(r'^[^\w가-힣]+', '', title).strip())


def slugify(text: str, used: set[str]) -> str:
    s = re.sub(r'[^\w가-힣]+', '-', text.strip()).strip('-').lower() or 'sec'
    base, n = s, 2
    while s in used:
        s, n = f'{base}-{n}', n + 1
    used.add(s)
    return s


def render_doc(md: str, idx: int, used: set[str],
               base: pathlib.Path) -> tuple[str, list[tuple[int, str, str]]]:
    """마크다운 1건 → (HTML, 목차항목[(레벨, 제목, 앵커)])."""
    import markdown
    body = markdown.markdown(
        inline_svgs(preprocess(md), base),
        extensions=['tables', 'fenced_code', 'sane_lists', 'nl2br', 'attr_list'],
    )

    toc: list[tuple[int, str, str]] = []

    def anchor(m: re.Match) -> str:
        lvl, inner = int(m.group(1)), m.group(2)
        plain = re.sub(r'<[^>]+>', '', inner)
        # 문서 안의 h1 은 섹션 제목과 중복되니 h2 로 눌러 계층을 맞춘다.
        out_lvl = max(2, lvl)
        if out_lvl <= 3:
            a = slugify(f'{idx}-{plain}', used)
            toc.append((out_lvl, plain, a))
            return f'<h{out_lvl} id="{a}">{inner}</h{out_lvl}>'
        return f'<h{out_lvl}>{inner}</h{out_lvl}>'

    body = re.sub(r'<h([1-6])>(.*?)</h\1>', anchor, body, flags=re.S)
    return body, toc


# ──────────────────────────────── CSS ────────────────────────────────

CSS = r"""
@page { size: A4; margin: 17mm 16mm 17mm 16mm; }

:root{
  --ink:#1a1a1a; --muted:#5b6166; --line:#d8dde1; --soft:#f5f7f8;
  --accent:#6b3410; --accent2:#9a5b2a; --warn:#b45309; --ok:#15803d;
}
*{ box-sizing:border-box; }
html{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }
body{
  font-family:"Noto Sans KR","NanumGothic","WenQuanYi Zen Hei",sans-serif;
  font-weight:400; font-size:10.3pt; line-height:1.78; color:var(--ink);
  margin:0; word-break:keep-all; overflow-wrap:break-word;
}

/* ── 표지 ── */
.cover{ height:247mm; display:flex; flex-direction:column; justify-content:center;
        page-break-after:always; }
.cover .kicker{ font-size:9pt; letter-spacing:.22em; color:var(--accent2);
                font-weight:700; margin-bottom:10mm; }
.cover h1{ font-size:33pt; font-weight:800; line-height:1.2; margin:0 0 5mm;
           letter-spacing:-.02em; border:0; padding:0; }
.cover .sub{ font-size:12.5pt; color:var(--muted); line-height:1.6; margin:0 0 14mm;
             font-weight:500; }
.cover .rule{ width:34mm; height:3px; background:var(--accent); margin:0 0 14mm; }
.cover dl{ margin:0; font-size:9.6pt; }
.cover dt{ color:var(--accent2); font-weight:700; font-size:8.6pt;
           letter-spacing:.08em; margin-top:5mm; }
.cover dd{ margin:1mm 0 0; color:var(--ink); }
.cover .note{ margin-top:16mm; padding:5mm 6mm; background:var(--soft);
              border-left:3px solid var(--warn); font-size:9pt; color:var(--muted);
              line-height:1.65; }

/* ── 목차 ── */
.toc{ page-break-after:always; }
.toc h2{ font-size:16pt; margin:0 0 7mm; border:0; padding:0; }
.toc ol{ list-style:none; margin:0; padding:0; counter-reset:s; }
.toc li.l2{ counter-increment:s; margin:0 0 1.5mm; font-weight:600; font-size:10.4pt;
            display:flex; gap:3mm; padding-top:2.5mm; border-top:1px solid var(--line); }
.toc li.l2::before{ content:counter(s); color:var(--accent2); font-weight:800;
                    min-width:6mm; }
.toc li.l3{ margin:0 0 .8mm 9mm; font-size:9.3pt; color:var(--muted); }
.toc li.l3::before{ content:"·"; color:var(--accent2); margin-right:2mm; }
.toc .part{ margin:7mm 0 3mm; font-size:8.6pt; letter-spacing:.14em;
            color:var(--accent2); font-weight:800; }

/* ── 섹션 ── */
.sec{ page-break-before:always; }
.sec-head{ margin:0 0 7mm; padding-bottom:4mm; border-bottom:2.5px solid var(--accent); }
.sec-head .n{ font-size:8.4pt; letter-spacing:.16em; color:var(--accent2);
              font-weight:800; }
.sec-head h1{ font-size:20pt; font-weight:800; margin:1.5mm 0 2mm; border:0;
              padding:0; line-height:1.25; }
.sec-head .d{ font-size:9.4pt; color:var(--muted); margin:0; }
.sec-head .src{ font-size:8.2pt; color:var(--muted); margin:2.5mm 0 0;
                font-family:ui-monospace,monospace; }

h2{ font-size:13.5pt; font-weight:800; margin:9mm 0 3mm; padding-bottom:1.8mm;
    border-bottom:1px solid var(--line); page-break-after:avoid; line-height:1.35; }
h3{ font-size:11.2pt; font-weight:700; margin:6.5mm 0 2mm; color:var(--accent);
    page-break-after:avoid; line-height:1.4; }
h4,h5,h6{ font-size:10.3pt; font-weight:700; margin:5mm 0 1.5mm;
          page-break-after:avoid; }
p{ margin:0 0 2.6mm; }
strong{ font-weight:700; }
ul,ol{ margin:0 0 3mm; padding-left:5.5mm; }
li{ margin:0 0 1.2mm; }
li>ul,li>ol{ margin-top:1.2mm; }
hr{ border:0; border-top:1px solid var(--line); margin:7mm 0; }
a{ color:var(--accent); text-decoration:none; }

/* 표 */
table{ width:100%; border-collapse:collapse; margin:3mm 0 4.5mm; font-size:9.1pt;
       page-break-inside:avoid; }
thead{ display:table-header-group; }
th{ background:var(--accent); color:#fff; font-weight:700; text-align:left;
    padding:2mm 2.4mm; font-size:8.8pt; line-height:1.45; }
td{ padding:1.9mm 2.4mm; border-bottom:1px solid var(--line); vertical-align:top;
    line-height:1.55; }
tbody tr:nth-child(even) td{ background:var(--soft); }
tr{ page-break-inside:avoid; }

/* 콜아웃(원문의 > 인용) */
blockquote{ margin:3.5mm 0; padding:3mm 4mm; background:var(--soft);
            border-left:3px solid var(--accent2); font-size:9.5pt;
            page-break-inside:avoid; }
blockquote p:last-child{ margin-bottom:0; }

/* 그림(인라인 SVG) */
@page land { size: A4 landscape; margin: 11mm; }
figure.fig{ margin:5mm 0 6mm; page-break-inside:avoid; }
figure.fig svg{ display:block; width:100%; height:auto; }
figure.fig figcaption{ margin-top:2.5mm; font-size:8.6pt; color:var(--muted);
                       text-align:center; }
/* 큰 계보도는 가로 A4 한 장을 통째로 쓴다 — 세로폭에 욱여넣으면 글자가 안 읽힌다.
   높이를 고정해야 한다: width:100%/height:auto 로 두면 그림이 인쇄영역보다 길어져
   아래쪽(범례)이 다음 장으로 잘려 넘어간다. viewBox + preserveAspectRatio 가
   이 상자 안에 비율 그대로 맞춰 넣는다. */
figure.fig-land{ page:land; page-break-before:always; page-break-after:always;
                 margin:0; width:100%; height:168mm;
                 display:flex; align-items:center; }
figure.fig-land svg{ width:100%; height:100%; }

/* 코드/위키참조 */
code{ font-family:ui-monospace,"DejaVu Sans Mono",monospace; font-size:8.9pt;
      background:#eef1f3; padding:.4mm 1.2mm; border-radius:2px;
      color:#31414d; word-break:break-all; }
pre{ background:#f7f9fa; border:1px solid var(--line); border-left:3px solid var(--muted);
     padding:3mm 3.5mm; overflow:hidden; margin:3mm 0 4mm; page-break-inside:avoid; }
pre code{ background:none; padding:0; font-size:8.5pt; line-height:1.55;
          word-break:normal; white-space:pre-wrap; }
"""


def build_html(title: str, subtitle: str, docs: list[tuple[str, str, str]],
               base: pathlib.Path) -> str:
    import datetime
    used: set[str] = set()
    secs, toc_html = [], []

    for i, (rel, sec_title, sec_desc) in enumerate(docs, 1):
        path = base / rel
        if not path.exists():
            print(f'⚠️  건너뜀 (없음): {rel}')
            continue
        body, toc = render_doc(path.read_text(encoding='utf-8'), i, used, base)

        # 원문 첫 h1 은 섹션 헤더와 중복이라 본문에서 제거한다.
        body = re.sub(r'<h2 id="[^"]*">(?:(?!</h2>).)*?</h2>', '', body, count=1,
                      flags=re.S)
        toc = toc[1:] if toc else toc

        first = slugify(f'sec{i}', used)
        secs.append(
            f'<section class="sec" id="{first}">'
            f'<div class="sec-head"><div class="n">PART {i:02d}</div>'
            f'<h1>{html.escape(sec_title)}</h1>'
            f'<p class="d">{html.escape(sec_desc)}</p>'
            f'<p class="src">vault/{html.escape(rel)}</p></div>'
            f'{body}</section>'
        )
        toc_html.append(f'<li class="l2"><span>{html.escape(sec_title)}</span></li>')
        subs = [t for lvl, t, _a in toc if lvl == 2 and toc_worthy(t)]
        for text in subs:
            toc_html.append(f'<li class="l3">{html.escape(text)}</li>')
        if not subs:
            toc_html.append(f'<li class="l3">{html.escape(sec_desc)}</li>')

    today = datetime.date.today().isoformat()
    srclist = ''.join(
        f'<dd>vault/{html.escape(r)}</dd>' for r, _t, _d in docs
        if (base / r).exists())

    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>

<div class="cover">
  <div class="kicker">생두마켓 · 커피 기초이론 시리즈</div>
  <h1>{html.escape(title)}</h1>
  <div class="rule"></div>
  <p class="sub">{html.escape(subtitle)}</p>
  <dl>
    <dt>발행</dt><dd>{today}</dd>
    <dt>수록 문서</dt>{srclist}
    <dt>출처</dt><dd>세컨드 브레인 볼트 (vault/) — 원문은 옵시디언에서 열람</dd>
  </dl>
  <div class="note">
    <strong>신뢰도 표기를 먼저 읽을 것.</strong> 각 문서 머리에 신뢰도와 본문 접근
    제약이 적혀 있다. 이 세션은 네트워크 정책상 WebFetch 가 대부분 차단되어
    (worldcoffeeresearch.org 403, PMC EGRESS_BLOCKED) 상당 부분이 검색 요약 기반이다.
    학술 1차 근거는 논문 전문 대기열에 등록돼 있고, 받아오면 수치를 교정한다.
    확인 못 한 항목은 각 문서 안에 <strong>미확인으로 남겨두었다</strong> — 추측으로
    메우지 않았다.
  </div>
</div>

<div class="toc"><h2>목차</h2>
  <div class="part">수록 내용</div>
  <ol>{''.join(toc_html)}</ol>
</div>

{''.join(secs)}
</body></html>"""


# ──────────────────────────────── main ────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--preset', choices=sorted(PRESETS))
    ap.add_argument('--title')
    ap.add_argument('--subtitle', default='')
    ap.add_argument('--out')
    ap.add_argument('--keep-html', action='store_true', help='중간 HTML 도 남긴다')
    ap.add_argument('docs', nargs='*', help='vault/ 기준 마크다운 경로')
    a = ap.parse_args()

    if a.preset:
        p = PRESETS[a.preset]
        title, subtitle, docs = p['title'], p['subtitle'], p['docs']
        out = (pathlib.Path(a.out).resolve() if a.out
               else ROOT / 'vault' / 'pdf' / f'커피-{a.preset}.pdf')
    else:
        if not a.docs or not a.title:
            ap.error('--preset 을 쓰거나, --title 과 문서 경로를 직접 주세요.')
        title, subtitle = a.title, a.subtitle
        docs = [(d, pathlib.Path(d).stem, '') for d in a.docs]
        out = (pathlib.Path(a.out).resolve() if a.out
               else ROOT / 'vault' / 'pdf' / f'{title}.pdf')

    ensure_font()

    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix('.html')
    html_path.write_text(build_html(title, subtitle, docs, VAULT), encoding='utf-8')
    print(f'📄 HTML 생성: {html_path.relative_to(ROOT)} '
          f'({html_path.stat().st_size:,} bytes)')

    r = subprocess.run(['node', str(PRINTER), str(html_path), str(out), title],
                       cwd=ROOT)
    if r.returncode != 0:
        print('❌ PDF 변환 실패')
        return r.returncode
    if not a.keep_html:
        html_path.unlink()

    print(f'✅ PDF: {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
