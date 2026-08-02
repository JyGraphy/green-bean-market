#!/usr/bin/env python3
"""AGENT HQ 현황판을 단일 HTML 파일로 빌드한다.

hq/agents.html + agents.css + agents.js 를 하나로 합치고,
docs/·research/ 의 보고서 마크다운을 window.__REPORTS__ 로 주입해
현황판에서 바로 읽을 수 있게 만든다.

사용법:
    python3 hq/build-artifact.py [출력경로]

출력물은 자체 완결형이라 Artifact로 게시하면 그대로 동작한다.
게시할 때는 반드시 기존 아티팩트 URL을 넘겨 같은 주소를 갱신할 것.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HQ = ROOT / 'hq'
LIVE_SITE = 'https://green-bean-market.vercel.app/'

# 보고서 목록: (파일경로, 담당 에이전트, 부서, 한 줄 설명)
# 새 보고서가 생기면 여기에 추가한다.
REPORT_SOURCES = [
    ('docs/coe-report-*.md', 'coe-auction-reporter', 'res',
     'COE 각국 옥션 일정과 결과 — 낙찰가·농장·품종·한국 업체 낙찰 내역'),
    ('docs/store-scout-report-*.md', 'store-scout', 'ops',
     '미등록 생두 쇼핑몰 후보 조사 — 플랫폼·난이도·추천도 (승인 대기)'),
    ('docs/daily/*-스크래퍼점검.md', 'scraper-checker', 'qa',
     '스크래퍼 안전장치 규칙 준수 전수 점검'),
    ('docs/daily/*-데이터검증.md', 'data-validator', 'qa',
     '상품 데이터 스키마·중복 ID·URL·가격 이상치 검증'),
    ('docs/daily/*-프론트리뷰.md', 'frontend-reviewer', 'qa',
     '화면 변경 리뷰 — 배지·필터·정렬·반응형'),
    ('docs/daily/*-결산.md', 'system', 'qa',
     '일일 퇴근 결산 — 부서별 업무와 컨펌 대기 항목'),
    ('docs/research/*.md', 'coffee-research-translator', 'res',
     '커피 과학 논문 한글 정리'),
    ('research/roast-profiles/SOURCES.md', 'roast-profile-collector', 'res',
     '로스팅 프로파일 데이터 출처 카탈로그 — 수집 후보와 라이선스'),
]

DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')


def collect_reports():
    reports = []
    seen = set()
    for pattern, agent, dept, desc in REPORT_SOURCES:
        for path in sorted(ROOT.glob(pattern), reverse=True):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            body = path.read_text(encoding='utf-8')
            # 제목: 첫 번째 '# ' 헤딩, 없으면 파일명
            m = re.search(r'^#\s+(.+)$', body, re.M)
            title = m.group(1).strip() if m else path.stem
            d = DATE_RE.search(path.name) or DATE_RE.search(body)
            reports.append({
                'title': title,
                'agent': agent,
                'dept': dept,
                'date': d.group(1) if d else '',
                'desc': desc,
                'path': str(path.relative_to(ROOT)),
                'words': len(body),
                'body': body,
            })
    reports.sort(key=lambda r: (r['date'], r['title']), reverse=True)
    return reports


def build(out_path):
    html = (HQ / 'agents.html').read_text(encoding='utf-8')
    css = (HQ / 'agents.css').read_text(encoding='utf-8')
    js = (HQ / 'agents.js').read_text(encoding='utf-8')

    # <body>~</body> 사이만 추출하고 <script src> 참조는 제거
    body = html.split('<body>', 1)[1].split('</body>', 1)[0]
    body = body.replace('<script src="agents.js"></script>', '')
    # 아티팩트에서는 상대경로 링크가 동작하지 않으므로 라이브 사이트로 교체
    body = body.replace('href="../index.html"', f'href="{LIVE_SITE}" target="_blank" rel="noopener"')

    reports = collect_reports()
    payload = json.dumps(reports, ensure_ascii=False)
    # </script> 가 문자열 안에 있으면 조기 종료되므로 이스케이프
    payload = payload.replace('</', '<\\/')

    out = (
        '<title>AGENT HQ — AI 직원 현황판</title>\n'
        f'<style>\n{css}\n</style>\n'
        f'{body}\n'
        f'<script>window.__REPORTS__ = {payload};</script>\n'
        f'<script>\n{js}\n</script>\n'
    )
    out_path.write_text(out, encoding='utf-8')
    print(f'✓ {out_path}  ({len(out)/1024:.0f} KB, 보고서 {len(reports)}건)')
    for r in reports:
        print(f'   · [{r["date"]}] {r["agent"]:<26} {r["title"][:44]}')


if __name__ == '__main__':
    target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HQ / 'agent-hq.build.html'
    build(target)
